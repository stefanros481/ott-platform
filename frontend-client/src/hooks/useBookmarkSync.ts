import { useEffect, useRef, useCallback } from 'react'
import { saveBookmark, BookmarkPayload } from '../api/viewing'

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
  const doSaveRef = useRef<(positionSeconds: number) => void>(() => {})

  const buildPayload = useCallback(
    (positionSeconds: number): BookmarkPayload => ({
      content_type: contentType,
      content_id: contentId,
      position_seconds: Math.floor(positionSeconds),
      duration_seconds: Math.floor(durationSeconds),
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
      if (durationSeconds <= 0) return // API requires duration >= 1
      saveBookmark(profileId, buildPayload(positionSeconds)).catch(() => {
        persistToLocalStorage(positionSeconds)
      })
    },
    [profileId, durationSeconds, buildPayload, persistToLocalStorage],
  )

  // Keep ref in sync so unmount cleanup always uses the latest doSave
  useEffect(() => {
    doSaveRef.current = doSave
  }, [doSave])

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

  // No independent interval — VideoPlayer drives periodic saves via onPositionUpdate
  // which calls saveNow(). This avoids duplicate bookmark writes every 30 seconds.

  // Save final position on unmount — use ref to avoid stale closure
  useEffect(() => {
    return () => {
      doSaveRef.current(positionRef.current)
    }
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
