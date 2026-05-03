import { useEffect, useState } from 'react'
import { fetchIncidents, type IncidentSummary } from '../services/api'

export function useIncidents(pollMs = 5000) {
  const [incidents, setIncidents] = useState<IncidentSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let mounted = true

    const load = async () => {
      try {
        const data = await fetchIncidents()
        if (!mounted) return
        setIncidents(data)
        setError(null)
      } catch (err) {
        if (!mounted) return
        setError(err instanceof Error ? err.message : 'Failed to load incidents')
      } finally {
        if (mounted) {
          setLoading(false)
        }
      }
    }

    load()
    const timer = window.setInterval(load, pollMs)

    return () => {
      mounted = false
      window.clearInterval(timer)
    }
  }, [pollMs])

  return { incidents, loading, error, refresh: async () => fetchIncidents() }
}
