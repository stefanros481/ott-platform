import { useState, useEffect, useCallback } from 'react'
import { getViewingHistory, type ViewingHistoryDay, type ViewingHistorySession } from '../../api/parentalControls'

interface ViewingHistoryProps {
  profileId: string
  profileName: string
}

function formatDuration(minutes: number): string {
  if (minutes < 60) return `${minutes}m`
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  return m > 0 ? `${h}h ${m}m` : `${h}h`
}

function formatTimeRange(startedAt: string, endedAt: string | null): string {
  const fmt = (iso: string) => {
    try {
      return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    } catch {
      return ''
    }
  }
  const start = fmt(startedAt)
  const end = endedAt ? fmt(endedAt) : 'now'
  return `${start} - ${end}`
}

function formatDate(dateStr: string): string {
  try {
    const date = new Date(dateStr + 'T00:00:00')
    return date.toLocaleDateString([], {
      weekday: 'long',
      month: 'short',
      day: 'numeric',
    })
  } catch {
    return dateStr
  }
}

function DeviceIcon({ type }: { type: string | null }) {
  if (!type) return null
  const icons: Record<string, string> = {
    tv: 'M4 5h16a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1Zm4 14h8',
    mobile: 'M7 2h10a2 2 0 0 1 2 2v16a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2Zm5 18h.01',
    tablet: 'M6 2h12a2 2 0 0 1 2 2v16a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2Zm6 18h.01',
    web: 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2Zm-1 17.93c-3.95-.49-7-3.85-7-7.93h3l2 4v3.93Zm6.54-2.93L16 15h-2v-2h4c0 1.93-.68 3.7-1.46 5Z',
  }
  const pathData = icons[type] || icons['web']
  return (
    <svg className="w-3.5 h-3.5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d={pathData} />
    </svg>
  )
}

function SessionRow({ session }: { session: ViewingHistorySession }) {
  return (
    <div className="flex items-center gap-3 py-2 px-3 hover:bg-white/5 rounded-lg transition-colors">
      <DeviceIcon type={session.device_type} />
      <div className="flex-1 min-w-0">
        <p className="text-sm text-white truncate">{session.title_name}</p>
        <p className="text-xs text-gray-500">
          {formatTimeRange(session.started_at, session.ended_at)}
        </p>
      </div>
      <div className="flex items-center gap-2 shrink-0">
        {session.is_educational && (
          <span className="text-[10px] font-medium uppercase px-1.5 py-0.5 bg-emerald-500/20 text-emerald-400 rounded">
            Edu
          </span>
        )}
        <span className="text-xs text-gray-400 tabular-nums">
          {formatDuration(session.duration_minutes)}
        </span>
      </div>
    </div>
  )
}

function DaySection({ day }: { day: ViewingHistoryDay }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="border border-white/5 rounded-lg overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-white/5 transition-colors text-left"
      >
        <div>
          <p className="text-sm font-medium text-white">{formatDate(day.date)}</p>
          <p className="text-xs text-gray-500">
            {formatDuration(day.total_minutes)} total
            {day.educational_minutes > 0 && (
              <span className="text-emerald-500"> | {formatDuration(day.educational_minutes)} educational</span>
            )}
          </p>
        </div>
        <svg
          className={`w-4 h-4 text-gray-500 transition-transform ${expanded ? 'rotate-180' : ''}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
        </svg>
      </button>
      {expanded && (
        <div className="border-t border-white/5 py-1">
          {day.sessions.length === 0 ? (
            <p className="text-sm text-gray-500 px-4 py-2">No sessions</p>
          ) : (
            day.sessions.map((session) => (
              <SessionRow key={session.session_id} session={session} />
            ))
          )}
        </div>
      )}
    </div>
  )
}

function todayStr(): string {
  return new Date().toISOString().slice(0, 10)
}

function weekAgoStr(): string {
  const d = new Date()
  d.setDate(d.getDate() - 7)
  return d.toISOString().slice(0, 10)
}

export default function ViewingHistory({ profileId, profileName }: ViewingHistoryProps) {
  const [days, setDays] = useState<ViewingHistoryDay[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [fromDate, setFromDate] = useState(weekAgoStr)
  const [toDate, setToDate] = useState(todayStr)

  const fetchHistory = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const resp = await getViewingHistory(
        profileId,
        fromDate || undefined,
        toDate || undefined,
      )
      setDays(resp.days)
    } catch (err: unknown) {
      const e = err as { message?: string; detail?: string }
      setError(e.message || e.detail || 'Failed to load history')
    } finally {
      setLoading(false)
    }
  }, [profileId, fromDate, toDate])

  useEffect(() => {
    fetchHistory()
  }, [fetchHistory])

  return (
    <div>
      <div className="flex items-center gap-3 mb-4">
        <div className="w-8 h-8 rounded-full bg-amber-600 flex items-center justify-center text-xs font-bold text-white uppercase">
          {profileName.charAt(0)}
        </div>
        <h3 className="text-base font-medium text-white">{profileName}</h3>
      </div>

      {/* Date filters */}
      <div className="flex flex-wrap gap-3 mb-4">
        <div>
          <label className="block text-xs text-gray-500 mb-1">From</label>
          <input
            type="date"
            value={fromDate}
            onChange={(e) => setFromDate(e.target.value)}
            className="px-3 py-1.5 text-sm bg-surface-overlay border border-white/10 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">To</label>
          <input
            type="date"
            value={toDate}
            onChange={(e) => setToDate(e.target.value)}
            className="px-3 py-1.5 text-sm bg-surface-overlay border border-white/10 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>
      </div>

      {loading && (
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="h-16 bg-surface-overlay animate-pulse rounded-lg" />
          ))}
        </div>
      )}

      {error && (
        <p className="text-sm text-red-400">{error}</p>
      )}

      {!loading && !error && days.length === 0 && (
        <p className="text-sm text-gray-500">No viewing history found for this period.</p>
      )}

      {!loading && !error && days.length > 0 && (
        <div className="space-y-2">
          {days.map((day) => (
            <DaySection key={day.date} day={day} />
          ))}
        </div>
      )}
    </div>
  )
}
