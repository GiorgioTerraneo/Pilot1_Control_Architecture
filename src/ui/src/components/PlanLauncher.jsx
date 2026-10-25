import { useState, useEffect, useRef } from 'react'

const HEARTBEAT_TIMEOUT_S = 15

function calcStatus(lastSeen) {
  if (!lastSeen) return 'OFFLINE'
  const last = new Date(lastSeen + 'Z')
  return (Date.now() - last.getTime()) / 1000 <= HEARTBEAT_TIMEOUT_S ? 'ONLINE' : 'OFFLINE'
}

/**
 * Estrae i nomi delle risorse menzionate in un masterplan (parsing client-side).
 * Formato riga: "ResourceName | SERVICE | args" oppure commento "#..."
 */
function extractResources(planContent) {
  const names = new Set()
  for (const line of planContent.split('\n')) {
    const trimmed = line.trim()
    if (!trimmed || trimmed.startsWith('#')) continue
    const parts = trimmed.split('|')
    if (parts.length >= 2) names.add(parts[0].trim())
  }
  return names
}

export default function PlanLauncher() {
  const [plans, setPlans] = useState([])
  const [selectedPlan, setSelectedPlan] = useState('')
  const [resources, setResources] = useState({})
  const [offlineResources, setOfflineResources] = useState([])
  const [isRunning, setIsRunning] = useState(false)
  const wsRef = useRef(null)

  // Connessione WebSocket per ricevere eventi di avanzamento
  useEffect(() => {
    const ws = new WebSocket(`ws://${window.location.host}/ws/ui`)
    wsRef.current = ws
    ws.onmessage = (evt) => {
      const data = JSON.parse(evt.data)
      if (data.type !== 'progress_event') return
      if (data.status === 'started') setIsRunning(true)
      if (['finished', 'aborted'].includes(data.status)) setIsRunning(false)
    }
    return () => ws.close()
  }, [])

  // Carica lista piani e risorse all'avvio
  useEffect(() => {
    fetch('/plans').then(r => r.json()).then(d => {
      setPlans(d.plans || [])
      if (d.plans?.length > 0) setSelectedPlan(d.plans[0])
    })
    fetch('/resources').then(r => r.json()).then(setResources)
  }, [])

  // Guardia pre-lancio: quando cambia il piano selezionato, verifica risorse richieste
  useEffect(() => {
    if (!selectedPlan) return
    fetch(`/plans/${selectedPlan}`)
      .then(r => r.json())
      .then(d => {
        const required = extractResources(d.content || '')
        const offline = [...required].filter(name => {
          const info = resources[name]
          return !info || calcStatus(info.last_seen) === 'OFFLINE'
        })
        setOfflineResources(offline)
      })
  }, [selectedPlan, resources])

  function sendWs(payload) {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(payload))
    }
  }

  function handleLaunch() {
    if (selectedPlan && !isRunning && offlineResources.length === 0) {
      sendWs({ action: 'launch_plan', plan: selectedPlan })
    }
  }

  function handleAbort() {
    sendWs({ action: 'abort_plan' })
  }

  const canLaunch = selectedPlan && !isRunning && offlineResources.length === 0

  return (
    <div style={{ fontFamily: 'monospace', padding: '24px', borderBottom: '1px solid #333' }}>
      <h2 style={{ marginBottom: '16px' }}>Lancio Piano</h2>

      <div style={{ display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
        <select
          value={selectedPlan}
          onChange={e => setSelectedPlan(e.target.value)}
          disabled={isRunning}
          style={{
            background: '#1a1a1a', color: '#eee', border: '1px solid #444',
            padding: '6px 12px', borderRadius: '6px', fontFamily: 'monospace', fontSize: '0.9rem',
            cursor: isRunning ? 'not-allowed' : 'pointer',
          }}
        >
          {plans.map(p => <option key={p} value={p}>{p}</option>)}
        </select>

        <button
          onClick={handleLaunch}
          disabled={!canLaunch}
          style={{
            padding: '6px 20px', borderRadius: '6px', fontFamily: 'monospace',
            fontWeight: 'bold', fontSize: '0.9rem', cursor: canLaunch ? 'pointer' : 'not-allowed',
            background: canLaunch ? '#22c55e' : '#333', color: canLaunch ? '#000' : '#666',
            border: 'none',
          }}
        >
          ▷ Lancia
        </button>

        {isRunning && (
          <button
            onClick={handleAbort}
            style={{
              padding: '6px 20px', borderRadius: '6px', fontFamily: 'monospace',
              fontWeight: 'bold', fontSize: '0.9rem', cursor: 'pointer',
              background: '#ef4444', color: 'white', border: 'none',
            }}
          >
            ■ Abort
          </button>
        )}
      </div>

      {offlineResources.length > 0 && !isRunning && (
        <p style={{ color: '#ef4444', fontSize: '0.8rem', marginTop: '8px' }}>
          ✕ Risorse OFFLINE richieste da questo piano: {offlineResources.join(', ')}
        </p>
      )}
    </div>
  )
}
