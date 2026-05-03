import { useState } from 'react'
import type { RCAFormPayload } from '../services/api'

interface Props {
  visible: boolean
  onSubmit: (payload: RCAFormPayload) => Promise<void>
  busy?: boolean
}

const causeOptions = ['Code regression', 'Infrastructure issue', 'Third-party outage', 'Capacity exhaustion', 'Configuration error', 'Unknown']

export default function RcaForm({ visible, onSubmit, busy = false }: Props) {
  const [rootCause, setRootCause] = useState('Unknown')
  const [fix, setFix] = useState('')
  const [prevention, setPrevention] = useState('')

  if (!visible) {
    return null
  }

  return (
    <form
      className="card stack"
      onSubmit={async (event) => {
        event.preventDefault()
        await onSubmit({ root_cause: rootCause, fix, prevention })
      }}
    >
      <h3>RCA</h3>

      <label>
        <span className="meta-label">Root Cause</span>
        <select className="select" value={rootCause} onChange={(event) => setRootCause(event.target.value)}>
          {causeOptions.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </label>

      <label>
        <span className="meta-label">Fix Applied</span>
        <textarea className="textarea" value={fix} onChange={(event) => setFix(event.target.value)} />
      </label>

      <label>
        <span className="meta-label">Prevention Steps</span>
        <textarea className="textarea" value={prevention} onChange={(event) => setPrevention(event.target.value)} />
      </label>

      <button className="button" type="submit" disabled={busy}>
        Submit RCA
      </button>
    </form>
  )
}
