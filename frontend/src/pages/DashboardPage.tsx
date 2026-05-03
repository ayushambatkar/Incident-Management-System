import IncidentTable from '../components/IncidentTable'
import SeedPanel from '../components/SeedPanel'
import { useIncidents } from '../hooks/useIncidents'

export default function DashboardPage() {
  const { incidents, loading, error } = useIncidents(5000)

  return (
    <section className="page-grid">
      <SeedPanel />

      <div className="card card-header">
        <div>
          <h2>Active Incidents</h2>
          <p className="muted">Live view refreshed every 5 seconds from the Redis-backed cache.</p>
        </div>
        <div className="status-badge">{incidents.length} active</div>
      </div>

      {error ? <div className="alert error">{error}</div> : null}
      {loading ? <div className="card">Loading incidents...</div> : <div className="card"><IncidentTable incidents={incidents} /></div>}
    </section>
  )
}
