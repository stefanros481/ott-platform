import { useRef, useState, useEffect, useMemo } from 'react'
import type { Channel, ScheduleEntry } from '../api/epg'

interface EpgGridProps {
  channels: Channel[]
  scheduleData: Record<string, ScheduleEntry[]>
  currentTime: Date
  onProgramClick: (entry: ScheduleEntry, channel: Channel) => void
}

const HOUR_WIDTH = 360 // pixels per hour
const CHANNEL_HEIGHT = 72
const CHANNEL_LABEL_WIDTH = 180
const VISIBLE_HOURS = 24

function getTimeOffset(time: Date, dayStart: Date): number {
  return ((time.getTime() - dayStart.getTime()) / 3600000) * HOUR_WIDTH
}

function formatTimeShort(date: Date): string {
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })
}

export default function EpgGrid({ channels, scheduleData, currentTime, onProgramClick }: EpgGridProps) {
  const scrollRef = useRef<HTMLDivElement>(null)
  const [filter, setFilter] = useState<string>('all')
  const [selectedProgram, setSelectedProgram] = useState<{ entry: ScheduleEntry; channel: Channel } | null>(null)

  // Day start: beginning of the day from currentTime
  const dayStart = useMemo(() => {
    const d = new Date(currentTime)
    d.setHours(0, 0, 0, 0)
    return d
  }, [currentTime])

  // Time slots for header (each hour)
  const timeSlots = useMemo(() => {
    const slots: Date[] = []
    for (let h = 0; h < VISIBLE_HOURS; h++) {
      const d = new Date(dayStart)
      d.setHours(h)
      slots.push(d)
    }
    return slots
  }, [dayStart])

  // Get unique genres for filter
  const genres = useMemo(() => {
    const genreSet = new Set<string>()
    channels.forEach(ch => {
      if (ch.genre) genreSet.add(ch.genre)
    })
    return Array.from(genreSet).sort()
  }, [channels])

  // Filter channels
  const filteredChannels = useMemo(() => {
    if (filter === 'all') return channels
    if (filter === 'favorites') return channels.filter(ch => ch.is_favorite)
    return channels.filter(ch => ch.genre === filter)
  }, [channels, filter])

  // Scroll to current time on mount
  useEffect(() => {
    const el = scrollRef.current
    if (!el) return
    const nowOffset = getTimeOffset(currentTime, dayStart)
    el.scrollLeft = Math.max(0, nowOffset - el.clientWidth / 3)
  }, [currentTime, dayStart])

  const nowOffset = getTimeOffset(currentTime, dayStart)

  return (
    <div className="flex flex-col h-full">
      {/* Filter bar */}
      <div className="flex items-center gap-2 px-4 py-3 bg-surface-raised border-b border-white/5 overflow-x-auto">
        <FilterButton label="All" active={filter === 'all'} onClick={() => setFilter('all')} />
        <FilterButton label="Favorites" active={filter === 'favorites'} onClick={() => setFilter('favorites')} />
        {genres.map(g => (
          <FilterButton key={g} label={g} active={filter === g} onClick={() => setFilter(g)} />
        ))}
      </div>

      {/* Grid container */}
      <div className="flex flex-1 overflow-hidden">
        {/* Channel labels (fixed left column) */}
        <div className="flex-shrink-0 bg-surface-raised border-r border-white/5" style={{ width: CHANNEL_LABEL_WIDTH }}>
          {/* Time header spacer */}
          <div className="h-10 border-b border-white/5" />
          {/* Channel names */}
          {filteredChannels.map(ch => (
            <div
              key={ch.id}
              className="flex items-center gap-3 px-3 border-b border-white/5"
              style={{ height: CHANNEL_HEIGHT }}
            >
              {ch.logo_url ? (
                <img src={ch.logo_url} alt={ch.name} className="w-8 h-8 rounded object-contain bg-white/10" />
              ) : (
                <div className="w-8 h-8 rounded bg-surface-overlay flex items-center justify-center text-xs font-bold text-gray-400">
                  {ch.channel_number}
                </div>
              )}
              <div className="min-w-0">
                <p className="text-sm font-medium text-white truncate">{ch.name}</p>
                <p className="text-xs text-gray-500">{ch.channel_number} {ch.is_hd && '- HD'}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Scrollable schedule area */}
        <div ref={scrollRef} className="flex-1 overflow-auto" style={{ scrollbarWidth: 'thin', scrollbarColor: '#333 #0f0f0f' }}>
          <div className="relative" style={{ width: HOUR_WIDTH * VISIBLE_HOURS, minHeight: '100%' }}>
            {/* Time header */}
            <div className="sticky top-0 z-20 flex h-10 bg-surface-raised border-b border-white/5">
              {timeSlots.map((slot, i) => (
                <div
                  key={i}
                  className="flex-shrink-0 flex items-center px-3 text-xs text-gray-400 border-r border-white/5"
                  style={{ width: HOUR_WIDTH }}
                >
                  {formatTimeShort(slot)}
                </div>
              ))}
            </div>

            {/* Program rows */}
            {filteredChannels.map(ch => {
              const programs = scheduleData[ch.id] || []
              return (
                <div
                  key={ch.id}
                  className="relative border-b border-white/5"
                  style={{ height: CHANNEL_HEIGHT }}
                >
                  {programs.map(entry => {
                    const start = new Date(entry.start_time)
                    const end = new Date(entry.end_time)
                    const left = getTimeOffset(start, dayStart)
                    const width = ((end.getTime() - start.getTime()) / 3600000) * HOUR_WIDTH

                    const isLive = currentTime >= start && currentTime <= end

                    return (
                      <button
                        key={entry.id}
                        className={`absolute top-1 bottom-1 rounded px-2 flex items-center overflow-hidden text-left transition-colors ${
                          isLive
                            ? 'bg-primary-500/20 border border-primary-500/50 hover:bg-primary-500/30'
                            : 'bg-surface-overlay hover:bg-white/10 border border-white/5'
                        }`}
                        style={{ left, width: Math.max(width - 2, 40) }}
                        onClick={() => {
                          setSelectedProgram({ entry, channel: ch })
                          onProgramClick(entry, ch)
                        }}
                        title={entry.title}
                      >
                        <div className="min-w-0 flex-1">
                          <p className="text-xs font-medium text-white truncate">{entry.title}</p>
                          <p className="text-[10px] text-gray-400 truncate">
                            {formatTimeShort(start)} - {formatTimeShort(end)}
                          </p>
                        </div>
                        {isLive && (
                          <span className="flex-shrink-0 ml-1 w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                        )}
                      </button>
                    )
                  })}
                </div>
              )
            })}

            {/* "Now" red line */}
            <div
              className="absolute top-0 bottom-0 w-0.5 bg-red-500 z-10 pointer-events-none"
              style={{ left: nowOffset }}
            >
              <div className="absolute -top-0 -left-1.5 w-3.5 h-3.5 bg-red-500 rounded-full" />
            </div>
          </div>
        </div>
      </div>

      {/* Program detail overlay */}
      {selectedProgram && (
        <div className="absolute bottom-0 left-0 right-0 z-30 bg-surface-raised border-t border-white/10 p-4 shadow-2xl">
          <div className="max-w-screen-lg mx-auto flex items-start justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <h3 className="text-lg font-semibold text-white">{selectedProgram.entry.title}</h3>
                {selectedProgram.entry.is_live && (
                  <span className="px-2 py-0.5 text-[10px] font-bold uppercase bg-red-500 text-white rounded">LIVE</span>
                )}
              </div>
              <p className="text-sm text-gray-400 mb-1">
                {selectedProgram.channel.name} | {formatTimeShort(new Date(selectedProgram.entry.start_time))} - {formatTimeShort(new Date(selectedProgram.entry.end_time))}
              </p>
              <p className="text-sm text-gray-300 line-clamp-2">{selectedProgram.entry.synopsis}</p>
            </div>
            <button
              onClick={() => setSelectedProgram(null)}
              className="p-1 text-gray-400 hover:text-white transition-colors shrink-0"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

function FilterButton({ label, active, onClick }: { label: string; active: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className={`px-3 py-1.5 text-xs font-medium rounded-full whitespace-nowrap transition-colors ${
        active
          ? 'bg-primary-500 text-white'
          : 'bg-surface-overlay text-gray-400 hover:text-white hover:bg-white/10'
      }`}
    >
      {label}
    </button>
  )
}
