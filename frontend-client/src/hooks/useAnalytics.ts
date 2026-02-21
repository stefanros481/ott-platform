import { useCallback } from 'react'
import { emitEvent, type AnalyticsEventPayload } from '../api/analytics'

// Region is derived server-side from the user's account.
// The frontend passes the region from the JWT/user context when available,
// otherwise falls back to "NO" as the DB-level default for Nordic PoC data.
const DEFAULT_REGION = 'NO'

function getRegion(): string {
  // In a production system this would come from the user's profile/account.
  // For this PoC, we use a sensible Nordic default.
  return DEFAULT_REGION
}

function nowISO(): string {
  return new Date().toISOString()
}

export function useAnalytics() {
  const trackPlay = useCallback(
    (
      titleId: string,
      serviceType: AnalyticsEventPayload['service_type'],
      sessionId?: string,
      profileId?: string,
    ) => {
      emitEvent({
        event_type: 'play_start',
        title_id: titleId,
        service_type: serviceType,
        profile_id: profileId ?? null,
        region: getRegion(),
        occurred_at: nowISO(),
        session_id: sessionId ?? null,
      })
    },
    [],
  )

  const trackPause = useCallback(
    (
      titleId: string,
      serviceType: AnalyticsEventPayload['service_type'],
      sessionId?: string,
      profileId?: string,
    ) => {
      emitEvent({
        event_type: 'play_pause',
        title_id: titleId,
        service_type: serviceType,
        profile_id: profileId ?? null,
        region: getRegion(),
        occurred_at: nowISO(),
        session_id: sessionId ?? null,
      })
    },
    [],
  )

  const trackComplete = useCallback(
    (
      titleId: string,
      serviceType: AnalyticsEventPayload['service_type'],
      sessionId?: string,
      profileId?: string,
      durationSeconds?: number,
      watchPercentage?: number,
    ) => {
      emitEvent({
        event_type: 'play_complete',
        title_id: titleId,
        service_type: serviceType,
        profile_id: profileId ?? null,
        region: getRegion(),
        occurred_at: nowISO(),
        session_id: sessionId ?? null,
        duration_seconds: durationSeconds ?? null,
        watch_percentage: watchPercentage ?? null,
      })
    },
    [],
  )

  const trackBrowse = useCallback(
    (
      serviceType: AnalyticsEventPayload['service_type'],
      extraData?: Record<string, unknown>,
      titleId?: string,
    ) => {
      emitEvent({
        event_type: 'browse',
        title_id: titleId ?? null,
        service_type: serviceType,
        region: getRegion(),
        occurred_at: nowISO(),
        extra_data: extraData ?? null,
      })
    },
    [],
  )

  const trackSearch = useCallback(
    (query: string, serviceType: AnalyticsEventPayload['service_type']) => {
      emitEvent({
        event_type: 'search',
        title_id: null,
        service_type: serviceType,
        region: getRegion(),
        occurred_at: nowISO(),
        extra_data: { query },
      })
    },
    [],
  )

  return { trackPlay, trackPause, trackComplete, trackBrowse, trackSearch }
}
