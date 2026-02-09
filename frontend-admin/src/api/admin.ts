import { apiFetch } from './client'

// ---- Types ----

export interface User {
  id: string
  email: string
  subscription_tier: string
  is_admin: boolean
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
}

export interface AdminStats {
  title_count: number
  channel_count: number
  user_count: number
  embedding_count: number
}

export interface Genre {
  id: string
  name: string
  slug: string
}

export interface Title {
  id: string
  title: string
  title_type: 'movie' | 'series'
  synopsis_short: string
  synopsis_long: string
  release_year: number
  duration_minutes: number
  age_rating: string
  poster_url: string
  landscape_url: string
  hls_manifest_url: string
  mood_tags: string[]
  theme_tags: string[]
  genre_ids: string[]
  genres?: Genre[]
  is_featured?: boolean
  created_at?: string
}

export interface TitlePayload {
  title: string
  title_type: 'movie' | 'series'
  synopsis_short: string
  synopsis_long: string
  release_year: number
  duration_minutes: number
  age_rating: string
  poster_url: string
  landscape_url: string
  hls_manifest_url: string
  mood_tags: string[]
  theme_tags: string[]
  genre_ids: string[]
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface Channel {
  id: string
  name: string
  channel_number: number
  logo_url: string
  genre: string
  is_hd: boolean
  hls_live_url?: string
}

export interface ChannelPayload {
  name: string
  channel_number: number
  logo_url: string
  genre: string
  is_hd: boolean
  hls_live_url: string
}

export interface ScheduleEntry {
  id: string
  channel_id: string
  title: string
  synopsis: string
  genre: string
  start_time: string
  end_time: string
  age_rating: string
  is_new: boolean
}

export interface SchedulePayload {
  channel_id: string
  title: string
  synopsis: string
  genre: string
  start_time: string
  end_time: string
  age_rating: string
  is_new: boolean
}

export interface EmbeddingResult {
  generated: number
  total: number
}

export interface AdminUser {
  id: string
  email: string
  subscription_tier: string
  is_admin: boolean
  created_at: string
  profiles_count?: number
}

// ---- Auth ----

export function login(email: string, password: string) {
  return apiFetch<LoginResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
}

export function getMe() {
  return apiFetch<User>('/auth/me')
}

// ---- Stats ----

export function getStats() {
  return apiFetch<AdminStats>('/admin/stats')
}

// ---- Titles ----

export function getTitles(page = 1, pageSize = 20, search = '') {
  const params = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  })
  if (search) params.set('q', search)
  return apiFetch<PaginatedResponse<Title>>(`/admin/titles?${params}`)
}

export function getTitle(id: string) {
  return apiFetch<Title>(`/admin/titles/${id}`)
}

export function createTitle(payload: TitlePayload) {
  return apiFetch<Title>('/admin/titles', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updateTitle(id: string, payload: TitlePayload) {
  return apiFetch<Title>(`/admin/titles/${id}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}

export function deleteTitle(id: string) {
  return apiFetch<void>(`/admin/titles/${id}`, { method: 'DELETE' })
}

// ---- Channels ----

export function getChannels() {
  return apiFetch<Channel[]>('/admin/channels')
}

export function createChannel(payload: ChannelPayload) {
  return apiFetch<Channel>('/admin/channels', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updateChannel(id: string, payload: ChannelPayload) {
  return apiFetch<Channel>(`/admin/channels/${id}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}

export function deleteChannel(id: string) {
  return apiFetch<void>(`/admin/channels/${id}`, { method: 'DELETE' })
}

// ---- Schedule ----

export function getSchedule(channelId: string, date: string) {
  const params = new URLSearchParams({ channel_id: channelId, date })
  return apiFetch<ScheduleEntry[]>(`/admin/schedule?${params}`)
}

export function createScheduleEntry(payload: SchedulePayload) {
  return apiFetch<ScheduleEntry>('/admin/schedule', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updateScheduleEntry(id: string, payload: SchedulePayload) {
  return apiFetch<ScheduleEntry>(`/admin/schedule/${id}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}

export function deleteScheduleEntry(id: string) {
  return apiFetch<void>(`/admin/schedule/${id}`, { method: 'DELETE' })
}

// ---- Embeddings ----

export function generateEmbeddings() {
  return apiFetch<EmbeddingResult>('/admin/embeddings/generate', {
    method: 'POST',
  })
}

// ---- Genres ----

export function getGenres() {
  return apiFetch<Genre[]>('/catalog/genres')
}

// ---- Users (read-only) ----

export function getUsers() {
  return apiFetch<AdminUser[]>('/admin/users')
}
