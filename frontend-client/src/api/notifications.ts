import { apiFetch } from './client'

export interface AppNotification {
  id: string
  notification_type: string
  title: string
  body: string
  deep_link: string | null
  is_read: boolean
  created_at: string
}

export function getNotifications(profileId: string, unreadOnly = false): Promise<AppNotification[]> {
  const params = new URLSearchParams({ profile_id: profileId })
  if (unreadOnly) params.set('unread_only', 'true')
  return apiFetch<AppNotification[]>(`/notifications?${params}`)
}

export function markNotificationRead(profileId: string, notificationId: string): Promise<void> {
  return apiFetch<void>(
    `/notifications/${notificationId}/read?profile_id=${profileId}`,
    { method: 'POST' },
  )
}

export function markAllNotificationsRead(profileId: string): Promise<void> {
  return apiFetch<void>(
    `/notifications/read-all?profile_id=${profileId}`,
    { method: 'POST' },
  )
}
