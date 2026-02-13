import { useCallback, useEffect, useMemo, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useAuth } from '../context/AuthContext'
import { getTitleById } from '../api/catalog'
import { getBookmarkByContent } from '../api/viewing'
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
  const { profile } = useAuth()
  const queryClient = useQueryClient()
  const [nextEpisodeCountdown, setNextEpisodeCountdown] = useState<number | null>(null)
  const [videoDuration, setVideoDuration] = useState(0)
  const [playerIsPlaying, setPlayerIsPlaying] = useState(false)
  const [startPosition, setStartPosition] = useState<number | undefined>(undefined)
  const [resumePromptDismissed, setResumePromptDismissed] = useState(false)

  // For movies, id is the title ID. For episodes, we need to find the parent title.
  // In a real app, we would have a dedicated episode endpoint. For this PoC, we fetch the title.
  const { data: title, isLoading } = useQuery({
    queryKey: ['title', id],
    queryFn: () => getTitleById(id!),
    enabled: !!id,
  })

  // Derive playback info from title data without calling setState during render
  const playbackInfo = useMemo(() => {
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
  }, [title, type, id])

  const { manifestUrl, displayTitle, contentType, contentId, nextEpisodeId } = playbackInfo

  // Fetch existing bookmark to offer resume — always fetch fresh, never serve stale cache
  const { data: existingBookmark, isLoading: bookmarkLoading } = useQuery({
    queryKey: ['bookmark', profile?.id, contentId],
    queryFn: () => getBookmarkByContent(profile!.id, contentId),
    enabled: !!profile && !!contentId && contentId !== '',
    gcTime: 0,
    staleTime: 0,
  })

  // Show the resume prompt if there's a non-completed bookmark with meaningful progress
  const showResumePrompt = !resumePromptDismissed
    && existingBookmark
    && !existingBookmark.completed
    && existingBookmark.position_seconds > 10

  // Only use the actual video duration from the player — title metadata may differ from the stream.
  // When videoDuration is 0, the doSave guard in useBookmarkSync skips saves until the player reports it.
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
  // Uses the parent title ID (not episode ID) so the backend can look up is_educational.
  // Stops sending when locked so no more time is counted.
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
    setStartPosition(0)
    setResumePromptDismissed(true)
  }, [])

  // Invalidate continue-watching cache on unmount so home page fetches fresh data.
  // Small delay gives the unmount bookmark save time to reach the server.
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

  if (isLoading || bookmarkLoading || balanceLoading) {
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
          <p className="text-gray-400 text-lg mb-4">No playback source available</p>
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

      {/* Lock screen — shown when daily viewing time is exceeded */}
      {isLocked && (
        <LockScreen
          profileId={profile?.id ?? ''}
          nextResetAt={balance?.next_reset_at ?? null}
          onUnlocked={handleUnlocked}
        />
      )}
    </div>
  )
}
