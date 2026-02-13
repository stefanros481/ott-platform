import { apiFetch } from './client'

// -- Types --

export type EnforcementStatus = 'allowed' | 'warning_15' | 'warning_5' | 'blocked'
export type DeviceType = 'tv' | 'mobile' | 'tablet' | 'web'

export interface ViewingTimeBalance {
  profile_id: string
  is_child_profile: boolean
  has_limits: boolean
  used_minutes: number
  educational_minutes: number
  limit_minutes: number | null
  remaining_minutes: number | null
  is_unlimited_override: boolean
  next_reset_at: string | null
  warning_threshold_minutes: number[]
}

export interface HeartbeatRequest {
  profile_id: string
  session_id?: string
  title_id: string
  device_id: string
  device_type?: DeviceType
  is_paused?: boolean
}

export interface HeartbeatResponse {
  session_id: string
  enforcement: EnforcementStatus
  remaining_minutes: number | null
  used_minutes: number
  is_educational: boolean
}

export interface SessionEndResponse {
  session_id: string
  total_seconds: number
  ended_at: string
}

export interface PlaybackEligibility {
  eligible: boolean
  remaining_minutes: number | null
  reason: string | null
  next_reset_at: string | null
}

// -- API functions --

export function getBalance(profileId: string): Promise<ViewingTimeBalance> {
  return apiFetch(`/viewing-time/balance/${profileId}`)
}

export function sendHeartbeat(req: HeartbeatRequest): Promise<HeartbeatResponse> {
  return apiFetch('/viewing-time/heartbeat', {
    method: 'POST',
    body: JSON.stringify(req),
  })
}

export function endSession(sessionId: string): Promise<SessionEndResponse> {
  return apiFetch(`/viewing-time/session/${sessionId}/end`, {
    method: 'POST',
  })
}

export function checkPlaybackEligibility(profileId: string): Promise<PlaybackEligibility> {
  return apiFetch(`/viewing-time/playback-eligible/${profileId}`)
}
