import { apiFetch } from '@/api/client'

// ── Types (T003) ──────────────────────────────────────────────────────────────

export interface QueryRequest {
  question: string // 3–1000 characters
}

export interface QueryResult {
  summary: string
  confidence: number // 0.0–1.0
  data: Record<string, unknown>[]
  applied_filters: {
    region: string | null
    time_period: string | null
    service_type: string | null
  }
  data_sources: string[]
  data_freshness: string // ISO 8601 datetime
  coverage_start: string // ISO 8601 datetime
}

export interface ClarificationPayload {
  type: 'clarification'
  clarifying_question: string
  context: string
}

export interface QueryResponse {
  status: 'complete' | 'pending' | 'clarification'
  result: QueryResult | null
  job_id: string | null
  clarification: ClarificationPayload | null
}

export interface JobStatusResponse {
  job_id: string
  status: 'pending' | 'complete' | 'failed'
  submitted_at: string // ISO 8601
  completed_at: string | null
  result: QueryResult | null
  error_message: string | null
}

export interface HistoryEntry {
  id: string // uuid generated client-side for React key
  question: string
  submittedAt: Date
  status: 'complete' | 'clarification' | 'failed'
  result: QueryResult | null
  clarification: ClarificationPayload | null
  errorMessage: string | null
}

export type ActiveQueryState =
  | { phase: 'idle' }
  | { phase: 'submitting' }
  | { phase: 'polling'; jobId: string }
  | { phase: 'complete'; result: QueryResult }
  | { phase: 'clarification'; payload: ClarificationPayload }
  | { phase: 'failed'; errorMessage: string }
  | { phase: 'timeout' }

// ── API functions ─────────────────────────────────────────────────────────────

// T004
export function submitQuery(question: string): Promise<QueryResponse> {
  return apiFetch<QueryResponse>('/content-analytics/query', {
    method: 'POST',
    body: JSON.stringify({ question }),
  })
}

// T005
export function pollJob(jobId: string): Promise<JobStatusResponse> {
  return apiFetch<JobStatusResponse>(`/content-analytics/jobs/${jobId}`)
}
