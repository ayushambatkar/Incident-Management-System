import axios from 'axios'

const baseURL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export const api = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export type Severity = 'P0' | 'P1' | 'P2' | 'P3'
export type IncidentState = 'OPEN' | 'INVESTIGATING' | 'RESOLVED' | 'CLOSED'

export interface IncidentSummary {
  id: number
  component_id: string
  severity: Severity
  state: IncidentState
  start_time: string
  end_time?: string | null
  mttr_seconds?: number | null
}

export interface RCAFormPayload {
  root_cause: string
  fix: string
  prevention: string
}

export interface IncidentDetail extends IncidentSummary {
  rca?: RCAFormPayload | null
  signals: Array<{
    _id?: string
    component_id: string
    work_item_id: number
    payload: {
      component_id: string
      severity: Severity
      message: string
      timestamp: number
    }
    timestamp: string
  }>
}

export type SeedMode = 'burst' | 'stream'

export interface SeedJob {
  job_id: string
  mode: SeedMode
  requested_count: number
  sent_count: number
  rate?: number | null
  status: 'running' | 'completed' | 'failed'
  started_at: string
  finished_at?: string | null
  error?: string | null
}

export interface SeedStatus {
  active_jobs: number
  total_signals_sent: number
  jobs: SeedJob[]
}

export async function fetchIncidents() {
  const response = await api.get<IncidentSummary[]>('/incidents')
  return response.data
}

export async function fetchIncident(id: number) {
  const response = await api.get<IncidentDetail>(`/incident/${id}`)
  return response.data
}

export async function updateIncidentState(id: number, state: IncidentState) {
  const response = await api.put<IncidentSummary>(`/incident/${id}/state`, { state })
  return response.data
}

export async function submitRca(id: number, payload: RCAFormPayload) {
  const response = await api.post<IncidentDetail>(`/incident/${id}/rca`, payload)
  return response.data
}

export async function startSeedJob(count: number, mode: SeedMode, rate = 10) {
  const response = await api.post<{ status: string }>('/seed', null, {
    params: { count, mode, rate },
  })
  return response.data
}

export async function fetchSeedStatus() {
  const response = await api.get<SeedStatus>('/seed/status')
  return response.data
}
