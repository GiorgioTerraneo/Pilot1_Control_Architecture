import ResourcePanel from './components/ResourcePanel'
import SupervisorPanel from './components/SupervisorPanel'
import PlanMonitor from './components/PlanMonitor'
import PlanLauncher from './components/PlanLauncher'
import LogPanel from './components/LogPanel'
import Dashboard from './components/Dashboard'

export default function App() {
  return (
    <div style={{ minHeight: '100vh', background: '#111', color: '#eee' }}>
      <header style={{
        padding: '16px 24px',
        borderBottom: '1px solid #333',
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
      }}>
        <span style={{ fontSize: '1.2rem', fontWeight: 'bold', fontFamily: 'monospace' }}>
          System Executor
        </span>
        <span style={{ color: '#888', fontSize: '0.8rem', fontFamily: 'monospace' }}>
          CIRC4ME Lab
        </span>
      </header>

      <SupervisorPanel />

      <main style={{ display: 'flex', gap: '0', flexWrap: 'wrap' }}>
        <div style={{ flex: '1', minWidth: '320px', borderRight: '1px solid #333' }}>
          <ResourcePanel />
        </div>
        <div style={{ flex: '2', minWidth: '400px' }}>
          <PlanLauncher />
          <PlanMonitor />
          <LogPanel />
        </div>
      </main>

      <section style={{ borderTop: '1px solid #333' }}>
        <Dashboard />
      </section>
    </div>
  )
}
