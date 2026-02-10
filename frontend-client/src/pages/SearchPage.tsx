import { useState, useEffect, useRef } from 'react'
import { useNavigate, Navigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useAuth } from '../context/AuthContext'
import { getTitles, semanticSearch } from '../api/catalog'
import type { SearchResultItem } from '../api/catalog'
import TitleCard from '../components/TitleCard'

export default function SearchPage() {
  const [query, setQuery] = useState('')
  const [debouncedQuery, setDebouncedQuery] = useState('')
  const [mode, setMode] = useState<'hybrid' | 'keyword'>('hybrid')
  const navigate = useNavigate()
  const { profile } = useAuth()
  const inputRef = useRef<HTMLInputElement>(null)

  // Autofocus
  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  // Debounce
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(query.trim())
    }, 300)
    return () => clearTimeout(timer)
  }, [query])

  // T009: Primary semantic search query
  const {
    data: semanticData,
    isLoading: semanticLoading,
    isError: semanticError,
  } = useQuery({
    queryKey: ['semantic-search', debouncedQuery, mode, profile?.id],
    queryFn: () =>
      semanticSearch({
        q: debouncedQuery,
        mode,
        page_size: 30,
        profile_id: profile!.id,
      }),
    enabled: debouncedQuery.length >= 2 && !!profile,
  })

  // T015: Fallback to keyword search when semantic endpoint errors
  const { data: fallbackData } = useQuery({
    queryKey: ['search-fallback', debouncedQuery, profile?.id],
    queryFn: () =>
      getTitles({ q: debouncedQuery, page_size: 30, profile_id: profile!.id }),
    enabled: semanticError && debouncedQuery.length >= 2 && !!profile,
  })

  // Determine which results to use
  const usingFallback = semanticError && !!fallbackData
  const results: SearchResultItem[] = usingFallback
    ? (fallbackData?.items ?? []).map((item) => ({
        ...item,
        match_reason: 'Keyword match',
        match_type: 'keyword' as const,
        similarity_score: null,
      }))
    : (semanticData?.items ?? [])
  const total = usingFallback ? fallbackData?.total ?? 0 : semanticData?.total ?? 0
  const isLoading = semanticLoading

  // T016: Hide AI badge when fallback is active or keyword mode
  const showAiBadge = mode !== 'keyword' && !usingFallback

  if (!profile) {
    return <Navigate to="/profiles" replace />
  }

  return (
    <div className="min-h-screen pt-14 pb-12 px-4 sm:px-6 lg:px-8">
      {/* Search input */}
      <div className="max-w-2xl mx-auto pt-8 mb-8">
        <div className="relative">
          <svg className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
          </svg>
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Try: dark comedy about office life, 90s thriller..."
            className="w-full pl-12 pr-4 py-4 text-lg bg-surface-raised border border-white/10 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
          />
          {query && (
            <button
              onClick={() => setQuery('')}
              className="absolute right-4 top-1/2 -translate-y-1/2 p-1 text-gray-500 hover:text-white transition-colors"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>

        {/* T013: Mode toggle */}
        <div className="flex gap-2 mt-3">
          <button
            onClick={() => setMode('hybrid')}
            className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              mode === 'hybrid'
                ? 'bg-primary-500 text-white'
                : 'bg-surface-overlay text-gray-400 hover:text-white'
            }`}
          >
            Smart Search
          </button>
          <button
            onClick={() => setMode('keyword')}
            className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              mode === 'keyword'
                ? 'bg-primary-500 text-white'
                : 'bg-surface-overlay text-gray-400 hover:text-white'
            }`}
          >
            Keyword
          </button>
        </div>
      </div>

      {/* Results */}
      {debouncedQuery.length < 2 ? (
        <div className="flex flex-col items-center justify-center py-20">
          <svg className="w-16 h-16 text-gray-600 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
            <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
          </svg>
          <p className="text-gray-400 text-lg">Type to search</p>
          <p className="text-gray-500 text-sm mt-1">Describe what you're in the mood for</p>
        </div>
      ) : isLoading ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
          {Array.from({ length: 12 }).map((_, i) => (
            <div key={i}>
              <div className="aspect-[2/3] rounded-lg bg-surface-overlay animate-pulse" />
              <div className="h-4 w-24 bg-surface-overlay rounded animate-pulse mt-2" />
            </div>
          ))}
        </div>
      ) : results.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20">
          <svg className="w-16 h-16 text-gray-600 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15.182 16.318A4.486 4.486 0 0 0 12.016 15a4.486 4.486 0 0 0-3.198 1.318M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0ZM9.75 9.75c0 .414-.168.75-.375.75S9 10.164 9 9.75 9.168 9 9.375 9s.375.336.375.75Zm-.375 0h.008v.015h-.008V9.75Zm5.625 0c0 .414-.168.75-.375.75s-.375-.336-.375-.75.168-.75.375-.75.375.336.375.75Zm-.375 0h.008v.015h-.008V9.75Z" />
          </svg>
          <p className="text-gray-400 text-lg">No results found</p>
          <p className="text-gray-500 text-sm mt-1">Try describing what you're looking for, like "funny workplace comedy"</p>
        </div>
      ) : (
        <div>
          <div className="flex items-center gap-2 mb-4">
            <p className="text-sm text-gray-500">{total} result{total !== 1 ? 's' : ''}</p>
            {/* T014: AI sparkle badge */}
            {showAiBadge && (
              <span className="text-xs text-primary-400 bg-primary-500/10 px-2 py-0.5 rounded-full inline-flex items-center gap-1">
                <svg className="w-3 h-3" viewBox="0 0 16 16" fill="currentColor">
                  <path d="M8 0l1.5 5.5L15 8l-5.5 1.5L8 15l-1.5-5.5L1 8l5.5-1.5z" />
                </svg>
                AI
              </span>
            )}
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
            {results.map(item => (
              <div
                key={item.id}
                className={`${
                  item.match_type === 'both'
                    ? 'border-l-2 border-primary-500'
                    : item.match_type === 'semantic'
                      ? 'border-l-2 border-teal-500'
                      : ''
                }`}
              >
                <TitleCard
                  title={item.title}
                  posterUrl={item.poster_url}
                  landscapeUrl={item.landscape_url}
                  titleType={item.title_type}
                  releaseYear={item.release_year}
                  ageRating={item.age_rating}
                  onClick={() => navigate(`/title/${item.id}`)}
                />
                {/* T010: Match reason */}
                <p className="text-xs text-gray-500 truncate mt-1 px-0.5">{item.match_reason}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
