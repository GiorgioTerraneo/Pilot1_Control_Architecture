import { useState, useEffect } from 'react'

const HEARTBEAT_TIMEOUT_S = 15

function calcStatus(lastSeen) {
  if (!lastSeen) return 'OFFLINE'
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

export default function SupervisorPanel() {
  const [supervisors, setSupervisors] = useState({})

  async function fetchStatus() {
    try {
      const res = await fetch('/status')
      const data = await res.json()
      setSupervisors(data)
    } catch (e) {
      console.error('Errore fetch status supervisori:', e)
    }
  }

  useEffect(() => {
    fetchStatus()
    const interval = setInterval(fetchStatus, HEARTBEAT_TIMEOUT_S * 1000)
    return () => clearInterval(interval)
  }, [])

  const entries = Object.entries(supervisors)

  return (
    <div style={{
      fontFamily: 'monospace',
      padding: '16px 24px',
      borderBottom: '1px solid #333',
      background: '#161b22',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
        <span style={{ color: '#888', fontSize: '0.8rem' }}>Supervisori:</span>
        {entries.length === 0 ? (
          <span style={{ color: '#ef4444', fontSize: '0.8rem' }}>Nessun supervisore connesso</span>
        ) : (
          entries.map(([name, info]) => {
            const status = calcStatus(info.last_seen)
            return (
              <div key={name} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 'bold' }}>{name}</span>
                <StatusBadge status={status} />
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}
