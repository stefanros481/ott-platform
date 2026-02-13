import { useNavigate } from 'react-router-dom'
import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query'
import { useAuth } from '../context/AuthContext'
import { getPausedBookmarks, restoreBookmark } from '../api/viewing'
import type { ContinueWatchingItem } from '../api/viewing'

export default function PausedPage() {
  const { profile } = useAuth()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data: paused, isLoading } = useQuery({
    queryKey: ['pausedBookmarks', profile?.id],
    queryFn: () => getPausedBookmarks(profile!.id),
    enabled: !!profile,
  })

  const restoreMutation = useMutation({
    mutationFn: (bookmarkId: string) => restoreBookmark(bookmarkId, profile!.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pausedBookmarks'] })
      queryClient.invalidateQueries({ queryKey: ['continueWatching'] })
    },
  })

  return (
    <div className="min-h-screen pt-20 pb-12 px-4 sm:px-6 lg:px-8">
      <h1 className="text-2xl sm:text-3xl font-bold text-white mb-6">Paused</h1>

      {isLoading ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i}>
              <div className="aspect-video rounded-lg bg-surface-overlay animate-pulse" />
              <div className="h-4 w-24 bg-surface-overlay rounded animate-pulse mt-2" />
            </div>
          ))}
        </div>
      ) : !paused?.length ? (
        <div className="flex flex-col items-center justify-center py-20">
          <svg className="w-16 h-16 text-gray-600 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 5.25v13.5m-7.5-13.5v13.5" />
          </svg>
          <p className="text-gray-400 text-lg">No paused items</p>
          <p className="text-gray-500 text-sm mt-1">Items you dismiss from Continue Watching will appear here</p>
          <button
            onClick={() => navigate('/')}
            className="mt-6 px-6 py-2.5 bg-primary-500 text-white font-medium rounded-lg hover:bg-primary-600 transition-colors"
          >
            Back to Home
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
          {paused.map((item: ContinueWatchingItem) => (
            <div key={item.id} className="group relative">
              <button
                onClick={() => navigate(`/play/${item.content_type}/${item.content_id}`)}
                className="w-full text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 rounded-lg"
              >
                <div className="relative aspect-video rounded-lg overflow-hidden bg-surface-overlay">
                  <img
                    src={item.title_info.landscape_url || item.title_info.poster_url || ''}
                    alt={item.title_info.title}
                    className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                    loading="lazy"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />

                  {/* Progress bar */}
                  <div className="absolute bottom-0 left-0 right-0 h-1.5 bg-white/20">
                    <div
                      className="h-full bg-primary-500"
                      style={{ width: `${Math.max(Math.min(item.progress_percent, 100), 2)}%` }}
                    />
                  </div>
                </div>
                <p className="mt-2 text-sm text-gray-300 truncate">{item.title_info.title}</p>
                {item.title_info.season_number != null && (
                  <p className="text-xs text-gray-500">
                    S{item.title_info.season_number}E{item.title_info.episode_number}
                  </p>
                )}
              </button>

              {/* Restore button */}
              <button
                onClick={e => {
                  e.stopPropagation()
                  restoreMutation.mutate(item.id)
                }}
                className="absolute top-2 right-2 px-2 py-1 text-xs font-medium rounded bg-black/70 text-gray-300 hover:text-white opacity-0 group-hover:opacity-100 transition-all"
                title="Restore to Continue Watching"
              >
                Restore
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
