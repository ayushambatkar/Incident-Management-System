import type { IncidentState } from '../services/api'

interface Props {
  currentState: IncidentState
  onTransition: (state: IncidentState) => Promise<void>
  busy?: boolean
}

const transitions: Record<IncidentState, IncidentState[]> = {
  OPEN: ['INVESTIGATING'],
  INVESTIGATING: ['RESOLVED'],
  RESOLVED: ['CLOSED'],
  CLOSED: [],
}

export default function StateControls({ currentState, onTransition, busy = false }: Props) {
  const available = transitions[currentState]

  return (
    <div className="actions-row">
      {available.length === 0 ? (
        <span className="muted">No further transitions available.</span>
      ) : (
        available.map((state) => (
          <button key={state} className={state === 'CLOSED' ? 'button danger' : 'button secondary'} disabled={busy} onClick={() => onTransition(state)}>
            Move to {state}
          </button>
        ))
      )}
    </div>
  )
}
