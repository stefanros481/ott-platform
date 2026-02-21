import { apiFetch } from './client'

export interface AnalyticsEventPayload {
  event_type: 'play_start' | 'play_pause' | 'play_complete' | 'browse' | 'search'
  title_id?: string | null
  service_type: 'Linear' | 'VoD' | 'SVoD' | 'TSTV' | 'Catch_up' | 'Cloud_PVR'
  profile_id?: string | null
  region: string
  occurred_at: string // ISO 8601
  session_id?: string | null
  duration_seconds?: number | null
  watch_percentage?: number | null
  extra_data?: Record<string, unknown> | null
}

/**
 * Fire-and-forget analytics event emitter.
 * Silently swallows all errors — analytics failures must never affect the viewer
 * experience (FR-011).
 */
export async function emitEvent(event: AnalyticsEventPayload): Promise<void> {
  try {
    await apiFetch<void>('/analytics/events', {
      method: 'POST',
      body: JSON.stringify(event),
    })
  } catch {
    // Silent failure — never propagate analytics errors to the UI
  }
}
