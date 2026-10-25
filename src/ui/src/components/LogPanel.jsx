import { useState, useEffect, useRef } from 'react'

const MAX_LOGS = 200

const LEVEL_COLORS = {
  ERROR:   '#ef4444',
  WARNING: '#f59e0b',
  INFO:    '#a3a3a3',
  DEBUG:   '#6b7280',
}

const SOURCE_COLORS = {
  SUPERVISOR: '#818cf8',
  APIServer:  '#34d399',
}

const ALL_LEVELS = ['ERROR', 'WARNING', 'INFO']

function sourceColor(name) {
  if (SOURCE_COLORS[name]) return SOURCE_COLORS[name]
  return '#67e8f9'
}

function FilterBtn({ label, active, color, onClick }) {
  return (
    <button
      onClick={onClick}
      style={{
        background: active ? color + '22' : 'none',
        border: `1px solid ${active ? color : '#444'}`,
        color: active ? color : '#555',
        borderRadius: '4px', padding: '1px 8px', cursor: 'pointer',
        fontFamily: 'monospace', fontSize: '0.72rem',
      }}
    >
      {label}
    </button>
  )
}

export default function LogPanel() {
  const [logs, setLogs] = useState([])
  const [activeLevels, setActiveLevels] = useState(new Set(ALL_LEVELS))
  const [activeSources, setActiveSources] = useState(new Set())   // vuoto = tutti attivi
  const [knownSources, setKnownSources] = useState([])
  const bottomRef = useRef(null)

  useEffect(() => {
    const ws = new WebSocket(`ws://${window.location.host}/ws/ui`)
    ws.onmessage = (evt) => {
      const data = JSON.parse(evt.data)
      if (data.type !== 'log_event') return
      const entry = {
        id: Date.now() + Math.random(),
        ts: new Date().toLocaleTimeString('it-IT', { hour12: false }),
        source: data.source || '?',
        level: data.level || 'INFO',
        message: data.message || '',
      }
      setLogs(prev => {
        const next = [...prev, entry]
        return next.length > MAX_LOGS ? next.slice(next.length - MAX_LOGS) : next
      })
      // Registra la sorgente se nuova
      setKnownSources(prev =>
        prev.includes(entry.source) ? prev : [...prev, entry.source]
      )
    }
    return () => ws.close()
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs])

  function toggleLevel(level) {
    setActiveLevels(prev => {
      const next = new Set(prev)
      next.has(level) ? next.delete(level) : next.add(level)
      return next
    })
  }

  function toggleSource(source) {
    setActiveSources(prev => {
      const next = new Set(prev)
      next.has(source) ? next.delete(source) : next.add(source)
      return next
    })
  }

  // activeSources vuoto = nessun filtro sorgente attivo (mostra tutto)
  const visible = logs.filter(l =>
    activeLevels.has(l.level) &&
    (activeSources.size === 0 || activeSources.has(l.source))
  )

  return (
    <div style={{ fontFamily: 'monospace', padding: '16px 24px', borderTop: '1px solid #333' }}>

      {/* Riga 1: titolo + filtri livello + clear */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px', flexWrap: 'wrap', gap: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <h2 style={{ margin: 0, fontSize: '1rem' }}>Log</h2>
          {ALL_LEVELS.map(level => (
            <FilterBtn
              key={level}
              label={level}
              active={activeLevels.has(level)}
              color={LEVEL_COLORS[level]}
              onClick={() => toggleLevel(level)}
            />
          ))}
        </div>
        <button
          onClick={() => setLogs([])}
          style={{
            background: 'none', border: '1px solid #444', color: '#888',
            borderRadius: '4px', padding: '2px 10px', cursor: 'pointer',
            fontFamily: 'monospace', fontSize: '0.75rem',
          }}
        >
          clear
        </button>
      </div>

      {/* Riga 2: filtri sorgente (appaiono dinamicamente) */}
      {knownSources.length > 0 && (
        <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginBottom: '8px' }}>
          {knownSources.map(src => (
            <FilterBtn
              key={src}
              label={src}
              active={activeSources.has(src)}
              color={sourceColor(src)}
              onClick={() => toggleSource(src)}
            />
          ))}
        </div>
      )}

      {/* Area log */}
      <div style={{
        height: '200px',
        overflowY: 'auto',
        background: '#0a0a0a',
        border: '1px solid #222',
        borderRadius: '6px',
        padding: '8px',
        textAlign: 'left',
      }}>
        {visible.length === 0 && (
          <span style={{ color: '#444', fontSize: '0.8rem' }}>In attesa di log...</span>
        )}
        {visible.map(log => (
          <div key={log.id} style={{ fontSize: '0.78rem', lineHeight: '1.5', whiteSpace: 'pre-wrap', wordBreak: 'break-all', textAlign: 'left' }}>
            <span style={{ color: '#555' }}>{log.ts} </span>
            <span style={{ color: sourceColor(log.source), fontWeight: 'bold' }}>[{log.source}] </span>
            <span style={{ color: LEVEL_COLORS[log.level] || '#a3a3a3' }}>{log.message}</span>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
