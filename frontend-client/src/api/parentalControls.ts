import { apiFetch } from './client'

// -- Types --

export interface PinVerifyResponse {
  verified: boolean
  pin_token: string | null
}

export interface PinError {
  detail: string
  // M-09: remaining_attempts removed — server no longer sends attempt count
  locked_until: string | null
}

export interface ViewingTimeConfig {
  profile_id: string
  weekday_limit_minutes: number | null
  weekend_limit_minutes: number | null
  reset_hour: number
  educational_exempt: boolean
  timezone: string
  updated_at: string
}

export interface ViewingTimeConfigUpdate {
  weekday_limit_minutes?: number | null
  weekend_limit_minutes?: number | null
  reset_hour?: number
  educational_exempt?: boolean
  timezone?: string
  pin_token?: string
}

export interface GrantExtraTimeResponse {
  granted_minutes: number | null
  remaining_minutes: number | null
  is_unlimited_override: boolean
}

export interface ViewingHistorySession {
  session_id: string
  title_id: string
  title_name: string
  device_type: string | null
  is_educational: boolean
  started_at: string
  ended_at: string | null
  duration_minutes: number
}

export interface ViewingHistoryDay {
  date: string
  total_minutes: number
  educational_minutes: number
  counted_minutes: number
  sessions: ViewingHistorySession[]
}

export interface ViewingHistoryResponse {
  profile_id: string
  days: ViewingHistoryDay[]
}

export interface TopTitle {
  title_id: string
  title_name: string
  total_minutes: number
}

export interface ProfileWeeklyStats {
  profile_id: string
  profile_name: string
  daily_totals: { date: string; counted_minutes: number; educational_minutes: number }[]
  average_daily_minutes: number
  total_minutes: number
  educational_minutes: number
  limit_usage_percent: number | null
  top_titles: TopTitle[]
}

export interface WeeklyReportResponse {
  week_start: string
  week_end: string
  profiles: ProfileWeeklyStats[]
}

// -- PIN management --

export function createPin(newPin: string, currentPin?: string): Promise<{ detail: string }> {
  return apiFetch('/parental-controls/pin', {
    method: 'POST',
    body: JSON.stringify({ new_pin: newPin, current_pin: currentPin }),
  })
}

export function verifyPin(pin: string): Promise<PinVerifyResponse> {
  return apiFetch('/parental-controls/pin/verify', {
    method: 'POST',
    body: JSON.stringify({ pin }),
  })
}

export function resetPin(password: string, newPin: string): Promise<{ detail: string }> {
  return apiFetch('/parental-controls/pin/reset', {
    method: 'POST',
    body: JSON.stringify({ password, new_pin: newPin }),
  })
}

// -- Viewing Time Config --

export function getViewingTimeConfig(profileId: string): Promise<ViewingTimeConfig> {
  return apiFetch(`/parental-controls/profiles/${profileId}/viewing-time`)
}

export function updateViewingTimeConfig(
  profileId: string,
  config: ViewingTimeConfigUpdate,
): Promise<ViewingTimeConfig> {
  return apiFetch(`/parental-controls/profiles/${profileId}/viewing-time`, {
    method: 'PUT',
    body: JSON.stringify(config),
  })
}

// -- Grant Extra Time --

export function grantExtraTime(
  profileId: string,
  minutes: number | null,
  pin?: string,
  pinToken?: string,
): Promise<GrantExtraTimeResponse> {
  return apiFetch(`/parental-controls/profiles/${profileId}/viewing-time/grant`, {
    method: 'POST',
    body: JSON.stringify({ minutes, pin, pin_token: pinToken }),
  })
}

// -- History & Reports --

export function getViewingHistory(
  profileId: string,
  fromDate?: string,
  toDate?: string,
): Promise<ViewingHistoryResponse> {
  const params = new URLSearchParams()
  if (fromDate) params.set('from_date', fromDate)
  if (toDate) params.set('to_date', toDate)
  const qs = params.toString()
  return apiFetch(`/parental-controls/profiles/${profileId}/history${qs ? `?${qs}` : ''}`)
}

export function getWeeklyReport(): Promise<WeeklyReportResponse> {
  return apiFetch('/parental-controls/weekly-report')
}
