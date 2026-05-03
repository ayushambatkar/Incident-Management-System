import { useEffect, useState } from 'react'
import { fetchIncident, type IncidentDetail } from '../services/api'

export function useIncidentDetail(id: number | null) {
  const [incident, setIncident] = useState<IncidentDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (id === null) {
      setIncident(null)
      setLoading(false)
      return
    }

    let mounted = true

    const load = async () => {
      try {
        const data = await fetchIncident(id)
        if (!mounted) return
        setIncident(data)
        setError(null)
      } catch (err) {
        if (!mounted) return
        setError(err instanceof Error ? err.message : 'Failed to load incident')
      } finally {
        if (mounted) {
          setLoading(false)
        }
      }
    }

    setLoading(true)
    load()

    return () => {
      mounted = false
    }
  }, [id])

  return { incident, loading, error, setIncident }
}
