import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuth } from '../context/AuthContext'
import { getTitleById } from '../api/catalog'
import { getSimilarTitles } from '../api/recommendations'
import { rateTitle, getRating, addToWatchlist, removeFromWatchlist, getWatchlist } from '../api/viewing'
import ContentRail from '../components/ContentRail'
import TitleCard from '../components/TitleCard'

export default function TitleDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { profile } = useAuth()
  const queryClient = useQueryClient()
  const [selectedSeason, setSelectedSeason] = useState(1)

  const { data: title, isLoading, error: titleError } = useQuery({
    queryKey: ['title', id, profile?.id],
    queryFn: () => getTitleById(id!, profile?.id),
    enabled: !!id,
    retry: (failureCount, error: any) => {
      if (error?.status === 403) return false
      return failureCount < 3
    },
  })

  const { data: similar } = useQuery({
    queryKey: ['similar', id, profile?.id],
    queryFn: () => getSimilarTitles(id!, profile?.id),
    enabled: !!id,
  })

  const { data: watchlist } = useQuery({
    queryKey: ['watchlist', profile?.id],
    queryFn: () => getWatchlist(profile!.id),
    enabled: !!profile,
  })

  const { data: ratingData } = useQuery({
    queryKey: ['rating', profile?.id, id],
    queryFn: () => getRating(profile!.id, id!),
    enabled: !!profile && !!id,
  })

  const userRating = ratingData?.rating ?? null

  const isInWatchlist = watchlist?.some(w => w.title_id === id)

  const watchlistMutation = useMutation({
    mutationFn: () => isInWatchlist
      ? removeFromWatchlist(profile!.id, id!)
      : addToWatchlist(profile!.id, id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['watchlist'] })
    },
  })

  const rateMutation = useMutation({
    mutationFn: (rating: 1 | -1) => rateTitle(profile!.id, { title_id: id!, rating }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rating', profile?.id, id] })
    },
  })

  const isRestricted = (titleError as any)?.status === 403

  if (isRestricted) {
    return (
      <div className="min-h-screen pt-14 flex flex-col items-center justify-center px-4">
        <svg className="w-20 h-20 text-gray-600 mb-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 1 0-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 0 0 2.25-2.25v-6.75a2.25 2.25 0 0 0-2.25-2.25H6.75a2.25 2.25 0 0 0-2.25 2.25v6.75a2.25 2.25 0 0 0 2.25 2.25Z" />
        </svg>
        <h2 className="text-xl font-semibold text-white mb-2">Content not available for this profile</h2>
        <p className="text-gray-400 text-sm mb-6">This title is restricted based on the current profile's parental rating.</p>
        <button
          onClick={() => navigate(-1)}
          className="px-6 py-2.5 bg-surface-overlay text-white rounded-lg hover:bg-white/10 transition-colors"
        >
          Go Back
        </button>
      </div>
    )
  }

  if (isLoading || !title) {
    return (
      <div className="min-h-screen pt-14">
        {/* Hero skeleton */}
        <div className="relative w-full h-[50vh] bg-surface-raised animate-pulse" />
        <div className="max-w-screen-xl mx-auto px-4 sm:px-6 lg:px-8 -mt-20 relative z-10 space-y-4">
          <div className="h-10 w-80 bg-surface-overlay rounded animate-pulse" />
          <div className="h-5 w-60 bg-surface-overlay rounded animate-pulse" />
          <div className="h-20 w-full max-w-2xl bg-surface-overlay rounded animate-pulse" />
        </div>
      </div>
    )
  }

  const currentSeason = title.seasons.find(s => s.season_number === selectedSeason)

  const handlePlay = () => {
    if (title.title_type === 'movie') {
      navigate(`/play/movie/${title.id}`)
    } else if (currentSeason?.episodes.length) {
      const firstEpisode = currentSeason.episodes[0]
      if (firstEpisode) {
        navigate(`/play/episode/${firstEpisode.id}`)
      }
    }
  }

  return (
    <div className="min-h-screen pt-14 pb-12">
      {/* Hero Section */}
      <div className="relative w-full h-[50vh] sm:h-[60vh] overflow-hidden">
        <img
          src={title.landscape_url || title.poster_url}
          alt={title.title}
          className="w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-surface via-surface/60 to-surface/20" />
        <div className="absolute inset-0 bg-gradient-to-r from-surface/80 via-transparent to-transparent" />
      </div>

      {/* Content */}
      <div className="max-w-screen-xl mx-auto px-4 sm:px-6 lg:px-8 -mt-32 relative z-10">
        {/* Title + Meta */}
        <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-white mb-3">{title.title}</h1>
        <div className="flex flex-wrap items-center gap-3 text-sm text-gray-400 mb-4">
          <span>{title.release_year}</span>
          {title.duration_minutes && (
            <>
              <span className="text-gray-600">|</span>
              <span>{Math.floor(title.duration_minutes / 60)}h {title.duration_minutes % 60}m</span>
            </>
          )}
          <span className="text-gray-600">|</span>
          <span className="px-2 py-0.5 border border-gray-600 rounded text-xs">{title.age_rating}</span>
          {title.genres.map(g => (
            <span key={g} className="px-2 py-0.5 bg-surface-overlay rounded-full text-xs">{g}</span>
          ))}
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-3 mb-6">
          <button
            onClick={handlePlay}
            className="flex items-center gap-2 px-8 py-3 bg-white text-black font-semibold rounded-md hover:bg-white/90 transition-colors"
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M8 5v14l11-7z" />
            </svg>
            Play
          </button>

          <button
            onClick={() => watchlistMutation.mutate()}
            disabled={watchlistMutation.isPending}
            className={`flex items-center gap-2 px-5 py-3 font-medium rounded-md transition-colors ${
              isInWatchlist
                ? 'bg-primary-500/20 text-primary-400 border border-primary-500/50 hover:bg-primary-500/30'
                : 'bg-white/10 text-white hover:bg-white/20'
            }`}
          >
            {isInWatchlist ? (
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" />
              </svg>
            ) : (
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
              </svg>
            )}
            {isInWatchlist ? 'In My List' : 'My List'}
          </button>

          {/* Rate buttons */}
          <button
            onClick={() => rateMutation.mutate(1)}
            className={`p-3 rounded-full transition-colors ${
              userRating === 1
                ? 'bg-green-500/20 text-green-400'
                : 'bg-white/10 text-gray-400 hover:bg-white/20 hover:text-white'
            }`}
            title="I liked this"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6.633 10.25c.806 0 1.533-.446 2.031-1.08a9.041 9.041 0 0 1 2.861-2.4c.723-.384 1.35-.956 1.653-1.715a4.498 4.498 0 0 0 .322-1.672V3a.75.75 0 0 1 .75-.75 2.25 2.25 0 0 1 2.25 2.25c0 1.152-.26 2.243-.723 3.218-.266.558.107 1.282.725 1.282m0 0h3.126c1.026 0 1.945.694 2.054 1.715.045.422.068.85.068 1.285a11.95 11.95 0 0 1-2.649 7.521c-.388.482-.987.729-1.605.729H13.48c-.483 0-.964-.078-1.423-.23l-3.114-1.04a4.501 4.501 0 0 0-1.423-.23H5.904m10.598-9.75H14.25M5.904 18.5c.083.205.173.405.27.602.197.4-.078.898-.523.898h-.908c-.889 0-1.713-.518-1.972-1.368a12 12 0 0 1-.521-3.507c0-1.553.295-3.036.831-4.398C3.387 9.953 4.167 9.5 5 9.5h1.053c.472 0 .745.556.5.96a8.958 8.958 0 0 0-1.302 4.665c0 1.194.232 2.333.654 3.375Z" />
            </svg>
          </button>

          <button
            onClick={() => rateMutation.mutate(-1)}
            className={`p-3 rounded-full transition-colors ${
              userRating === -1
                ? 'bg-red-500/20 text-red-400'
                : 'bg-white/10 text-gray-400 hover:bg-white/20 hover:text-white'
            }`}
            title="Not for me"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M7.498 15.25H4.372c-1.026 0-1.945-.694-2.054-1.715a12.137 12.137 0 0 1-.068-1.285c0-2.848.992-5.464 2.649-7.521C5.287 4.247 5.886 4 6.504 4h4.016a4.5 4.5 0 0 1 1.423.23l3.114 1.04a4.5 4.5 0 0 0 1.423.23h1.294M7.498 15.25c.618 0 .991.724.725 1.282A7.471 7.471 0 0 0 7.5 19.75 2.25 2.25 0 0 0 9.75 22a.75.75 0 0 0 .75-.75v-.633c0-.573.11-1.14.322-1.672.304-.76.93-1.33 1.653-1.715a9.04 9.04 0 0 0 2.86-2.4c.498-.634 1.226-1.08 2.032-1.08h.384m-10.253 1.5H9.7m8.075-9.75c.01.05.027.1.05.148.593 1.2.925 2.55.925 3.977 0 1.31-.269 2.559-.754 3.695-.292.683.033 1.555.794 1.555h1.341c.816 0 1.6-.28 1.973-1.068a12.122 12.122 0 0 0 1.046-4.182c0-.169-.002-.337-.006-.505" />
            </svg>
          </button>
        </div>

        {/* Synopsis */}
        <p className="text-gray-300 text-base leading-relaxed max-w-3xl mb-8">
          {title.synopsis_long || title.synopsis_short}
        </p>

        {/* Cast */}
        {title.cast.length > 0 && (
          <div className="mb-10">
            <h3 className="text-lg font-semibold text-white mb-3">Cast</h3>
            <div className="flex flex-wrap gap-4">
              {title.cast.map((member, i) => (
                <div key={i} className="flex items-center gap-3 bg-surface-raised rounded-lg p-3 pr-5">
                  <div className="w-10 h-10 rounded-full bg-surface-overlay flex items-center justify-center text-sm font-bold text-gray-400">
                    {member.person_name.charAt(0)}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-white">{member.person_name}</p>
                    <p className="text-xs text-gray-500">{member.character_name || member.role}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Seasons & Episodes (for series) */}
        {title.title_type === 'series' && title.seasons.length > 0 && (
          <div className="mb-10">
            {/* Season tabs */}
            <div className="flex items-center gap-3 mb-4 overflow-x-auto" style={{ scrollbarWidth: 'none' }}>
              {title.seasons.map(s => (
                <button
                  key={s.season_number}
                  onClick={() => setSelectedSeason(s.season_number)}
                  className={`px-4 py-2 text-sm font-medium rounded-full whitespace-nowrap transition-colors ${
                    selectedSeason === s.season_number
                      ? 'bg-primary-500 text-white'
                      : 'bg-surface-overlay text-gray-400 hover:text-white hover:bg-white/10'
                  }`}
                >
                  Season {s.season_number}
                </button>
              ))}
            </div>

            {/* Episode list */}
            <div className="space-y-2">
              {currentSeason?.episodes.map(ep => (
                <button
                  key={ep.id}
                  onClick={() => navigate(`/play/episode/${ep.id}`)}
                  className="w-full flex items-center gap-4 p-3 rounded-lg bg-surface-raised hover:bg-surface-overlay transition-colors text-left group"
                >
                  {/* Thumbnail */}
                  <div className="relative w-32 sm:w-40 aspect-video rounded overflow-hidden bg-surface-overlay shrink-0">
                    <div className="w-full h-full flex items-center justify-center">
                      <svg className="w-8 h-8 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="m15.75 10.5 4.72-4.72a.75.75 0 0 1 1.28.53v11.38a.75.75 0 0 1-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 0 0 2.25-2.25v-9a2.25 2.25 0 0 0-2.25-2.25h-9A2.25 2.25 0 0 0 2.25 7.5v9a2.25 2.25 0 0 0 2.25 2.25Z" />
                      </svg>
                    </div>
                    {/* Play icon overlay */}
                    <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity bg-black/40">
                      <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M8 5v14l11-7z" />
                      </svg>
                    </div>
                  </div>

                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-bold text-gray-500">{ep.episode_number}</span>
                      <h4 className="text-sm font-medium text-white truncate">{ep.title}</h4>
                    </div>
                    <p className="text-xs text-gray-400 mt-0.5">{ep.duration_minutes} min</p>
                    <p className="text-xs text-gray-500 mt-1 line-clamp-2">{ep.synopsis}</p>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* More Like This */}
        {similar && similar.length > 0 && (
          <ContentRail title="More Like This">
            {similar.map(item => (
              <TitleCard
                key={item.id}
                title={item.title}
                posterUrl={item.poster_url}
                landscapeUrl={item.landscape_url}
                titleType={item.title_type}
                releaseYear={item.release_year}
                ageRating={item.age_rating}
                onClick={() => navigate(`/title/${item.id}`)}
              />
            ))}
          </ContentRail>
        )}
      </div>
    </div>
  )
}
