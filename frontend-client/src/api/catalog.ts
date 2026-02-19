import { apiFetch } from './client'

export interface AccessOption {
  type: 'svod' | 'rent' | 'buy' | 'free'
  label: string
  price_cents: number | null
  currency: string | null
  rental_window_hours: number | null
}

export interface UserAccess {
  has_access: boolean
  access_type: 'svod' | 'tvod_rent' | 'tvod_buy' | 'free' | null
  expires_at: string | null
  required_tier: 'basic' | 'standard' | 'premium' | null
}

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
  access_options: AccessOption[]
  user_access: UserAccess | null
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
  access_options: AccessOption[]
  user_access: UserAccess | null
}

export interface CatalogParams {
  page?: number
  page_size?: number
  genre?: string
  type?: string
  q?: string
  profile_id?: string
}

export function getTitles(params: CatalogParams = {}): Promise<PaginatedTitles> {
  const searchParams = new URLSearchParams()
  if (params.page) searchParams.set('page', String(params.page))
  if (params.page_size) searchParams.set('page_size', String(params.page_size))
  if (params.genre) searchParams.set('genre', params.genre)
  if (params.type) searchParams.set('type', params.type)
  if (params.q) searchParams.set('q', params.q)
  if (params.profile_id) searchParams.set('profile_id', params.profile_id)

  const qs = searchParams.toString()
  return apiFetch<PaginatedTitles>(`/catalog/titles${qs ? `?${qs}` : ''}`)
}

export function getTitleById(id: string, profileId?: string): Promise<TitleDetail> {
  const qs = profileId ? `?profile_id=${profileId}` : ''
  return apiFetch<TitleDetail>(`/catalog/titles/${id}${qs}`)
}

export function getGenres(): Promise<Genre[]> {
  return apiFetch<Genre[]>('/catalog/genres')
}

export function getFeatured(profileId?: string): Promise<TitleListItem[]> {
  const qs = profileId ? `?profile_id=${profileId}` : ''
  return apiFetch<TitleListItem[]>(`/catalog/featured${qs}`)
}

// ── Semantic search ─────────────────────────────────────────────────────────

export interface SearchResultItem extends TitleListItem {
  match_reason: string
  match_type: 'keyword' | 'semantic' | 'both'
  similarity_score: number | null
}

export interface SemanticSearchResponse {
  items: SearchResultItem[]
  total: number
  query: string
  mode: string
}

export interface SemanticSearchParams {
  q: string
  mode?: 'keyword' | 'semantic' | 'hybrid'
  page_size?: number
  profile_id?: string
}

export function semanticSearch(params: SemanticSearchParams): Promise<SemanticSearchResponse> {
  const searchParams = new URLSearchParams()
  searchParams.set('q', params.q)
  if (params.mode) searchParams.set('mode', params.mode)
  if (params.page_size) searchParams.set('page_size', String(params.page_size))
  if (params.profile_id) searchParams.set('profile_id', params.profile_id)

  return apiFetch<SemanticSearchResponse>(`/catalog/search/semantic?${searchParams.toString()}`)
}
