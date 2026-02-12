import { useEffect, useRef, useCallback } from 'react'
import { saveBookmark, BookmarkPayload } from '../api/viewing'

const HEARTBEAT_INTERVAL_MS = 30_000
const PENDING_BOOKMARKS_KEY = 'pendingBookmarks'

interface PendingBookmark {
  profileId: string
  payload: BookmarkPayload
}

interface UseBookmarkSyncParams {
  profileId: string
  contentType: 'movie' | 'episode'
  contentId: string
  durationSeconds: number
  isPlaying: boolean
}

export function useBookmarkSync({
  profileId,
  contentType,
  contentId,
  durationSeconds,
  isPlaying,
}: UseBookmarkSyncParams): { saveNow: (positionSeconds: number) => void } {
  const positionRef = useRef(0)
  const intervalRef = useRef<ReturnType<typeof setInterval>>()

  const buildPayload = useCallback(
    (positionSeconds: number): BookmarkPayload => ({
      content_type: contentType,
      content_id: contentId,
      position_seconds: positionSeconds,
      duration_seconds: durationSeconds,
    }),
    [contentType, contentId, durationSeconds],
  )

  const persistToLocalStorage = useCallback(
    (positionSeconds: number) => {
      try {
        const raw = localStorage.getItem(PENDING_BOOKMARKS_KEY)
        const pending: PendingBookmark[] = raw ? JSON.parse(raw) : []
        pending.push({ profileId, payload: buildPayload(positionSeconds) })
        localStorage.setItem(PENDING_BOOKMARKS_KEY, JSON.stringify(pending))
      } catch {
        // localStorage unavailable — silently ignore
      }
    },
    [profileId, buildPayload],
  )

  const doSave = useCallback(
    (positionSeconds: number) => {
      saveBookmark(profileId, buildPayload(positionSeconds)).catch(() => {
        persistToLocalStorage(positionSeconds)
      })
    },
    [profileId, buildPayload, persistToLocalStorage],
  )

  // Flush pending bookmarks from localStorage on mount
  useEffect(() => {
    try {
      const raw = localStorage.getItem(PENDING_BOOKMARKS_KEY)
      if (!raw) return
      const pending: PendingBookmark[] = JSON.parse(raw)
      localStorage.removeItem(PENDING_BOOKMARKS_KEY)
      for (const entry of pending) {
        saveBookmark(entry.profileId, entry.payload).catch(() => {
          // If flush fails again, re-persist
          try {
            const current = localStorage.getItem(PENDING_BOOKMARKS_KEY)
            const arr: PendingBookmark[] = current ? JSON.parse(current) : []
            arr.push(entry)
            localStorage.setItem(PENDING_BOOKMARKS_KEY, JSON.stringify(arr))
          } catch {
            // give up
          }
        })
      }
    } catch {
      // localStorage unavailable
    }
  }, [])

  // 30-second heartbeat while playing
  useEffect(() => {
    if (!isPlaying) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = undefined
      }
      return
    }

    intervalRef.current = setInterval(() => {
      doSave(positionRef.current)
    }, HEARTBEAT_INTERVAL_MS)

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = undefined
      }
    }
  }, [isPlaying, doSave])

  // Save final position on unmount
  useEffect(() => {
    return () => {
      doSave(positionRef.current)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const saveNow = useCallback(
    (positionSeconds: number) => {
      positionRef.current = positionSeconds
      doSave(positionSeconds)
    },
    [doSave],
  )

  return { saveNow }
}
