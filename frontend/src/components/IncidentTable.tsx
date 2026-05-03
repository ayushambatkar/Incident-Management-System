import { Link } from 'react-router-dom'
import type { IncidentSummary } from '../services/api'

interface Props {
  incidents: IncidentSummary[]
}

const severityRank: Record<IncidentSummary['severity'], number> = {
  P0: 0,
  P1: 1,
  P2: 2,
  P3: 3,
}

export default function IncidentTable({ incidents }: Props) {
  const sorted = [...incidents].sort((left, right) => {
    const severityDiff = severityRank[left.severity] - severityRank[right.severity]
    if (severityDiff !== 0) return severityDiff
    return new Date(right.start_time).getTime() - new Date(left.start_time).getTime()
  })

  return (
    <div className="table-wrap">
      <table className="table">
        <thead>
          <tr>
            <th>Component</th>
            <th>Severity</th>
            <th>State</th>
            <th>Start Time</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {sorted.length === 0 ? (
            <tr>
              <td colSpan={5} className="muted">
                No active incidents right now.
              </td>
            </tr>
          ) : (
            sorted.map((incident) => (
              <tr key={incident.id}>
                <td>{incident.component_id}</td>
                <td>
                  <span className={`severity ${incident.severity.toLowerCase()}`}>{incident.severity}</span>
                </td>
                <td>
                  <span className="status-badge">{incident.state}</span>
                </td>
                <td>{new Date(incident.start_time).toLocaleString()}</td>
                <td>
                  <Link className="link-chip" to={`/incident/${incident.id}`}>
                    View
                  </Link>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  )
}
