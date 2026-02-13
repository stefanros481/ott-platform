import { apiFetch } from './client'

export interface TitleInfo {
  title: string
  poster_url: string | null
  landscape_url: string | null
  title_type: 'movie' | 'series'
  age_rating: string | null
  episode_title?: string | null
  season_number?: number | null
  episode_number?: number | null
}

export interface NextEpisodeInfo {
  episode_id: string
  season_number: number
  episode_number: number
  episode_title: string
}

export interface ContinueWatchingItem {
  id: string
  content_type: 'movie' | 'episode'
  content_id: string
  position_seconds: number
  duration_seconds: number
  progress_percent: number
  completed: boolean
  dismissed_at: string | null
  updated_at: string
  resumption_score: number | null
  title_info: TitleInfo
  next_episode: NextEpisodeInfo | null
}

export interface BookmarkResponse {
  id: string
  content_type: string
  content_id: string
  position_seconds: number
  duration_seconds: number
  completed: boolean
  dismissed_at: string | null
  updated_at: string
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

export function getContinueWatching(
  profileId: string,
  deviceType?: string,
  hourOfDay?: number,
): Promise<ContinueWatchingItem[]> {
  const params = new URLSearchParams({ profile_id: profileId })
  if (deviceType) params.set('device_type', deviceType)
  if (hourOfDay !== undefined) params.set('hour_of_day', String(hourOfDay))
  return apiFetch<ContinueWatchingItem[]>(`/viewing/continue-watching?${params}`)
}

export function getPausedBookmarks(profileId: string): Promise<ContinueWatchingItem[]> {
  return apiFetch<ContinueWatchingItem[]>(`/viewing/continue-watching/paused?profile_id=${profileId}`)
}

export function dismissBookmark(bookmarkId: string, profileId: string): Promise<BookmarkResponse> {
  return apiFetch<BookmarkResponse>(`/viewing/bookmarks/${bookmarkId}/dismiss?profile_id=${profileId}`, {
    method: 'POST',
  })
}

export function restoreBookmark(bookmarkId: string, profileId: string): Promise<BookmarkResponse> {
  return apiFetch<BookmarkResponse>(`/viewing/bookmarks/${bookmarkId}/restore?profile_id=${profileId}`, {
    method: 'POST',
  })
}

export function getBookmarkByContent(profileId: string, contentId: string): Promise<BookmarkResponse | null> {
  return apiFetch<BookmarkResponse | null>(`/viewing/bookmarks/by-content/${contentId}?profile_id=${profileId}`)
}

export function saveBookmark(profileId: string, payload: BookmarkPayload): Promise<BookmarkResponse> {
  return apiFetch<BookmarkResponse>(`/viewing/bookmarks?profile_id=${profileId}`, {
    method: 'PUT',
    body: JSON.stringify({
      ...payload,
      position_seconds: Math.floor(payload.position_seconds),
      duration_seconds: Math.floor(payload.duration_seconds),
    }),
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
