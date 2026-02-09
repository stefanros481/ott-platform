import { apiFetch } from './client'

export interface TitleListItem {
  id: string
  title: string
  synopsis_short: string | null
  poster_url: string
  landscape_url: string | null
  title_type: 'movie' | 'series'
  release_year: number
  age_rating: string
  genres: string[]
  duration_minutes: number | null
  is_featured: boolean
  mood_tags: string[] | null
}

export interface PaginatedTitles {
  items: TitleListItem[]
  total: number
  page: number
  page_size: number
}

export interface Genre {
  id: string
  name: string
  slug: string
}

export interface CastMember {
  person_name: string
  role: string
  character_name: string | null
}

export interface Episode {
  id: string
  title: string
  episode_number: number
  synopsis: string | null
  duration_minutes: number | null
  hls_manifest_url: string | null
}

export interface Season {
  season_number: number
  episodes: Episode[]
}

export interface TitleDetail {
  id: string
  title: string
  synopsis_short: string | null
  synopsis_long: string | null
  poster_url: string
  landscape_url: string | null
  title_type: 'movie' | 'series'
  release_year: number
  age_rating: string
  genres: string[]
  duration_minutes: number | null
  cast: CastMember[]
  seasons: Season[]
  hls_manifest_url: string | null
  mood_tags: string[] | null
  theme_tags: string[] | null
  ai_description: string | null
}

export interface CatalogParams {
  page?: number
  page_size?: number
  genre?: string
  type?: string
  q?: string
}

export function getTitles(params: CatalogParams = {}): Promise<PaginatedTitles> {
  const searchParams = new URLSearchParams()
  if (params.page) searchParams.set('page', String(params.page))
  if (params.page_size) searchParams.set('page_size', String(params.page_size))
  if (params.genre) searchParams.set('genre', params.genre)
  if (params.type) searchParams.set('type', params.type)
  if (params.q) searchParams.set('q', params.q)

  const qs = searchParams.toString()
  return apiFetch<PaginatedTitles>(`/catalog/titles${qs ? `?${qs}` : ''}`)
}

export function getTitleById(id: string): Promise<TitleDetail> {
  return apiFetch<TitleDetail>(`/catalog/titles/${id}`)
}

export function getGenres(): Promise<Genre[]> {
  return apiFetch<Genre[]>('/catalog/genres')
}

export function getFeatured(): Promise<TitleListItem[]> {
  return apiFetch<TitleListItem[]>('/catalog/featured')
}
