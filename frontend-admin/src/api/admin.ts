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

// ---- Packages ----

export interface PackageResponse {
  id: string
  name: string
  description: string | null
  tier: string
  max_streams: number
  price_cents: number
  currency: string
  title_count: number
}

export interface PackageCreate {
  name: string
  description?: string
  tier?: string
  max_streams?: number
  price_cents?: number
  currency?: string
}

export function getPackages(): Promise<PackageResponse[]> {
  return apiFetch<PackageResponse[]>('/admin/packages')
}

export function createPackage(data: PackageCreate): Promise<PackageResponse> {
  return apiFetch<PackageResponse>('/admin/packages', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function updatePackage(id: string, data: Partial<PackageCreate>): Promise<PackageResponse> {
  return apiFetch<PackageResponse>(`/admin/packages/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export function deletePackage(id: string): Promise<void> {
  return apiFetch<void>(`/admin/packages/${id}`, { method: 'DELETE' })
}

export function getPackageTitles(packageId: string, page = 1, pageSize = 50): Promise<TitlePaginatedResponse> {
  return apiFetch<TitlePaginatedResponse>(
    `/admin/packages/${packageId}/titles?page=${page}&page_size=${pageSize}`
  )
}

export function assignTitleToPackage(packageId: string, titleId: string): Promise<void> {
  return apiFetch<void>(`/admin/packages/${packageId}/titles`, {
    method: 'POST',
    body: JSON.stringify({ title_id: titleId }),
  })
}

export function removeTitleFromPackage(packageId: string, titleId: string): Promise<void> {
  return apiFetch<void>(`/admin/packages/${packageId}/titles/${titleId}`, {
    method: 'DELETE',
  })
}

// ---- Offers ----

export interface OfferResponse {
  id: string
  offer_type: 'rent' | 'buy'
  price_cents: number
  currency: string
  rental_window_hours: number | null
  is_active: boolean
  created_at: string
}

export interface OfferCreate {
  offer_type: 'rent' | 'buy'
  price_cents: number
  currency: string
  rental_window_hours?: number | null
}

export interface OfferUpdate {
  price_cents?: number
  currency?: string
  rental_window_hours?: number | null
  is_active?: boolean
}

export function getTitleOffers(titleId: string): Promise<OfferResponse[]> {
  return apiFetch<OfferResponse[]>(`/admin/titles/${titleId}/offers`)
}

export function createOffer(titleId: string, data: OfferCreate): Promise<OfferResponse> {
  return apiFetch<OfferResponse>(`/admin/titles/${titleId}/offers`, {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function updateOffer(titleId: string, offerId: string, data: Partial<OfferUpdate>): Promise<OfferResponse> {
  return apiFetch<OfferResponse>(`/admin/titles/${titleId}/offers/${offerId}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  })
}

// ---- Subscriptions & Entitlements ----

export interface UserEntitlement {
  id: string
  source_type: string          // "subscription" | "tvod_rent" | "tvod_buy"
  package_id: string | null
  package_name: string | null
  package_tier: string | null
  title_id: string | null
  title_name: string | null
  granted_at: string
  expires_at: string | null
  is_active: boolean
}

export function updateUserSubscription(
  userId: string,
  packageId: string | null,
  expiresAt?: string,
): Promise<void> {
  return apiFetch<void>(`/admin/users/${userId}/subscription`, {
    method: 'PATCH',
    body: JSON.stringify({ package_id: packageId, expires_at: expiresAt ?? null }),
  })
}

export function getUserEntitlements(
  userId: string,
  includeExpired = false,
): Promise<UserEntitlement[]> {
  return apiFetch<UserEntitlement[]>(
    `/admin/users/${userId}/entitlements?include_expired=${includeExpired}`,
  )
}

export function revokeUserEntitlement(userId: string, entitlementId: string): Promise<void> {
  return apiFetch<void>(`/admin/users/${userId}/entitlements/${entitlementId}`, {
    method: 'DELETE',
  })
}

// ---- SimLive ----

export interface SimLiveChannelStatus {
  channel_key: string
  running: boolean
  pid: number | null
  segment_count: number
  disk_bytes: number
  error: string | null
}

export interface CleanupResult {
  channels_processed: number
  total_segments_deleted: number
  total_bytes_freed: number
}

export function getSimLiveStatus(): Promise<SimLiveChannelStatus[]> {
  return apiFetch<SimLiveChannelStatus[]>('/admin/simlive/status')
}

export function startSimLive(channelKey: string): Promise<{ status: string }> {
  return apiFetch<{ status: string }>(`/admin/simlive/${channelKey}/start`, { method: 'POST' })
}

export function stopSimLive(channelKey: string): Promise<{ status: string }> {
  return apiFetch<{ status: string }>(`/admin/simlive/${channelKey}/stop`, { method: 'POST' })
}

export function restartSimLive(channelKey: string): Promise<{ status: string }> {
  return apiFetch<{ status: string }>(`/admin/simlive/${channelKey}/restart`, { method: 'POST' })
}

export function cleanupSimLive(): Promise<CleanupResult> {
  return apiFetch<CleanupResult>('/admin/simlive/cleanup', { method: 'POST' })
}

// ---- TSTV Rules ----

export interface TSTVRules {
  channel_id: string
  channel_name: string
  tstv_enabled: boolean
  startover_enabled: boolean
  catchup_enabled: boolean
  cutv_window_hours: number
  catchup_window_hours: number
}

export interface TSTVRulesUpdate {
  tstv_enabled?: boolean
  startover_enabled?: boolean
  catchup_enabled?: boolean
  cutv_window_hours?: number
}

export function getTSTVRules(): Promise<TSTVRules[]> {
  return apiFetch<TSTVRules[]>('/admin/tstv/rules')
}

export function updateTSTVRules(channelId: string, data: TSTVRulesUpdate): Promise<TSTVRules> {
  return apiFetch<TSTVRules>(`/admin/tstv/rules/${channelId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}
