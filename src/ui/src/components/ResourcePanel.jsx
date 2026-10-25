import { useState, useEffect } from 'react'

const HEARTBEAT_TIMEOUT_S = 15

/**
 * Calcola lo stato di un agente confrontando last_seen con l'ora corrente.
 * Restituisce "ONLINE" se l'ultimo heartbeat è più recente di HEARTBEAT_TIMEOUT_S secondi.
 */
function calcStatus(lastSeen) {
  if (!lastSeen) return 'OFFLINE'
  // SQLite restituisce timestamp UTC senza 'Z' — lo aggiungiamo per parsing corretto
  const last = new Date(lastSeen + 'Z')
  const diffS = (Date.now() - last.getTime()) / 1000
  return diffS <= HEARTBEAT_TIMEOUT_S ? 'ONLINE' : 'OFFLINE'
}

function StatusBadge({ status }) {
  const online = status === 'ONLINE'
  return (
    <span style={{
      padding: '2px 10px',
      borderRadius: '12px',
      fontSize: '0.75rem',
      fontWeight: 'bold',
      background: online ? '#22c55e' : '#ef4444',
      color: 'white',
    }}>
      {status}
    </span>
  )
}

export default function ResourcePanel() {
  const [resources, setResources] = useState({})
  const [lastRefresh, setLastRefresh] = useState(null)

  async function fetchResources() {
    try {
      const res = await fetch('/resources')
      const data = await res.json()
      setResources(data)
      setLastRefresh(new Date())
    } catch (e) {
      console.error('Errore fetch risorse:', e)
    }
  }

  useEffect(() => {
    fetchResources()
    // Aggiorna ogni HEARTBEAT_TIMEOUT_S secondi per ricalcolare lo stato
    const interval = setInterval(fetchResources, HEARTBEAT_TIMEOUT_S * 1000)
    return () => clearInterval(interval)
  }, [])

  const entries = Object.entries(resources)

  return (
    <div style={{ fontFamily: 'monospace', padding: '24px', maxWidth: '800px', margin: '0 auto' }}>
      <h2 style={{ marginBottom: '4px' }}>◇ Risorse connesse</h2>
      <p style={{ color: '#888', fontSize: '0.8rem', marginBottom: '20px' }}>
        Aggiornamento ogni {HEARTBEAT_TIMEOUT_S}s
        {lastRefresh && ` — ultimo: ${lastRefresh.toLocaleTimeString()}`}
      </p>

      {entries.length === 0 ? (
        <p style={{ color: '#888' }}>Nessuna risorsa registrata.</p>
      ) : (
        entries.map(([name, info]) => {
          const status = calcStatus(info.last_seen)
          const services = info.services || {}
          return (
            <div key={name} style={{
              border: '1px solid #333',
              borderRadius: '8px',
              padding: '16px',
              marginBottom: '12px',
              background: '#1a1a1a',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
                <strong style={{ fontSize: '1rem' }}>{name}</strong>
                <StatusBadge status={status} />
              </div>
              <div style={{ color: '#aaa', fontSize: '0.8rem', marginBottom: '8px' }}>
                Ultimo heartbeat: {info.last_seen ?? 'N/A'}
              </div>
              <div style={{ fontSize: '0.8rem' }}>
                <span style={{ color: '#888' }}>Servizi: </span>
                {Object.keys(services).map(s => (
                  <span key={s} style={{
                    display: 'inline-block',
                    margin: '2px 4px',
                    padding: '1px 8px',
                    background: '#2a2a2a',
                    border: '1px solid #444',
                    borderRadius: '4px',
                  }}>{s}</span>
                ))}
              </div>
            </div>
          )
        })
      )}
    </div>
  )
}
