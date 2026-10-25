import { useState, useEffect } from 'react'
import { LineChart, Line, ScatterChart, Scatter, ResponsiveContainer, XAxis, YAxis, Tooltip } from 'recharts'

const HEARTBEAT_TIMEOUT_S = 15

function calcStatus(lastSeen) {
  if (!lastSeen) return 'OFFLINE'
  const last = new Date(lastSeen + 'Z')
  return (Date.now() - last.getTime()) / 1000 <= HEARTBEAT_TIMEOUT_S ? 'ONLINE' : 'OFFLINE'
}

function append(seriesMap, observerName, node, point, window) {
  const obs = seriesMap[observerName] || {}
  const pts = [...(obs[node] || []), point]
  return {
    ...seriesMap,
    [observerName]: {
      ...obs,
      [node]: pts.length > window ? pts.slice(pts.length - window) : pts
    }
  }
}

/**
 * Renderer generico per un singolo observer.
 * Riceve la dashboard_config dall'observer e la usa per costruire le chart.
 * Non sa nulla di quali nodi esistono — lo decide l'observer.
 */
function ObserverWidget({ name, lastSeen, config, data }) {
  const online = calcStatus(lastSeen) === 'ONLINE'
  const charts = config.charts || []

  return (
    <div style={{
      background: '#0d0d0d',
      border: '1px solid #2a2a2a',
      borderRadius: '8px',
      padding: '12px 16px',
      marginBottom: '16px',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
        <span style={{ fontFamily: 'monospace', fontSize: '0.85rem', fontWeight: 'bold', color: '#ccc' }}>{name}</span>
        <span style={{
          fontSize: '0.65rem', padding: '1px 6px', borderRadius: '4px', fontFamily: 'monospace',
          background: online ? '#14532d' : '#3f1515',
          color: online ? '#4ade80' : '#f87171',
        }}>
          {online ? 'ONLINE' : 'OFFLINE'}
        </span>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))',
        gap: '10px',
      }}>
        {charts.map(chart => {
          if (chart.type === 'scatter') {
            const xSeries = data[chart.x_node.name] || []
            const ySeries = data[chart.y_node.name] || []
            const len = Math.min(xSeries.length, ySeries.length)
            const scatterPoints = Array.from({ length: len }, (_, i) => ({
              x: xSeries[xSeries.length - len + i].value,
              y: ySeries[ySeries.length - len + i].value,
            }))
            const color = chart.y_node.color

            return (
              <div key={chart.id} style={{
                background: '#0a0a0a',
                border: '1px solid #1e1e1e',
                borderRadius: '6px',
                padding: '10px 12px',
                gridColumn: '1 / -1',
              }}>
                <div style={{ marginBottom: '6px' }}>
                  <span style={{ color: '#555', fontSize: '0.72rem', fontFamily: 'monospace' }}>{chart.title}</span>
                </div>
                <ResponsiveContainer width="100%" height={200}>
                  <ScatterChart margin={{ top: 4, right: 8, bottom: 20, left: 8 }}>
                    <XAxis
                      dataKey="x"
                      type="number"
                      domain={['auto', 'auto']}
                      label={{ value: chart.x_node.label, position: 'insideBottom', offset: -10, fill: '#555', fontSize: '0.65rem', fontFamily: 'monospace' }}
                      tick={{ fill: '#444', fontSize: '0.65rem', fontFamily: 'monospace' }}
                    />
                    <YAxis
                      dataKey="y"
                      type="number"
                      domain={['auto', 'auto']}
                      label={{ value: chart.y_node.label, angle: -90, position: 'insideLeft', offset: 12, fill: '#555', fontSize: '0.65rem', fontFamily: 'monospace' }}
                      tick={{ fill: '#444', fontSize: '0.65rem', fontFamily: 'monospace' }}
                      width={45}
                    />
                    <Tooltip
                      contentStyle={{
                        background: '#1a1a1a',
                        border: `1px solid ${color}44`,
                        fontSize: '0.7rem',
                        fontFamily: 'monospace'
                      }}
                      formatter={(v, name) => [Number(v).toFixed(2), name === 'x' ? chart.x_node.label : chart.y_node.label]}
                      cursor={{ strokeDasharray: '3 3', stroke: '#333' }}
                    />
                    <Scatter
                      data={scatterPoints}
                      fill={color}
                      opacity={0.7}
                      isAnimationActive={false}
                    />
                  </ScatterChart>
                </ResponsiveContainer>
                {scatterPoints.length === 0 && (
                  <div style={{ color: '#2a2a2a', fontSize: '0.7rem', textAlign: 'center', fontFamily: 'monospace' }}>
                    nessun dato
                  </div>
                )}
              </div>
            )
          }

          // Combina i dati di tutti i nodi del chart (multi-line support)
          // Usa il primo nodo come asse temporale base
          const primaryNode = chart.nodes[0]
          const points = data[primaryNode.name] || []
          const currentVal = points.length > 0 ? points[points.length - 1].value : null
          const primaryColor = primaryNode.color

          return (
            <div key={chart.id} style={{
              background: '#0a0a0a',
              border: '1px solid #1e1e1e',
              borderRadius: '6px',
              padding: '10px 12px',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '6px' }}>
                <span style={{ color: '#555', fontSize: '0.72rem', fontFamily: 'monospace' }}>{chart.title}</span>
                <span style={{ color: primaryColor, fontSize: '0.9rem', fontWeight: 'bold', fontFamily: 'monospace' }}>
                  {currentVal !== null ? Number(currentVal).toFixed(2) : '—'}
                </span>
              </div>

              <ResponsiveContainer width="100%" height={70}>
                <LineChart data={points}>
                  <YAxis domain={['auto', 'auto']} hide />
                  <Tooltip
                    contentStyle={{
                      background: '#1a1a1a',
                      border: `1px solid ${primaryColor}44`,
                      fontSize: '0.7rem',
                      fontFamily: 'monospace'
                    }}
                    formatter={v => [Number(v).toFixed(2), chart.title]}
                    labelFormatter={() => ''}
                  />
                  {chart.nodes.map(n => (
                    <Line
                      key={n.name}
                      type="monotone"
                      dataKey="value"
                      data={data[n.name] || []}
                      stroke={n.color}
                      dot={false}
                      strokeWidth={1.5}
                      isAnimationActive={false}
                      name={n.label}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>

              {points.length === 0 && (
                <div style={{ color: '#2a2a2a', fontSize: '0.7rem', textAlign: 'center', marginTop: '-16px', fontFamily: 'monospace' }}>
                  nessun dato
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}


export default function Dashboard() {
  const [observers, setObservers] = useState({})   // { name: { last_seen, dashboard_config } }
  const [series, setSeries] = useState({})          // { observer_name: { node_name: [{ts, value}] } }

  // Carica observers e dati storici all'avvio
  useEffect(() => {
    fetch('/observers')
      .then(r => r.json())
      .then(obs => {
        setObservers(obs)
        // Carica dati storici per ogni observer
        Object.entries(obs).forEach(([name, info]) => {
          const window = info.dashboard_config?.window || 200
          fetch(`/data/recent?observer=${name}&limit=${window}`)
            .then(r => r.json())
            .then(data => {
              setSeries(prev => ({ ...prev, [name]: data }))
            })
            .catch(() => {})
        })
      })
      .catch(() => {})
  }, [])

  // Aggiornamenti live
  useEffect(() => {
    const ws = new WebSocket(`ws://${window.location.host}/ws/ui`)
    ws.onmessage = (evt) => {
      const data = JSON.parse(evt.data)

      if (data.type === 'data_event') {
        const obsName = data.observer
        const config = observers[obsName]?.dashboard_config
        const win = config?.window || 200
        setSeries(prev => append(prev, obsName, data.node, { ts: data.timestamp, value: data.value }, win))
      }
    }
    return () => ws.close()
  }, [observers])

  const observerList = Object.entries(observers)

  if (observerList.length === 0) {
    return (
      <div style={{ fontFamily: 'monospace', padding: '16px 24px', color: '#444', fontSize: '0.8rem' }}>
        Nessun observer connesso.
      </div>
    )
  }

  return (
    <div style={{ fontFamily: 'monospace', padding: '16px 24px' }}>
      <h2 style={{ marginBottom: '16px', fontSize: '1rem' }}>Dashboard</h2>
      {observerList.map(([name, info]) => (
        <ObserverWidget
          key={name}
          name={name}
          lastSeen={info.last_seen}
          config={info.dashboard_config || {}}
          data={series[name] || {}}
        />
      ))}
    </div>
  )
}
