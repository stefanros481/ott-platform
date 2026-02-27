import { useMemo } from 'react'
import { useNavigate, Navigate } from 'react-router-dom'
import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query'
import { useAuth } from '../context/AuthContext'
import { getFeatured } from '../api/catalog'
import { getHomeRecommendations } from '../api/recommendations'
import { getContinueWatching, getPausedBookmarks, dismissBookmark } from '../api/viewing'
import { listCatchUpByDate } from '../api/tstv'
import HeroBanner from '../components/HeroBanner'
import ContentRail from '../components/ContentRail'
import TitleCard from '../components/TitleCard'
import ContinueWatchingCard from '../components/ContinueWatchingCard'
import CatchUpRail from '../components/CatchUpRail'

function detectDeviceType(): string {
  const ua = navigator.userAgent
  if (/Mobile/i.test(ua)) return 'mobile'
  if (/Tablet/i.test(ua)) return 'tablet'
  return 'web'
}

export default function HomePage() {
  const { profile } = useAuth()
  const navigate = useNavigate()
  const deviceType = useMemo(() => detectDeviceType(), [])
  const hourOfDay = useMemo(() => new Date().getHours(), [])

  const { data: featured, isLoading: featuredLoading } = useQuery({
    queryKey: ['featured', profile?.id],
    queryFn: () => getFeatured(profile!.id),
    enabled: !!profile,
  })

  const { data: recommendations, isLoading: recsLoading } = useQuery({
    queryKey: ['recommendations', 'home', profile?.id],
    queryFn: () => getHomeRecommendations(profile!.id),
    enabled: !!profile,
  })

  const queryClient = useQueryClient()

  const { data: continueWatching } = useQuery({
    queryKey: ['continueWatching', profile?.id, deviceType, hourOfDay],
    queryFn: () => getContinueWatching(profile!.id, deviceType, hourOfDay),
    enabled: !!profile,
  })

  const { data: pausedBookmarks } = useQuery({
    queryKey: ['pausedBookmarks', profile?.id],
    queryFn: () => getPausedBookmarks(profile!.id),
    enabled: !!profile,
  })

  // Catch-Up Continue Watching — programs with saved bookmarks
  const { data: catchupContinue } = useQuery({
    queryKey: ['catchupContinue', profile?.id],
    queryFn: async () => {
      const result = await listCatchUpByDate(undefined, undefined, undefined, 50, 0, profile!.id)
      return result.programs.filter(p => p.bookmark_position_seconds != null && p.bookmark_position_seconds > 0)
    },
    enabled: !!profile,
  })

  const dismissMutation = useMutation({
    mutationFn: (bookmarkId: string) => dismissBookmark(bookmarkId, profile!.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['continueWatching'] })
      queryClient.invalidateQueries({ queryKey: ['pausedBookmarks'] })
    },
  })

  if (!profile) {
    return <Navigate to="/profiles" replace />
  }

  const heroItems = (featured || []).slice(0, 5).map(t => ({
    id: t.id,
    title: t.title,
    synopsis: t.synopsis_short || '',
    landscapeUrl: t.landscape_url,
    posterUrl: t.poster_url,
  }))

  const isRecent = (dateStr: string) => {
    const created = new Date(dateStr)
    const daysAgo = (Date.now() - created.getTime()) / (1000 * 60 * 60 * 24)
    return daysAgo <= 30
  }

  return (
    <div className="pb-12">
      {/* Hero Banner */}
      {featuredLoading ? (
        <div className="w-full h-[50vh] sm:h-[60vh] lg:h-[70vh] bg-surface-raised animate-pulse" />
      ) : (
        <HeroBanner
          items={heroItems}
          onPlay={id => navigate(`/play/movie/${id}`)}
          onMoreInfo={id => navigate(`/title/${id}`)}
        />
      )}

      {/* Content Rails */}
      <div className="mt-8 space-y-10">
        {/* Continue Watching Rail */}
        {(continueWatching && continueWatching.length > 0 || (pausedBookmarks && pausedBookmarks.length > 0)) && (
          <div>
            {continueWatching && continueWatching.length > 0 && (
              <ContentRail title="Continue Watching">
                {continueWatching.map(item => (
                  <ContinueWatchingCard
                    key={item.id}
                    item={item}
                    onResume={(contentType, contentId) =>
                      navigate(`/play/${contentType}/${contentId}`)
                    }
                    onDismiss={bookmarkId => dismissMutation.mutate(bookmarkId)}
                  />
                ))}
              </ContentRail>
            )}
            {pausedBookmarks && pausedBookmarks.length > 0 && (
              <div className="px-4 sm:px-6 lg:px-8 mt-2">
                <button
                  onClick={() => navigate('/paused')}
                  className="text-sm text-gray-500 hover:text-gray-300 transition-colors"
                >
                  Paused ({pausedBookmarks.length})
                </button>
              </div>
            )}
          </div>
        )}

        {/* Catch-Up Continue Watching Rail */}
        {catchupContinue && catchupContinue.length > 0 && (
          <ContentRail title="Continue Watching — Catch-Up TV">
            <CatchUpRail programs={catchupContinue} />
          </ContentRail>
        )}

        {recsLoading ? (
          // Loading skeletons
          Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="px-4 sm:px-6 lg:px-8">
              <div className="h-6 w-48 bg-surface-overlay rounded animate-pulse mb-4" />
              <div className="flex gap-3 overflow-hidden">
                {Array.from({ length: 6 }).map((_, j) => (
                  <div key={j} className="flex-shrink-0 w-[160px] sm:w-[180px] md:w-[200px]">
                    <div className="aspect-[2/3] rounded-lg bg-surface-overlay animate-pulse" />
                    <div className="h-4 w-24 bg-surface-overlay rounded animate-pulse mt-2" />
                  </div>
                ))}
              </div>
            </div>
          ))
        ) : (
          recommendations?.rails.filter(rail => rail.name !== 'Continue Watching').map(rail => (
            <ContentRail key={rail.name} title={rail.name}>
              {rail.items.map(item => (
                <TitleCard
                  key={item.id}
                  title={item.title}
                  posterUrl={item.poster_url}
                  landscapeUrl={item.landscape_url}
                  titleType={item.title_type}
                  releaseYear={item.release_year}
                  ageRating={item.age_rating}
                  onClick={() => navigate(`/title/${item.id}`)}
                  isNew={isRecent(String(item.release_year))}
                />
              ))}
            </ContentRail>
          ))
        )}
      </div>
    </div>
  )
}
