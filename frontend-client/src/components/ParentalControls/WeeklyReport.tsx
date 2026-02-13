import { useState, useEffect } from 'react'
import { getWeeklyReport, type ProfileWeeklyStats, type WeeklyReportResponse } from '../../api/parentalControls'

function formatDuration(minutes: number): string {
  if (minutes < 60) return `${minutes}m`
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  return m > 0 ? `${h}h ${m}m` : `${h}h`
}

function formatDayLabel(dateStr: string): string {
  try {
    const date = new Date(dateStr + 'T00:00:00')
    return date.toLocaleDateString([], { weekday: 'short' })
  } catch {
    return dateStr.slice(-2)
  }
}

function DailyBarChart({
  dailyTotals,
}: {
  dailyTotals: { date: string; counted_minutes: number; educational_minutes: number }[]
}) {
  const maxMinutes = Math.max(...dailyTotals.map((d) => d.counted_minutes + d.educational_minutes), 1)

  return (
    <div className="flex items-end gap-1.5 h-32">
      {dailyTotals.map((day) => {
        const total = day.counted_minutes + day.educational_minutes
        const heightPct = Math.max((total / maxMinutes) * 100, 2)
        const eduPct = total > 0 ? (day.educational_minutes / total) * 100 : 0

        return (
          <div key={day.date} className="flex-1 flex flex-col items-center gap-1">
            <div className="w-full relative" style={{ height: '100px' }}>
              <div
                className="absolute bottom-0 left-0 right-0 rounded-t overflow-hidden"
                style={{ height: `${heightPct}%` }}
              >
                {/* Educational portion */}
                {eduPct > 0 && (
                  <div
                    className="bg-emerald-500/60 w-full"
                    style={{ height: `${eduPct}%` }}
                  />
                )}
                {/* Counted portion */}
                <div
                  className="bg-primary-500/70 w-full"
                  style={{ height: `${100 - eduPct}%` }}
                />
              </div>
            </div>
            <span className="text-[10px] text-gray-500">{formatDayLabel(day.date)}</span>
          </div>
        )
      })}
    </div>
  )
}

function ProfileCard({ stats }: { stats: ProfileWeeklyStats }) {
  return (
    <div className="bg-surface-overlay rounded-lg p-4 border border-white/5">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-8 h-8 rounded-full bg-amber-600 flex items-center justify-center text-xs font-bold text-white uppercase">
          {stats.profile_name.charAt(0)}
        </div>
        <h3 className="text-sm font-medium text-white">{stats.profile_name}</h3>
      </div>

      {/* Bar chart */}
      <DailyBarChart dailyTotals={stats.daily_totals} />

      {/* Legend */}
      <div className="flex items-center gap-4 mt-3 mb-4">
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-sm bg-primary-500/70" />
          <span className="text-[10px] text-gray-400">Counted</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-sm bg-emerald-500/60" />
          <span className="text-[10px] text-gray-400">Educational</span>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div>
          <p className="text-xs text-gray-500">Average Daily</p>
          <p className="text-sm font-medium text-white">{formatDuration(Math.round(stats.average_daily_minutes))}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Total This Week</p>
          <p className="text-sm font-medium text-white">{formatDuration(stats.total_minutes)}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Educational</p>
          <p className="text-sm font-medium text-emerald-400">{formatDuration(stats.educational_minutes)}</p>
        </div>
        {stats.limit_usage_percent !== null && (
          <div>
            <p className="text-xs text-gray-500">Limit Usage</p>
            <p className="text-sm font-medium text-white">{Math.round(stats.limit_usage_percent)}%</p>
          </div>
        )}
      </div>

      {/* Top titles */}
      {stats.top_titles.length > 0 && (
        <div>
          <p className="text-xs text-gray-500 mb-2">Most Watched</p>
          <div className="space-y-1.5">
            {stats.top_titles.slice(0, 3).map((title, i) => (
              <div key={title.title_id} className="flex items-center gap-2">
                <span className="text-xs text-gray-600 w-4">{i + 1}.</span>
                <span className="text-sm text-gray-300 flex-1 truncate">{title.title_name}</span>
                <span className="text-xs text-gray-500 tabular-nums">{formatDuration(title.total_minutes)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default function WeeklyReport() {
  const [report, setReport] = useState<WeeklyReportResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const load = async () => {
      setLoading(true)
      try {
        const data = await getWeeklyReport()
        setReport(data)
      } catch (err: unknown) {
        const e = err as { message?: string }
        setError(e.message || 'Failed to load weekly report')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  if (loading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 2 }).map((_, i) => (
          <div key={i} className="h-64 bg-surface-overlay animate-pulse rounded-lg" />
        ))}
      </div>
    )
  }

  if (error) {
    return <p className="text-sm text-red-400">{error}</p>
  }

  if (!report || report.profiles.length === 0) {
    return <p className="text-sm text-gray-500">No weekly data available yet.</p>
  }

  return (
    <div>
      <p className="text-xs text-gray-500 mb-4">
        Week of {report.week_start} to {report.week_end}
      </p>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {report.profiles.map((stats) => (
          <ProfileCard key={stats.profile_id} stats={stats} />
        ))}
      </div>
    </div>
  )
}
