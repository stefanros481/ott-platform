import { useEffect, useRef, useCallback, useState } from 'react'
import {
  getBalance,
  sendHeartbeat,
  endSession,
  type ViewingTimeBalance,
  type HeartbeatResponse,
  type EnforcementStatus,
} from '../api/viewingTime'

// ── Stable device ID ────────────────────────────────────────────────────────

function getDeviceId(): string {
  const key = 'device_id'
  let id = localStorage.getItem(key)
  if (!id) {
    id = crypto.randomUUID()
    localStorage.setItem(key, id)
  }
  return id
}

// ── Balance polling hook ────────────────────────────────────────────────────

const POLL_NORMAL_MS = 60_000
const POLL_LOCKED_MS = 10_000

export interface UseViewingTimeReturn {
  balance: ViewingTimeBalance | null
  remainingMinutes: number | null
  isLocked: boolean
  enforcement: EnforcementStatus | null
  isLoading: boolean
  showWarning15: boolean
  showWarning5: boolean
  canPlay: boolean
  dismissWarning15: () => void
  dismissWarning5: () => void
  refetchBalance: () => void
}

/** Consecutive fetch errors before we fail-closed and lock the screen. */
const FAIL_CLOSED_THRESHOLD = 2

export function useViewingTime(profileId: string): UseViewingTimeReturn {
  const [balance, setBalance] = useState<ViewingTimeBalance | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isLocked, setIsLocked] = useState(false)
  const [enforcement, setEnforcement] = useState<EnforcementStatus | null>(null)
  const [showWarning15, setShowWarning15] = useState(false)
  const [showWarning5, setShowWarning5] = useState(false)

  const warning15ShownRef = useRef(false)
  const warning5ShownRef = useRef(false)
  const intervalRef = useRef<ReturnType<typeof setInterval>>()
  const profileIdRef = useRef(profileId)
  const consecutiveErrorsRef = useRef(0)
  profileIdRef.current = profileId

  const fetchBalance = useCallback(async () => {
    if (!profileIdRef.current) return
    try {
      const data = await getBalance(profileIdRef.current)
      consecutiveErrorsRef.current = 0
      setBalance(data)

      // Derive enforcement from balance
      if (!data.has_limits || data.is_unlimited_override) {
        setEnforcement('allowed')
        setIsLocked(false)
      } else if (data.remaining_minutes !== null && data.remaining_minutes <= 0) {
        setEnforcement('blocked')
        setIsLocked(true)
      } else if (data.remaining_minutes !== null && data.remaining_minutes <= 5) {
        setEnforcement('warning_5')
        setIsLocked(false)
        if (!warning5ShownRef.current) {
          setShowWarning5(true)
          warning5ShownRef.current = true
        }
      } else if (data.remaining_minutes !== null && data.remaining_minutes <= 15) {
        setEnforcement('warning_15')
        setIsLocked(false)
        if (!warning15ShownRef.current) {
          setShowWarning15(true)
          warning15ShownRef.current = true
        }
      } else {
        setEnforcement('allowed')
        setIsLocked(false)
      }
    } catch {
      // Fail-closed: lock after consecutive failures so kids can't bypass
      // limits by blocking the API endpoint (C-01 security fix)
      consecutiveErrorsRef.current += 1
      if (consecutiveErrorsRef.current >= FAIL_CLOSED_THRESHOLD) {
        setEnforcement('blocked')
        setIsLocked(true)
      }
    } finally {
      setIsLoading(false)
    }
  }, [])

  // Initial fetch
  useEffect(() => {
    if (!profileId) return
    setIsLoading(true)
    warning15ShownRef.current = false
    warning5ShownRef.current = false
    fetchBalance()
  }, [profileId, fetchBalance])

  // Polling with accelerated interval when locked (T027)
  useEffect(() => {
    if (!profileId) return

    const interval = isLocked ? POLL_LOCKED_MS : POLL_NORMAL_MS
    intervalRef.current = setInterval(fetchBalance, interval)

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [profileId, isLocked, fetchBalance])

  // Auto-dismiss lock screen when balance shows time available (T027)
  useEffect(() => {
    if (balance && isLocked) {
      if (
        balance.is_unlimited_override ||
        !balance.has_limits ||
        (balance.remaining_minutes !== null && balance.remaining_minutes > 0)
      ) {
        setIsLocked(false)
        setEnforcement('allowed')
      }
    }
  }, [balance, isLocked])

  const dismissWarning15 = useCallback(() => setShowWarning15(false), [])
  const dismissWarning5 = useCallback(() => setShowWarning5(false), [])

  const canPlay = !isLocked
  const remainingMinutes = balance?.remaining_minutes ?? null

  return {
    balance,
    remainingMinutes,
    isLocked,
    enforcement,
    isLoading,
    showWarning15,
    showWarning5,
    canPlay,
    dismissWarning15,
    dismissWarning5,
    refetchBalance: fetchBalance,
  }
}

// ── Heartbeat hook ──────────────────────────────────────────────────────────

const HEARTBEAT_INTERVAL_MS = 30_000

export interface UseHeartbeatReturn {
  enforcement: EnforcementStatus | null
  remainingMinutes: number | null
  isEducational: boolean
  sessionId: string | null
}

export function useHeartbeat(
  profileId: string,
  titleId: string,
  deviceId?: string,
  isPlaying?: boolean,
): UseHeartbeatReturn {
  const resolvedDeviceId = deviceId || getDeviceId()
  const [enforcement, setEnforcement] = useState<EnforcementStatus | null>(null)
  const [remainingMinutes, setRemainingMinutes] = useState<number | null>(null)
  const [isEducational, setIsEducational] = useState(false)
  const [sessionId, setSessionId] = useState<string | null>(null)

  const intervalRef = useRef<ReturnType<typeof setInterval>>()
  const sessionIdRef = useRef<string | null>(null)
  const profileIdRef = useRef(profileId)
  const titleIdRef = useRef(titleId)
  const deviceIdRef = useRef(resolvedDeviceId)

  profileIdRef.current = profileId
  titleIdRef.current = titleId
  deviceIdRef.current = resolvedDeviceId

  const doHeartbeat = useCallback(async (isPaused: boolean) => {
    if (!profileIdRef.current || !titleIdRef.current) return
    try {
      const resp: HeartbeatResponse = await sendHeartbeat({
        profile_id: profileIdRef.current,
        session_id: sessionIdRef.current || undefined,
        title_id: titleIdRef.current,
        device_id: deviceIdRef.current,
        is_paused: isPaused,
      })
      sessionIdRef.current = resp.session_id
      setSessionId(resp.session_id)
      setEnforcement(resp.enforcement)
      setRemainingMinutes(resp.remaining_minutes)
      setIsEducational(resp.is_educational)
    } catch {
      // Silently handle heartbeat failure
    }
  }, [])

  // Start/stop heartbeat based on isPlaying
  useEffect(() => {
    if (!isPlaying) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = undefined
      }
      return
    }

    // Send initial heartbeat immediately
    doHeartbeat(false)

    intervalRef.current = setInterval(() => {
      doHeartbeat(false)
    }, HEARTBEAT_INTERVAL_MS)

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = undefined
      }
    }
  }, [isPlaying, doHeartbeat])

  // End session on unmount
  useEffect(() => {
    return () => {
      if (sessionIdRef.current) {
        endSession(sessionIdRef.current).catch(() => {
          // Best effort
        })
      }
    }
  }, [])

  return {
    enforcement,
    remainingMinutes,
    isEducational,
    sessionId,
  }
}
