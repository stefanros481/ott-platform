import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useParams, useNavigate, useLocation } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useAuth } from '../context/AuthContext'
import { getTitleById } from '../api/catalog'
import { getBookmarkByContent, createStreamSession, heartbeatSession, stopSession, listActiveSessions } from '../api/viewing'
import { type Channel, type ScheduleEntry, getSchedule } from '../api/epg'
import { useBookmarkSync } from '../hooks/useBookmarkSync'
import { useViewingTime, useHeartbeat } from '../hooks/useViewingTime'
import LockScreen from '../components/LockScreen'
import ViewingTimeWarning from '../components/ViewingTimeWarning'
import VideoPlayer from '../components/VideoPlayer'

function formatTime(seconds: number): string {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
  return `${m}:${String(s).padStart(2, '0')}`
}

export default function PlayerPage() {
  const { type, id } = useParams<{ type: string; id: string }>()
  const navigate = useNavigate()
  const location = useLocation()
  const { profile } = useAuth()
  const queryClient = useQueryClient()
  const [nextEpisodeCountdown, setNextEpisodeCountdown] = useState<number | null>(null)
  const [videoDuration, setVideoDuration] = useState(0)
  const [playerIsPlaying, setPlayerIsPlaying] = useState(false)
  const [startPosition, setStartPosition] = useState<number | undefined>(undefined)
  const [resumePromptDismissed, setResumePromptDismissed] = useState(false)

  // Stream session state — tracks the concurrent stream session with the backend
  const [streamError, setStreamError] = useState<'no_access' | 'stream_limit' | 'session_ended' | null>(null)
  const [streamSessionReady, setStreamSessionReady] = useState(false)
  const [isStoppingOtherSessions, setIsStoppingOtherSessions] = useState(false)
  const streamSessionId = useRef<string | null>(null)
  const streamHeartbeatTimer = useRef<ReturnType<typeof setInterval> | null>(null)

  // Live TV state — channel from route state, program can update on transition
  const isLive = type === 'live'
  const routeState = location.state as { channel?: Channel; currentProgram?: ScheduleEntry } | null
  const liveChannel = isLive ? routeState?.channel ?? null : null
  const [liveProgram, setLiveProgram] = useState<ScheduleEntry | null>(routeState?.currentProgram ?? null)
  const liveProgramRef = useRef(liveProgram)
  liveProgramRef.current = liveProgram

  // For movies/episodes, fetch title data. Skip for live TV.
  const { data: title, isLoading } = useQuery({
    queryKey: ['title', id],
    queryFn: () => getTitleById(id!),
    enabled: !!id && !isLive,
  })

  // Derive playback info from title data without calling setState during render
  const playbackInfo = useMemo(() => {
    // Live TV — data comes from route state, not title query
    if (isLive) {
      if (!liveChannel?.hls_live_url) {
        return { manifestUrl: '', displayTitle: liveChannel?.name ?? 'Channel temporarily unavailable', contentType: 'movie' as const, contentId: id || '', nextEpisodeId: null as string | null }
      }
      const program = liveProgram
      const timeSlot = program
        ? `${new Date(program.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} – ${new Date(program.end_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`
        : ''
      return {
        manifestUrl: liveChannel.hls_live_url,
        displayTitle: program ? `${program.title} — ${timeSlot}` : liveChannel.name,
        contentType: 'movie' as const,
        contentId: id || '',
        nextEpisodeId: null as string | null,
      }
    }

    if (!title) return { manifestUrl: '', displayTitle: '', contentType: 'movie' as const, contentId: id || '', nextEpisodeId: null as string | null }

    if (type === 'movie') {
      return {
        manifestUrl: title.hls_manifest_url || '',
        displayTitle: title.title,
        contentType: 'movie' as const,
        contentId: title.id,
        nextEpisodeId: null,
      }
    }

    if (type === 'episode') {
      for (const season of title.seasons) {
        const episode = season.episodes.find(e => e.id === id)
        if (episode) {
          let nextEpId: string | null = null
          const epIndex = season.episodes.indexOf(episode)
          if (epIndex < season.episodes.length - 1) {
            const next = season.episodes[epIndex + 1]
            if (next) nextEpId = next.id
          } else {
            const seasonIndex = title.seasons.indexOf(season)
            if (seasonIndex < title.seasons.length - 1) {
              const nextSeason = title.seasons[seasonIndex + 1]
              if (nextSeason?.episodes.length) {
                const firstEp = nextSeason.episodes[0]
                if (firstEp) nextEpId = firstEp.id
              }
            }
          }

          return {
            manifestUrl: episode.hls_manifest_url || '',
            displayTitle: `${title.title} - S${season.season_number}E${episode.episode_number}: ${episode.title}`,
            contentType: 'episode' as const,
            contentId: episode.id,
            nextEpisodeId: nextEpId,
          }
        }
      }
    }

    return { manifestUrl: '', displayTitle: '', contentType: 'movie' as const, contentId: id || '', nextEpisodeId: null }
  }, [title, type, id, isLive, liveChannel, liveProgram])

  const { manifestUrl, displayTitle, contentType, contentId, nextEpisodeId } = playbackInfo

  // Fetch existing bookmark to offer resume — always fetch fresh, never serve stale cache
  const { data: existingBookmark, isLoading: bookmarkLoading } = useQuery({
    queryKey: ['bookmark', profile?.id, contentId],
    queryFn: () => getBookmarkByContent(profile!.id, contentId),
    enabled: !!profile && !!contentId && contentId !== '' && !isLive,
    gcTime: 0,
    staleTime: 0,
  })

  // Show the resume prompt if there's a non-completed bookmark with meaningful progress
  const showResumePrompt = !resumePromptDismissed
    && existingBookmark
    && !existingBookmark.completed
    && existingBookmark.position_seconds > 10

  // Only use the actual video duration from the player — title metadata may differ from the stream.
  const durationSeconds = videoDuration

  const { saveNow } = useBookmarkSync({
    profileId: profile?.id ?? '',
    contentType,
    contentId,
    durationSeconds,
    isPlaying: playerIsPlaying,
  })

  // Viewing time balance polling — drives warnings and lock screen
  const {
    isLocked: balanceLocked,
    isLoading: balanceLoading,
    showWarning15,
    showWarning5,
    dismissWarning15,
    dismissWarning5,
    balance,
    refetchBalance,
  } = useViewingTime(profile?.id ?? '')

  const [heartbeatBlocked, setHeartbeatBlocked] = useState(false)
  const isLocked = balanceLocked || heartbeatBlocked

  // Viewing time heartbeat — sends 30s heartbeats to track kids profile usage.
  const { enforcement, isEducational } = useHeartbeat(
    profile?.id ?? '',
    title?.id ?? '',
    undefined,
    playerIsPlaying && !isLocked,
  )

  // Lock immediately when heartbeat returns blocked (faster than balance polling)
  useEffect(() => {
    if (enforcement === 'blocked') {
      setHeartbeatBlocked(true)
    } else if (enforcement === 'allowed') {
      setHeartbeatBlocked(false)
    }
  }, [enforcement])

  const handleUnlocked = useCallback(() => {
    setHeartbeatBlocked(false)
    refetchBalance()
  }, [refetchBalance])

  // Stop all other active sessions and retry starting a new one
  const handleStopOtherSessions = useCallback(async () => {
    setIsStoppingOtherSessions(true)
    try {
      const sessions = await listActiveSessions()
      await Promise.allSettled(sessions.map(s => stopSession(s.session_id)))
      // Reset error and retry — the session effect will re-run on next render via state reset
      setStreamError(null)
      setStreamSessionReady(false)
      // Trigger re-run by momentarily clearing session state
      streamSessionId.current = null
      if (streamHeartbeatTimer.current) {
        clearInterval(streamHeartbeatTimer.current)
        streamHeartbeatTimer.current = null
      }
      // Retry session creation directly
      const session = await createStreamSession(contentId, 'vod_title')
      streamSessionId.current = session.session_id
      streamHeartbeatTimer.current = setInterval(async () => {
        if (streamSessionId.current) {
          try {
            await heartbeatSession(streamSessionId.current)
          } catch (err: any) {
            if (err?.status === 404) {
              clearInterval(streamHeartbeatTimer.current!)
              streamHeartbeatTimer.current = null
              streamSessionId.current = null
              setStreamError('session_ended')
            }
          }
        }
      }, 30_000)
      setStreamSessionReady(true)
    } catch (err: any) {
      if (err?.status === 429) {
        setStreamError('stream_limit')
      } else {
        setStreamSessionReady(true) // fail open
      }
    } finally {
      setIsStoppingOtherSessions(false)
    }
  }, [contentId])

  // ── Stream session management ─────────────────────────────────────────────
  // For VOD titles (movie/episode), create a stream session before playback.
  // Live TV skips session management — handled differently server-side.
  useEffect(() => {
    if (isLive || !contentId || contentId === '') return
    // Wait until title data is available (or live) before creating session
    if (!isLive && isLoading) return

    let unmounted = false

    async function startSession() {
      try {
        const session = await createStreamSession(contentId, 'vod_title')
        if (unmounted) {
          // Component unmounted while the API call was in-flight — close the
          // orphaned session immediately so it doesn't block the stream limit.
          stopSession(session.session_id).catch(() => {})
          return
        }
        streamSessionId.current = session.session_id

        // Start 30-second heartbeat to keep the session alive.
        // 404 means the session was terminated externally (another device took over).
        streamHeartbeatTimer.current = setInterval(async () => {
          if (streamSessionId.current) {
            try {
              await heartbeatSession(streamSessionId.current)
            } catch (err: any) {
              if (err?.status === 404) {
                clearInterval(streamHeartbeatTimer.current!)
                streamHeartbeatTimer.current = null
                streamSessionId.current = null
                setStreamError('session_ended')
              }
              // Other errors: tolerate — transient network failures
            }
          }
        }, 30_000)

        setStreamSessionReady(true)
      } catch (err: any) {
        if (unmounted) return
        if (err?.status === 403) {
          setStreamError('no_access')
        } else if (err?.status === 429) {
          setStreamError('stream_limit')
        } else {
          // Unexpected error — still allow playback (fail open for better UX)
          setStreamSessionReady(true)
        }
      }
    }

    startSession()

    return () => {
      unmounted = true
      // Clean up heartbeat timer
      if (streamHeartbeatTimer.current) {
        clearInterval(streamHeartbeatTimer.current)
        streamHeartbeatTimer.current = null
      }
      // Stop stream session on unmount (if already established)
      if (streamSessionId.current) {
        stopSession(streamSessionId.current).catch(() => {
          // Fire-and-forget — best effort on unmount
        })
        streamSessionId.current = null
      }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [contentId, isLive, isLoading])

  const handlePositionUpdate = useCallback((positionSeconds: number) => {
    if (!title || !profile) return
    saveNow(positionSeconds)
  }, [title, profile, saveNow])

  const handleEnded = useCallback(() => {
    if (nextEpisodeId) {
      setNextEpisodeCountdown(10)
    } else {
      navigate(-1)
    }
  }, [nextEpisodeId, navigate])

  const handleResume = useCallback(() => {
    if (existingBookmark) {
      setStartPosition(existingBookmark.position_seconds)
    }
    setResumePromptDismissed(true)
  }, [existingBookmark])

  const handleStartOver = useCallback(() => {
    if (isLive && liveProgramRef.current) {
      const elapsed = (Date.now() - new Date(liveProgramRef.current.start_time).getTime()) / 1000
      setStartPosition(-Math.max(0, elapsed))
    } else {
      setStartPosition(0)
    }
    setResumePromptDismissed(true)
  }, [isLive])

  // Live TV: schedule a timer at program end_time to fetch the next program
  useEffect(() => {
    if (!isLive || !liveProgram || !liveChannel) return
    const endTime = new Date(liveProgram.end_time).getTime()
    const delay = endTime - Date.now()
    if (delay <= 0) return

    const timer = setTimeout(async () => {
      try {
        const today = new Date().toISOString().split('T')[0]!
        const schedule = await getSchedule(liveChannel.id, today)
        const now = Date.now()
        const next = schedule.find(
          (entry) => new Date(entry.start_time).getTime() <= now && new Date(entry.end_time).getTime() > now
        )
        if (next) setLiveProgram(next)
      } catch {
        // Silently continue — display title stays as channel name
      }
    }, delay + 1000)

    return () => clearTimeout(timer)
  }, [isLive, liveProgram, liveChannel])

  // Invalidate continue-watching cache on unmount so home page fetches fresh data.
  useEffect(() => {
    return () => {
      setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ['continueWatching'] })
      }, 500)
    }
  }, [queryClient])

  // Countdown for next episode
  useEffect(() => {
    if (nextEpisodeCountdown === null) return
    if (nextEpisodeCountdown <= 0) {
      navigate(`/play/episode/${nextEpisodeId}`, { replace: true })
      return
    }
    const timer = setTimeout(() => setNextEpisodeCountdown(prev => (prev !== null ? prev - 1 : null)), 1000)
    return () => clearTimeout(timer)
  }, [nextEpisodeCountdown, nextEpisodeId, navigate])

  // ── Stream access error screens ───────────────────────────────────────────
  if (streamError === 'no_access') {
    return (
      <div className="fixed inset-0 bg-black flex items-center justify-center">
        <div className="text-center max-w-sm px-6">
          <svg className="w-16 h-16 text-gray-500 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 1 0-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 0 0 2.25-2.25v-6.75a2.25 2.25 0 0 0-2.25-2.25H6.75a2.25 2.25 0 0 0-2.25 2.25v6.75a2.25 2.25 0 0 0 2.25 2.25Z" />
          </svg>
          <p className="text-white text-lg font-semibold mb-2">No access to this title</p>
          <p className="text-gray-400 text-sm mb-6">Purchase or subscribe to watch this content.</p>
          <button
            onClick={() => navigate(-1)}
            className="px-6 py-2.5 bg-white/20 text-white rounded-lg hover:bg-white/30 transition-colors"
          >
            Go Back
          </button>
        </div>
      </div>
    )
  }

  if (streamError === 'stream_limit') {
    return (
      <div className="fixed inset-0 bg-black flex items-center justify-center">
        <div className="text-center max-w-sm px-6">
          <svg className="w-16 h-16 text-gray-500 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 17.25v1.007a3 3 0 0 1-.879 2.122L7.5 21h9l-.621-.621A3 3 0 0 1 15 18.257V17.25m6-12V15a2.25 2.25 0 0 1-2.25 2.25H5.25A2.25 2.25 0 0 1 3 15V5.25m18 0A2.25 2.25 0 0 0 18.75 3H5.25A2.25 2.25 0 0 0 3 5.25m18 0H3" />
          </svg>
          <p className="text-white text-lg font-semibold mb-2">Stream limit reached</p>
          <p className="text-gray-400 text-sm mb-6">
            You've reached the maximum number of simultaneous streams for your plan.
          </p>
          <div className="flex flex-col gap-3">
            <button
              onClick={handleStopOtherSessions}
              disabled={isStoppingOtherSessions}
              className="px-6 py-2.5 bg-primary-500 text-white rounded-lg hover:bg-primary-400 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isStoppingOtherSessions ? 'Stopping other streams…' : 'Stop other streams & watch here'}
            </button>
            <button
              onClick={() => navigate(-1)}
              className="px-6 py-2.5 bg-white/20 text-white rounded-lg hover:bg-white/30 transition-colors"
            >
              Go Back
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (streamError === 'session_ended') {
    return (
      <div className="fixed inset-0 bg-black flex items-center justify-center">
        <div className="text-center max-w-sm px-6">
          <svg className="w-16 h-16 text-gray-500 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 17.25v1.007a3 3 0 0 1-.879 2.122L7.5 21h9l-.621-.621A3 3 0 0 1 15 18.257V17.25m6-12V15a2.25 2.25 0 0 1-2.25 2.25H5.25A2.25 2.25 0 0 1 3 15V5.25m18 0A2.25 2.25 0 0 0 18.75 3H5.25A2.25 2.25 0 0 0 3 5.25m18 0H3" />
          </svg>
          <p className="text-white text-lg font-semibold mb-2">Stream stopped</p>
          <p className="text-gray-400 text-sm mb-6">Your stream was stopped because playback started on another device.</p>
          <button
            onClick={() => navigate(-1)}
            className="px-6 py-2.5 bg-white/20 text-white rounded-lg hover:bg-white/30 transition-colors"
          >
            Go Back
          </button>
        </div>
      </div>
    )
  }

  // Show loading while title fetches OR while stream session is being created for VOD
  const waitingForSession = !isLive && !streamSessionReady && !streamError
  if (isLoading || bookmarkLoading || balanceLoading || waitingForSession) {
    return (
      <div className="fixed inset-0 bg-black flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <svg className="w-10 h-10 animate-spin text-primary-500" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <p className="text-gray-400">Loading...</p>
        </div>
      </div>
    )
  }

  if (!manifestUrl) {
    return (
      <div className="fixed inset-0 bg-black flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-400 text-lg mb-4">{isLive ? 'Channel temporarily unavailable' : 'No playback source available'}</p>
          <button
            onClick={() => navigate(-1)}
            className="px-6 py-2.5 bg-white/20 text-white rounded-lg hover:bg-white/30 transition-colors"
          >
            Go Back
          </button>
        </div>
      </div>
    )
  }

  // Lock screen takes priority — block playback entry when daily limit is exceeded
  if (isLocked) {
    return (
      <div className="fixed inset-0 bg-black z-50">
        <LockScreen
          profileId={profile?.id ?? ''}
          nextResetAt={balance?.next_reset_at ?? null}
          onUnlocked={handleUnlocked}
        />
      </div>
    )
  }

  // Show resume prompt before starting playback
  if (showResumePrompt) {
    const pos = existingBookmark.position_seconds
    const dur = existingBookmark.duration_seconds
    const progressPct = dur > 0 ? Math.round((pos / dur) * 100) : 0
    return (
      <div className="fixed inset-0 bg-black z-50 flex items-center justify-center">
        <div className="bg-surface-raised border border-white/10 rounded-xl p-6 max-w-sm w-full mx-4 shadow-2xl">
          <h2 className="text-white text-lg font-semibold mb-2">{displayTitle}</h2>
          <p className="text-gray-400 text-sm mb-4">
            You stopped at {formatTime(pos)} ({progressPct}%)
          </p>
          {/* Progress bar */}
          <div className="h-1.5 bg-white/20 rounded-full mb-6">
            <div
              className="h-full bg-primary-500 rounded-full"
              style={{ width: `${Math.max(progressPct, 2)}%` }}
            />
          </div>
          <div className="flex flex-col gap-3">
            <button
              onClick={handleResume}
              className="w-full px-4 py-3 text-sm font-medium bg-primary-500 text-white rounded-lg hover:bg-primary-400 transition-colors"
            >
              Resume from {formatTime(pos)}
            </button>
            <button
              onClick={handleStartOver}
              className="w-full px-4 py-3 text-sm font-medium bg-white/10 text-gray-300 rounded-lg hover:bg-white/20 hover:text-white transition-colors"
            >
              Start from beginning
            </button>
            <button
              onClick={() => navigate(-1)}
              className="w-full px-4 py-2 text-sm text-gray-500 hover:text-gray-300 transition-colors"
            >
              Go back
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 bg-black z-50">
      <VideoPlayer
        manifestUrl={manifestUrl}
        title={displayTitle}
        isLive={type === 'live'}
        onPositionUpdate={handlePositionUpdate}
        onDurationChange={setVideoDuration}
        onPlayStateChange={setPlayerIsPlaying}
        onEnded={handleEnded}
        onBack={() => navigate(-1)}
        startPosition={startPosition}
      />

      {/* Viewing time warnings (15min / 5min / educational) */}
      <ViewingTimeWarning
        showWarning15={showWarning15}
        showWarning5={showWarning5}
        onDismiss15={dismissWarning15}
        onDismiss5={dismissWarning5}
        remainingMinutes={balance?.remaining_minutes}
        isEducational={isEducational}
      />

      {/* Next episode toast */}
      {nextEpisodeCountdown !== null && nextEpisodeCountdown > 0 && (
        <div className="absolute bottom-20 right-6 z-60 bg-surface-raised border border-white/10 rounded-lg p-4 shadow-2xl">
          <p className="text-sm text-gray-400 mb-2">Next episode in</p>
          <p className="text-2xl font-bold text-white mb-3">{nextEpisodeCountdown}s</p>
          <div className="flex gap-2">
            <button
              onClick={() => navigate(`/play/episode/${nextEpisodeId}`, { replace: true })}
              className="px-4 py-2 text-sm font-medium bg-white text-black rounded hover:bg-white/90 transition-colors"
            >
              Play Now
            </button>
            <button
              onClick={() => setNextEpisodeCountdown(null)}
              className="px-4 py-2 text-sm font-medium text-gray-400 hover:text-white transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
