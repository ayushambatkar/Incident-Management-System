import { useEffect, useState } from 'react'
import { fetchSeedStatus, startSeedJob, type SeedMode, type SeedStatus } from '../services/api'

export default function SeedPanel() {
  const [count, setCount] = useState<number>(100)
  const [mode, setMode] = useState<SeedMode>('burst')
  const [rate, setRate] = useState<number>(10)
  const [busy, setBusy] = useState(false)
  const [status, setStatus] = useState<SeedStatus | null>(null)
  const [message, setMessage] = useState<string | null>(null)

  const loadStatus = async () => {
    try {
      const data = await fetchSeedStatus()
      setStatus(data)
    } catch {
      setStatus(null)
    }
  }

  useEffect(() => {
    loadStatus()
    const timer = window.setInterval(loadStatus, 5000)
    return () => window.clearInterval(timer)
  }, [])

  const submit = async () => {
    try {
      setBusy(true)
      setMessage(null)
      await startSeedJob(count, mode, rate)
      setMessage('Signal generation started in background.')
      await loadStatus()
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Failed to start seeding job')
    } finally {
      setBusy(false)
    }
  }

  const latestJobs = (status?.jobs ?? []).slice(0, 3)

  return (
    <div className="card stack">
      <div className="card-header seed-header">
        <div>
          <h3>Generate Signals</h3>
          <p className="muted">Push synthetic signals through queue and worker for demos and tests.</p>
        </div>
        <button className="button" disabled={busy} onClick={submit}>Run Seed</button>
      </div>

      <div className="seed-form-grid">
        <label>
          <span className="meta-label">Count</span>
          <select className="select" value={count} onChange={(event) => setCount(Number(event.target.value))}>
            <option value={100}>100</option>
            <option value={1000}>1000</option>
          </select>
        </label>

        <label>
          <span className="meta-label">Mode</span>
          <select className="select" value={mode} onChange={(event) => setMode(event.target.value as SeedMode)}>
            <option value="burst">burst</option>
            <option value="stream">stream</option>
          </select>
        </label>

        <label>
          <span className="meta-label">Rate (signals/sec)</span>
          <input
            className="input"
            type="number"
            min={1}
            max={100}
            value={rate}
            disabled={mode === 'burst'}
            onChange={(event) => setRate(Number(event.target.value))}
          />
        </label>
      </div>

      {message ? <div className="alert success">{message}</div> : null}

      <div className="seed-status-grid">
        <div className="meta-item">
          <span className="meta-label">Active Seed Jobs</span>
          <strong>{status?.active_jobs ?? 0}</strong>
        </div>
        <div className="meta-item">
          <span className="meta-label">Total Signals Sent</span>
          <strong>{status?.total_signals_sent ?? 0}</strong>
        </div>
      </div>

      {latestJobs.length > 0 ? (
        <div className="stack">
          <h3>Recent Seed Jobs</h3>
          {latestJobs.map((job) => (
            <article key={job.job_id} className="signal-item">
              <p>
                <strong>{job.mode}</strong> · {job.sent_count}/{job.requested_count} · {job.status}
              </p>
              <p className="muted">{new Date(job.started_at).toLocaleString()}</p>
              {job.error ? <p className="alert error">{job.error}</p> : null}
            </article>
          ))}
        </div>
      ) : null}
    </div>
  )
}
