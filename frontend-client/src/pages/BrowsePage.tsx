import { useState, useEffect } from 'react'
import { useNavigate, useParams, Navigate } from 'react-router-dom'
import { useQuery, useInfiniteQuery } from '@tanstack/react-query'
import { useAuth } from '../context/AuthContext'
import { getGenres, getTitles, type CatalogParams } from '../api/catalog'
import { useAnalytics } from '../hooks/useAnalytics'
import TitleCard from '../components/TitleCard'

type TitleType = 'all' | 'movie' | 'series'

export default function BrowsePage() {
  const { genre: genreParam } = useParams<{ genre?: string }>()
  const navigate = useNavigate()
  const { profile } = useAuth()
  const [selectedGenre, setSelectedGenre] = useState(genreParam || '')
  const [titleType, setTitleType] = useState<TitleType>('all')

  const { trackBrowse } = useAnalytics()

  // Emit a browse event on page load and whenever the filter selection changes
  useEffect(() => {
    trackBrowse('VoD', { genre: selectedGenre || null, title_type: titleType })
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedGenre, titleType])

  const { data: genres } = useQuery({
    queryKey: ['genres'],
    queryFn: getGenres,
  })

  const {
    data,
    isLoading,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useInfiniteQuery({
    queryKey: ['catalog', selectedGenre, titleType, profile?.id],
    queryFn: ({ pageParam }) => {
      const params: CatalogParams = {
        page: pageParam,
        page_size: 24,
        profile_id: profile!.id,
      }
      if (selectedGenre) params.genre = selectedGenre
      if (titleType !== 'all') params.type = titleType
      return getTitles(params)
    },
    initialPageParam: 1,
    getNextPageParam: (lastPage) => {
      const totalPages = Math.ceil(lastPage.total / lastPage.page_size)
      return lastPage.page < totalPages ? lastPage.page + 1 : undefined
    },
    enabled: !!profile,
  })

  const allItems = data?.pages.flatMap(p => p.items) ?? []

  if (!profile) {
    return <Navigate to="/profiles" replace />
  }

  const handleGenreChange = (slug: string) => {
    setSelectedGenre(slug)
    if (slug) {
      navigate(`/browse/${slug}`, { replace: true })
    } else {
      navigate('/browse', { replace: true })
    }
  }

  return (
    <div className="min-h-screen pt-20 pb-12 px-4 sm:px-6 lg:px-8">
      <h1 className="text-2xl sm:text-3xl font-bold text-white mb-6">Browse</h1>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4 mb-8">
        {/* Genre tabs */}
        <div className="flex gap-2 overflow-x-auto pb-2" style={{ scrollbarWidth: 'none' }}>
          <button
            onClick={() => handleGenreChange('')}
            className={`px-4 py-2 text-sm font-medium rounded-full whitespace-nowrap transition-colors ${
              !selectedGenre
                ? 'bg-primary-500 text-white'
                : 'bg-surface-overlay text-gray-400 hover:text-white hover:bg-white/10'
            }`}
          >
            All Genres
          </button>
          {genres?.map(g => (
            <button
              key={g.id}
              onClick={() => handleGenreChange(g.slug)}
              className={`px-4 py-2 text-sm font-medium rounded-full whitespace-nowrap transition-colors ${
                selectedGenre === g.slug
                  ? 'bg-primary-500 text-white'
                  : 'bg-surface-overlay text-gray-400 hover:text-white hover:bg-white/10'
              }`}
            >
              {g.name}
            </button>
          ))}
        </div>

        {/* Type filter */}
        <div className="flex gap-2 shrink-0">
          {(['all', 'movie', 'series'] as TitleType[]).map(type => (
            <button
              key={type}
              onClick={() => setTitleType(type)}
              className={`px-4 py-2 text-sm font-medium rounded-full whitespace-nowrap transition-colors ${
                titleType === type
                  ? 'bg-white/20 text-white'
                  : 'bg-surface-overlay text-gray-400 hover:text-white hover:bg-white/10'
              }`}
            >
              {type === 'all' ? 'All' : type === 'movie' ? 'Movies' : 'Series'}
            </button>
          ))}
        </div>
      </div>

      {/* Results Grid */}
      {isLoading ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
          {Array.from({ length: 18 }).map((_, i) => (
            <div key={i}>
              <div className="aspect-[2/3] rounded-lg bg-surface-overlay animate-pulse" />
              <div className="h-4 w-24 bg-surface-overlay rounded animate-pulse mt-2" />
            </div>
          ))}
        </div>
      ) : allItems.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20">
          <svg className="w-16 h-16 text-gray-600 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
            <path strokeLinecap="round" strokeLinejoin="round" d="m15.75 10.5 4.72-4.72a.75.75 0 0 1 1.28.53v11.38a.75.75 0 0 1-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 0 0 2.25-2.25v-9a2.25 2.25 0 0 0-2.25-2.25h-9A2.25 2.25 0 0 0 2.25 7.5v9a2.25 2.25 0 0 0 2.25 2.25Z" />
          </svg>
          <p className="text-gray-400 text-lg">No titles found</p>
          <p className="text-gray-500 text-sm mt-1">Try a different genre or filter</p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
            {allItems.map(item => (
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
          </div>

          {/* Load more */}
          {hasNextPage && (
            <div className="flex justify-center mt-10">
              <button
                onClick={() => fetchNextPage()}
                disabled={isFetchingNextPage}
                className="px-8 py-3 text-sm font-medium text-white bg-surface-overlay hover:bg-white/10 rounded-lg transition-colors disabled:opacity-50"
              >
                {isFetchingNextPage ? 'Loading...' : 'Load More'}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
