import { useEffect, useRef, useCallback } from 'react'
import { saveBookmark, BookmarkPayload } from '../api/viewing'

const PENDING_BOOKMARKS_KEY = 'pendingBookmarks'

interface PendingBookmark {
  profileId: string
  payload: BookmarkPayload
}

interface UseBookmarkSyncParams {
  profileId: string
  contentType: 'movie' | 'episode' | 'tstv_catchup' | 'tstv_startover'
  contentId: string
  durationSeconds: number
  isPlaying: boolean
}

export function useBookmarkSync({
  profileId,
  contentType,
  contentId,
  durationSeconds,
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
  // M-08: Only replay entries belonging to the current profile; keep others
  useEffect(() => {
    try {
      const raw = localStorage.getItem(PENDING_BOOKMARKS_KEY)
      if (!raw) return
      let pending: PendingBookmark[]
      try {
        pending = JSON.parse(raw)
        if (!Array.isArray(pending)) {
          localStorage.removeItem(PENDING_BOOKMARKS_KEY)
          return
        }
      } catch {
        localStorage.removeItem(PENDING_BOOKMARKS_KEY)
        return
      }
      localStorage.removeItem(PENDING_BOOKMARKS_KEY)

      const toReplay: PendingBookmark[] = []
      const toKeep: PendingBookmark[] = []
      for (const entry of pending) {
        if (entry.profileId === profileId) {
          toReplay.push(entry)
        } else {
          toKeep.push(entry)
        }
      }

      // Re-persist entries belonging to other profiles
      if (toKeep.length > 0) {
        localStorage.setItem(PENDING_BOOKMARKS_KEY, JSON.stringify(toKeep))
      }

      for (const entry of toReplay) {
        saveBookmark(entry.profileId, entry.payload).catch(() => {
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
  }, [profileId])

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
