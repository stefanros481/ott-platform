import { apiFetch } from './client'

export interface RecommendationItem {
  id: string
  title: string
  poster_url: string | null
  landscape_url: string | null
  synopsis_short: string | null
  title_type: string
  release_year: number | null
  age_rating: string | null
  similarity_score: number | null
}

export interface ContentRailData {
  name: string
  rail_type: string
  items: RecommendationItem[]
}

export interface HomeRecommendations {
  rails: ContentRailData[]
}

export function getHomeRecommendations(profileId: string): Promise<HomeRecommendations> {
  return apiFetch<HomeRecommendations>(`/recommendations/home?profile_id=${profileId}`)
}

export function getSimilarTitles(titleId: string): Promise<RecommendationItem[]> {
  return apiFetch<RecommendationItem[]>(`/recommendations/similar/${titleId}`)
}
