import { apiFetch } from './client'

export interface ContinueWatchingItem {
  content_type: 'movie' | 'episode'
  content_id: string
  position_seconds: number
  duration_seconds: number
  title_info: {
    id: string
    title: string
    poster_url: string
    landscape_url: string | null
    episode_title?: string
    season_number?: number
    episode_number?: number
  }
}

export interface WatchlistItem {
  title_id: string
  title_info: {
    id: string
    title: string
    poster_url: string
    landscape_url: string | null
    title_type: 'movie' | 'series'
    release_year: number
    age_rating: string
  }
}

export interface BookmarkPayload {
  content_type: 'movie' | 'episode'
  content_id: string
  position_seconds: number
  duration_seconds: number
}

export interface RatingPayload {
  title_id: string
  rating: 1 | -1
}

export function getContinueWatching(profileId: string): Promise<ContinueWatchingItem[]> {
  return apiFetch<ContinueWatchingItem[]>(`/viewing/continue-watching?profile_id=${profileId}`)
}

export function saveBookmark(profileId: string, payload: BookmarkPayload): Promise<void> {
  return apiFetch<void>(`/viewing/bookmarks?profile_id=${profileId}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}

export interface RatingResponse {
  title_id: string
  rating: 1 | -1
}

export function getRating(profileId: string, titleId: string): Promise<RatingResponse | null> {
  return apiFetch<RatingResponse | null>(`/viewing/ratings/${titleId}?profile_id=${profileId}`)
}

export function rateTitle(profileId: string, payload: RatingPayload): Promise<void> {
  return apiFetch<void>(`/viewing/ratings?profile_id=${profileId}`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function getWatchlist(profileId: string): Promise<WatchlistItem[]> {
  return apiFetch<WatchlistItem[]>(`/viewing/watchlist?profile_id=${profileId}`)
}

export function addToWatchlist(profileId: string, titleId: string): Promise<void> {
  return apiFetch<void>(`/viewing/watchlist/${titleId}?profile_id=${profileId}`, {
    method: 'POST',
  })
}

export function removeFromWatchlist(profileId: string, titleId: string): Promise<void> {
  return apiFetch<void>(`/viewing/watchlist/${titleId}?profile_id=${profileId}`, {
    method: 'DELETE',
  })
}
