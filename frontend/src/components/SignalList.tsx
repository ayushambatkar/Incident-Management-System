interface Props {
  signals: Array<{
    _id?: string
    component_id: string
    work_item_id: number
    payload: {
      message: string
      timestamp: number
    }
    timestamp: string
  }>
}

export default function SignalList({ signals }: Props) {
  if (signals.length === 0) {
    return <p className="muted">No raw signals recorded yet.</p>
  }

  return (
    <div className="signal-list">
      {signals.map((signal) => (
        <article className="signal-item" key={signal._id ?? `${signal.work_item_id}-${signal.timestamp}`}>
          <strong>{new Date(signal.timestamp).toLocaleString()}</strong>
          <p className="muted">{signal.payload.message}</p>
        </article>
      ))}
    </div>
  )
}
