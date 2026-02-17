import { apiFetch } from './client'

export interface Channel {
  id: string
  name: string
  channel_number: number
  logo_url: string | null
  genre: string
  is_hd: boolean
  is_favorite: boolean
  hls_live_url: string | null
}

export interface ScheduleEntry {
  id: string
  title: string
  synopsis: string
  genre: string
  start_time: string
  end_time: string
  is_live: boolean
  is_replayable: boolean
  age_rating: string
  thumbnail_url: string | null
}

export interface NowPlaying {
  channel: Channel
  current_program: ScheduleEntry | null
  next_program: ScheduleEntry | null
}

export function getChannels(profileId?: string): Promise<Channel[]> {
  const qs = profileId ? `?profile_id=${profileId}` : ''
  return apiFetch<Channel[]>(`/epg/channels${qs}`)
}

export function getSchedule(channelId: string, date: string): Promise<ScheduleEntry[]> {
  return apiFetch<ScheduleEntry[]>(`/epg/schedule/${channelId}?date=${date}`)
}

export function getNowPlaying(): Promise<NowPlaying[]> {
  return apiFetch<NowPlaying[]>('/epg/now')
}
