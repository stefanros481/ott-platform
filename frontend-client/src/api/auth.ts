import { apiFetch } from './client'

export interface AuthResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface UserProfile {
  id: string
  email: string
  subscription_tier: string
  is_admin: boolean
}

export interface Profile {
  id: string
  name: string
  avatar_url: string | null
  parental_rating: string | null
  is_kids: boolean
}

export interface CreateProfilePayload {
  name: string
  parental_rating?: string
  is_kids?: boolean
}

export function loginUser(email: string, password: string): Promise<AuthResponse> {
  return apiFetch<AuthResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
}

export function registerUser(email: string, password: string): Promise<AuthResponse> {
  return apiFetch<AuthResponse>('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
}

export function getCurrentUser(): Promise<UserProfile> {
  return apiFetch<UserProfile>('/auth/me')
}

export function getProfiles(): Promise<Profile[]> {
  return apiFetch<Profile[]>('/auth/profiles')
}

export function createProfile(payload: CreateProfilePayload): Promise<Profile> {
  return apiFetch<Profile>('/auth/profiles', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}
