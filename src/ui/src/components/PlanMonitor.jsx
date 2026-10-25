import { useState, useEffect, useRef } from 'react'

const STATUS_ICON = {
  pending: '—',
  running: '⋯',
  done:    '✓',
  error:   '✕',
}

const STATUS_COLOR = {
  pending: '#555',
  running: '#facc15',
  done:    '#22c55e',
  error:   '#ef4444',
}

export default function PlanMonitor() {
  const [plan, setPlan] = useState(null)   // { name, total }
  const [steps, setSteps] = useState([])  // [{ step, target, service, status, message }]
  const [finalStatus, setFinalStatus] = useState(null)  // "finished" | "aborted" | null
  const wsRef = useRef(null)

  useEffect(() => {
    const ws = new WebSocket(`ws://${window.location.host}/ws/ui`)
    wsRef.current = ws

    ws.onmessage = (evt) => {
      const data = JSON.parse(evt.data)
      if (data.type !== 'progress_event') return

      const { status, step, total, target, service, message, plan: planName } = data

      if (status === 'started') {
        // Nuovo piano avviato: reset completo
        setPlan({ name: planName, total })
        setSteps(Array.from({ length: total }, (_, i) => ({
          step: i + 1, target: null, service: null, status: 'pending', message: null,
        })))
        setFinalStatus(null)
        return
      }

      if (status === 'finished' || status === 'aborted') {
        setFinalStatus(status)
        return
      }

      // Aggiorna lo step specifico
      setSteps(prev => prev.map(s =>
        s.step === step
          ? { ...s, target, service, status, message: message ?? s.message }
          : s
      ))
    }

    return () => ws.close()
  }, [])

  if (!plan) {
    return (
      <div style={{ fontFamily: 'monospace', padding: '24px', color: '#888' }}>
        <h2 style={{ marginBottom: '8px' }}>Monitor Piano</h2>
        <p>In attesa dell'avvio di un masterplan...</p>
      </div>
    )
  }

  return (
    <div style={{ fontFamily: 'monospace', padding: '24px', maxWidth: '800px' }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: '12px', marginBottom: '16px' }}>
        <h2 style={{ margin: 0 }}>Monitor Piano</h2>
        <span style={{ color: '#aaa', fontSize: '0.85rem' }}>{plan.name}</span>
        {finalStatus && (
          <span style={{
            padding: '2px 10px', borderRadius: '12px', fontSize: '0.75rem', fontWeight: 'bold',
            background: finalStatus === 'finished' ? '#22c55e' : '#ef4444', color: 'white',
          }}>
            {finalStatus === 'finished' ? 'COMPLETATO' : 'INTERROTTO'}
          </span>
        )}
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
        {steps.map(s => (
          <div key={s.step} style={{
            display: 'flex', alignItems: 'center', gap: '12px',
            padding: '8px 12px', borderRadius: '6px',
            background: s.status === 'running' ? '#1e2a1e' : '#1a1a1a',
            border: `1px solid ${s.status === 'running' ? '#22c55e44' : '#2a2a2a'}`,
          }}>
            <span style={{ color: STATUS_COLOR[s.status], width: '16px', textAlign: 'center' }}>
              {STATUS_ICON[s.status]}
            </span>
            <span style={{ color: '#888', minWidth: '60px' }}>Step {s.step}/{plan.total}</span>
            {s.target && (
              <span style={{ color: '#aaa' }}>
                <span style={{ color: '#eee' }}>{s.target}</span>
                {s.service && <span style={{ color: '#666' }}> › {s.service}</span>}
              </span>
            )}
            {s.message && s.status === 'error' && (
              <span style={{ color: '#ef4444', fontSize: '0.8rem', marginLeft: 'auto' }}>
                {s.message}
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
