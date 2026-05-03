import { useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import RcaForm from '../components/RcaForm'
import SignalList from '../components/SignalList'
import StateControls from '../components/StateControls'
import { fetchIncident, submitRca, updateIncidentState, type IncidentState } from '../services/api'
import { useIncidentDetail } from '../hooks/useIncidentDetail'

export default function IncidentDetailPage() {
  const params = useParams()
  const id = params.id ? Number(params.id) : null
  const { incident, loading, error, setIncident } = useIncidentDetail(id)
  const [message, setMessage] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const showRcaForm = incident?.state === 'RESOLVED' || incident?.state === 'INVESTIGATING'

  const refresh = async () => {
    if (id === null) return
    const latest = await fetchIncident(id)
    setIncident(latest)
  }

  const transition = async (state: IncidentState) => {
    if (id === null) return
    if (state === 'CLOSED' && !incident?.rca) {
      setMessage('RCA is required before closing an incident.')
      return
    }

    try {
      setBusy(true)
      setMessage(null)
      const updated = await updateIncidentState(id, state)
      setIncident((current) => current ? { ...current, ...updated } : current)
      await refresh()
      setMessage(`Incident moved to ${state}.`)
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'State update failed')
    } finally {
      setBusy(false)
    }
  }

  const submitRcaHandler = async (payload: Parameters<typeof submitRca>[1]) => {
    if (id === null) return
    try {
      setBusy(true)
      setMessage(null)
      const updated = await submitRca(id, payload)
      setIncident(updated)
      setMessage('RCA saved and incident closed.')
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'RCA submission failed')
    } finally {
      setBusy(false)
    }
  }

  const statusLine = useMemo(() => {
    if (!incident) return null
    return `${incident.component_id} is currently ${incident.state}`
  }, [incident])

  if (loading) {
    return <div className="card">Loading incident...</div>
  }

  if (error) {
    return <div className="card stack"><div className="alert error">{error}</div><Link className="link-chip" to="/">Back to dashboard</Link></div>
  }

  if (!incident) {
    return <div className="card stack"><p>Incident not found.</p><Link className="link-chip" to="/">Back to dashboard</Link></div>
  }

  return (
    <section className="page-grid">
      <div className="card card-header">
        <div>
          <p className="eyebrow">Incident Detail</p>
          <h2>{statusLine}</h2>
          <p className="muted">Signals are loaded from MongoDB through the incident detail API.</p>
        </div>
        <Link className="link-chip" to="/">Back to dashboard</Link>
      </div>

      {message ? <div className="alert success">{message}</div> : null}

      <div className="detail-layout">
        <div className="stack">
          <div className="card stack">
            <div className="meta-grid">
              <div className="meta-item"><span className="meta-label">Incident ID</span><strong>{incident.id}</strong></div>
              <div className="meta-item"><span className="meta-label">Component</span><strong>{incident.component_id}</strong></div>
              <div className="meta-item"><span className="meta-label">Severity</span><strong>{incident.severity}</strong></div>
              <div className="meta-item"><span className="meta-label">State</span><strong>{incident.state}</strong></div>
              <div className="meta-item"><span className="meta-label">Start Time</span><strong>{new Date(incident.start_time).toLocaleString()}</strong></div>
              <div className="meta-item"><span className="meta-label">End Time / MTTR</span><strong>{incident.end_time ? new Date(incident.end_time).toLocaleString() : 'Open'}{incident.mttr_seconds ? ` · ${Math.round(incident.mttr_seconds)}s` : ''}</strong></div>
            </div>
          </div>

          <div className="card stack">
            <h3>Signals</h3>
            <SignalList signals={incident.signals} />
          </div>
        </div>

        <div className="stack">
          <div className="card stack">
            <h3>State Controls</h3>
            <StateControls currentState={incident.state} busy={busy} onTransition={transition} />
          </div>
          <RcaForm visible={showRcaForm} busy={busy} onSubmit={submitRcaHandler} />
          {incident.rca ? (
            <div className="card stack">
              <h3>Stored RCA</h3>
              <p><strong>Root Cause:</strong> {incident.rca.root_cause}</p>
              <p><strong>Fix:</strong> {incident.rca.fix}</p>
              <p><strong>Prevention:</strong> {incident.rca.prevention}</p>
            </div>
          ) : null}
        </div>
      </div>
    </section>
  )
}
