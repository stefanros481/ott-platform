import { useCallback, useEffect, useMemo, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useAuth } from '../context/AuthContext'
import { getTitleById } from '../api/catalog'
import { useBookmarkSync } from '../hooks/useBookmarkSync'
import VideoPlayer from '../components/VideoPlayer'

export default function PlayerPage() {
  const { type, id } = useParams<{ type: string; id: string }>()
  const navigate = useNavigate()
  const { profile } = useAuth()
  const [nextEpisodeCountdown, setNextEpisodeCountdown] = useState<number | null>(null)

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

  const durationSeconds = title?.duration_minutes ? title.duration_minutes * 60 : 0

  const { saveNow } = useBookmarkSync({
    profileId: profile?.id ?? '',
    contentType,
    contentId,
    durationSeconds,
    isPlaying: true,
  })

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

  if (isLoading) {
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

  return (
    <div className="fixed inset-0 bg-black z-50">
      <VideoPlayer
        manifestUrl={manifestUrl}
        title={displayTitle}
        isLive={type === 'live'}
        onPositionUpdate={handlePositionUpdate}
        onEnded={handleEnded}
        onBack={() => navigate(-1)}
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
