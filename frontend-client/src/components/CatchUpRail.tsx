import { useNavigate } from 'react-router-dom'
import type { CatchUpProgram } from '../api/tstv'

interface CatchUpRailProps {
  programs: CatchUpProgram[]
}

function formatTime(dateStr: string): string {
  return new Date(dateStr).toLocaleTimeString(undefined, {
    hour: '2-digit',
    minute: '2-digit',
  })
}

function formatDuration(startStr: string, endStr: string): string {
  const mins = Math.round((new Date(endStr).getTime() - new Date(startStr).getTime()) / 60000)
  if (mins < 60) return `${mins}m`
  const h = Math.floor(mins / 60)
  const m = mins % 60
  return m > 0 ? `${h}h ${m}m` : `${h}h`
}

export default function CatchUpRail({ programs }: CatchUpRailProps) {
  const navigate = useNavigate()

  if (programs.length === 0) return null

  const handlePlay = (program: CatchUpProgram) => {
    const e = program.schedule_entry
    navigate(`/play/live/${e.channel_id}`, {
      state: {
        catchupMode: true,
        scheduleEntryId: e.id,
        channelId: e.channel_id,
      },
    })
  }

  return (
    <div className="flex gap-3 overflow-x-auto pb-2" style={{ scrollbarWidth: 'none' }}>
      {programs.map((program) => {
        const e = program.schedule_entry
        const progress = program.bookmark_position_seconds != null
          ? Math.round((program.bookmark_position_seconds / ((new Date(e.end_time).getTime() - new Date(e.start_time).getTime()) / 1000)) * 100)
          : 0
        const hoursLeft = (new Date(program.expires_at).getTime() - Date.now()) / (1000 * 60 * 60)
        const expiringSoon = hoursLeft < 24

        return (
          <button
            key={e.id}
            onClick={() => handlePlay(program)}
            className="flex-shrink-0 w-[220px] bg-surface-raised/50 hover:bg-surface-raised border border-white/5 rounded-lg overflow-hidden transition-colors text-left group"
          >
            {/* Thumbnail placeholder */}
            <div className="relative w-full h-[100px] bg-primary-500/10 flex items-center justify-center">
              <svg className="w-10 h-10 text-primary-500/40 group-hover:text-primary-400/60 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.347a1.125 1.125 0 0 1 0 1.972l-11.54 6.347a1.125 1.125 0 0 1-1.667-.986V5.653Z" />
              </svg>
              {expiringSoon && (
                <span className="absolute top-2 right-2 px-1.5 py-0.5 text-[10px] font-medium bg-amber-500/80 text-white rounded">
                  Expires today
                </span>
              )}
            </div>
            {/* Progress bar */}
            {progress > 0 && (
              <div className="h-1 bg-white/10">
                <div className="h-full bg-primary-500" style={{ width: `${Math.min(progress, 100)}%` }} />
              </div>
            )}
            {/* Info */}
            <div className="p-3">
              <p className="text-sm font-medium text-white truncate">{e.title}</p>
              <p className="text-xs text-gray-500 mt-0.5 truncate">
                {formatTime(e.start_time)} · {formatDuration(e.start_time, e.end_time)}
                {e.genre && ` · ${e.genre}`}
              </p>
              {program.bookmark_position_seconds != null && (
                <p className="text-xs text-primary-400 mt-1">
                  {Math.floor(program.bookmark_position_seconds / 60)}m watched
                </p>
              )}
            </div>
          </button>
        )
      })}
    </div>
  )
}
