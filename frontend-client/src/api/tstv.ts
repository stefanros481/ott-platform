import { apiFetch } from './client'

// ---------------------------------------------------------------------------
// TSTV Channels
// ---------------------------------------------------------------------------

export interface TSTVChannel {
  id: string
  name: string
  cdn_channel_key: string
  tstv_enabled: boolean
  startover_enabled: boolean
  catchup_enabled: boolean
  cutv_window_hours: number
}

export function fetchTSTVChannels(): Promise<TSTVChannel[]> {
  return apiFetch<TSTVChannel[]>('/tstv/channels')
}

// ---------------------------------------------------------------------------
// Start Over
// ---------------------------------------------------------------------------

export interface ScheduleEntrySummary {
  id: string
  channel_id: string
  title: string
  synopsis: string | null
  genre: string | null
  start_time: string
  end_time: string
  catchup_eligible: boolean
  startover_eligible: boolean
}

export interface StartOverAvailability {
  channel_id: string
  schedule_entry: ScheduleEntrySummary
  startover_available: boolean
  elapsed_seconds: number
}

export function getStartOverAvailability(channelId: string): Promise<StartOverAvailability> {
  return apiFetch<StartOverAvailability>(`/tstv/startover/${channelId}`)
}

export function getStartOverManifestUrl(channelId: string, scheduleEntryId: string): string {
  const base = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'
  return `${base}/tstv/startover/${channelId}/manifest?schedule_entry_id=${scheduleEntryId}`
}

// ---------------------------------------------------------------------------
// Catch-Up
// ---------------------------------------------------------------------------

export interface CatchUpProgram {
  schedule_entry: ScheduleEntrySummary
  expires_at: string
  bookmark_position_seconds: number | null
}

export interface CatchUpListResponse {
  programs: CatchUpProgram[]
  total: number
}

export interface CatchUpByDateResponse {
  programs: CatchUpProgram[]
  total: number
  date: string
}

export function listCatchUpPrograms(
  channelId: string,
  limit = 50,
  offset = 0,
): Promise<CatchUpListResponse> {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) })
  return apiFetch<CatchUpListResponse>(`/tstv/catchup/${channelId}?${params}`)
}

export function listCatchUpByDate(
  date?: string,
  channelId?: string,
  genre?: string,
  limit = 50,
  offset = 0,
  profileId?: string,
): Promise<CatchUpByDateResponse> {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) })
  if (date) params.set('date', date)
  if (channelId) params.set('channel_id', channelId)
  if (genre) params.set('genre', genre)
  if (profileId) params.set('profile_id', profileId)
  return apiFetch<CatchUpByDateResponse>(`/tstv/catchup?${params}`)
}

export function getCatchUpManifestUrl(channelId: string, scheduleEntryId: string): string {
  const base = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'
  return `${base}/tstv/catchup/${channelId}/manifest?schedule_entry_id=${scheduleEntryId}`
}

// ---------------------------------------------------------------------------
// DRM ClearKeys
// ---------------------------------------------------------------------------

export function getClearKeys(channelId: string): Promise<{ keys: Record<string, string> }> {
  return apiFetch<{ keys: Record<string, string> }>(`/drm/clearkeys/${channelId}`)
}

// ---------------------------------------------------------------------------
// TSTV Sessions
// ---------------------------------------------------------------------------

export interface TSTVSession {
  id: number
  channel_id: string
  schedule_entry_id: string
  session_type: 'startover' | 'catchup'
  started_at: string
  last_position_s: number
  completed: boolean
}

export function createTSTVSession(
  channelId: string,
  scheduleEntryId: string,
  sessionType: 'startover' | 'catchup',
  profileId?: string,
): Promise<TSTVSession> {
  return apiFetch<TSTVSession>('/tstv/sessions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      channel_id: channelId,
      schedule_entry_id: scheduleEntryId,
      session_type: sessionType,
      profile_id: profileId ?? null,
    }),
  })
}

export function updateTSTVSession(
  sessionId: number,
  lastPositionS?: number,
  completed?: boolean,
): Promise<TSTVSession> {
  const body: Record<string, unknown> = {}
  if (lastPositionS !== undefined) body.last_position_s = lastPositionS
  if (completed !== undefined) body.completed = completed
  return apiFetch<TSTVSession>(`/tstv/sessions/${sessionId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}
