import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuth } from '../context/AuthContext'
import { getWatchlist, removeFromWatchlist } from '../api/viewing'

export default function WatchlistPage() {
  const { profile } = useAuth()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data: watchlist, isLoading } = useQuery({
    queryKey: ['watchlist', profile?.id],
    queryFn: () => getWatchlist(profile!.id),
    enabled: !!profile,
  })

  const removeMutation = useMutation({
    mutationFn: (titleId: string) => removeFromWatchlist(profile!.id, titleId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['watchlist'] })
    },
  })

  return (
    <div className="min-h-screen pt-20 pb-12 px-4 sm:px-6 lg:px-8">
      <h1 className="text-2xl sm:text-3xl font-bold text-white mb-6">My List</h1>

      {isLoading ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i}>
              <div className="aspect-[2/3] rounded-lg bg-surface-overlay animate-pulse" />
              <div className="h-4 w-24 bg-surface-overlay rounded animate-pulse mt-2" />
            </div>
          ))}
        </div>
      ) : !watchlist?.length ? (
        <div className="flex flex-col items-center justify-center py-20">
          <svg className="w-16 h-16 text-gray-600 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M17.593 3.322c1.1.128 1.907 1.077 1.907 2.185V21L12 17.25 4.5 21V5.507c0-1.108.806-2.057 1.907-2.185a48.507 48.507 0 0 1 11.186 0Z" />
          </svg>
          <p className="text-gray-400 text-lg">Your list is empty</p>
          <p className="text-gray-500 text-sm mt-1">Add movies and series to your list to find them here</p>
          <button
            onClick={() => navigate('/browse')}
            className="mt-6 px-6 py-2.5 bg-primary-500 text-white font-medium rounded-lg hover:bg-primary-600 transition-colors"
          >
            Browse Catalog
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
          {watchlist.map(item => (
            <div key={item.title_id} className="group relative">
              {/* Card */}
              <button
                onClick={() => navigate(`/title/${item.title_id}`)}
                className="w-full text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 rounded-lg"
              >
                <div className="relative aspect-[2/3] rounded-lg overflow-hidden bg-surface-overlay">
                  <img
                    src={item.title_info.poster_url}
                    alt={item.title_info.title}
                    className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                    loading="lazy"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />

                  {/* Type badge */}
                  <span className="absolute top-2 right-2 px-1.5 py-0.5 text-[10px] font-medium uppercase bg-black/60 text-gray-300 rounded">
                    {item.title_info.title_type === 'series' ? 'Series' : 'Movie'}
                  </span>

                  {/* Bottom info on hover */}
                  <div className="absolute bottom-0 left-0 right-0 p-3 opacity-0 group-hover:opacity-100 transition-opacity">
                    <p className="text-sm font-semibold text-white leading-tight">{item.title_info.title}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-xs text-gray-400">{item.title_info.release_year}</span>
                      <span className="text-xs text-gray-500">|</span>
                      <span className="text-xs text-gray-400">{item.title_info.age_rating}</span>
                    </div>
                  </div>
                </div>
                <p className="mt-2 text-sm text-gray-300 truncate">{item.title_info.title}</p>
              </button>

              {/* Remove button */}
              <button
                onClick={e => {
                  e.stopPropagation()
                  removeMutation.mutate(item.title_id)
                }}
                className="absolute top-2 left-2 p-1.5 rounded-full bg-black/60 text-gray-400 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-all"
                title="Remove from My List"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
