import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import {
  fetchTSTVChannels,
  listCatchUpPrograms,
  listCatchUpByDate,
  type CatchUpProgram,
} from '../api/tstv'

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString(undefined, {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
  })
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

function getDateTabs(): { label: string; value: string }[] {
  const tabs = []
  const now = new Date()
  for (let i = 0; i < 8; i++) {
    const d = new Date(now)
    d.setDate(d.getDate() - i)
    const iso = d.toISOString().split('T')[0]!
    const label = i === 0 ? 'Today' : i === 1 ? 'Yesterday' : formatDate(iso)
    tabs.push({ label, value: iso })
  }
  return tabs
}

type BrowseMode = 'by-channel' | 'by-date'

export default function CatchUpPage() {
  const navigate = useNavigate()
  const [browseMode, setBrowseMode] = useState<BrowseMode>('by-channel')
  const [selectedChannelId, setSelectedChannelId] = useState<string | null>(null)
  const [selectedDate, setSelectedDate] = useState(getDateTabs()[0]!.value)

  const { data: channels } = useQuery({
    queryKey: ['tstv-channels'],
    queryFn: fetchTSTVChannels,
  })

  // By Channel mode — programs for selected channel
  const { data: channelPrograms, isLoading: channelLoading, error: channelError } = useQuery({
    queryKey: ['catchup-channel', selectedChannelId],
    queryFn: () => listCatchUpPrograms(selectedChannelId!, 100),
    enabled: browseMode === 'by-channel' && !!selectedChannelId,
  })

  // By Date mode — programs across all channels
  const { data: datePrograms, isLoading: dateLoading, error: dateError } = useQuery({
    queryKey: ['catchup-date', selectedDate],
    queryFn: () => listCatchUpByDate(selectedDate),
    enabled: browseMode === 'by-date',
  })

  const handlePlayProgram = (program: CatchUpProgram) => {
    const channelId = program.schedule_entry.channel_id
    navigate(`/play/live/${channelId}`, {
      state: {
        catchupMode: true,
        scheduleEntryId: program.schedule_entry.id,
        channelId,
      },
    })
  }

  const isExpiringSoon = (expiresAt: string) => {
    const hoursLeft = (new Date(expiresAt).getTime() - Date.now()) / (1000 * 60 * 60)
    return hoursLeft < 24
  }

  const dateTabs = getDateTabs()
  const programs = browseMode === 'by-channel' ? channelPrograms?.programs : datePrograms?.programs
  const isLoading = browseMode === 'by-channel' ? channelLoading : dateLoading
  const error = browseMode === 'by-channel' ? channelError : dateError

  return (
    <div className="min-h-screen bg-background pt-20 pb-10 px-4 sm:px-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-2xl font-bold text-white mb-6">Catch-Up TV</h1>

        {/* Browse mode toggle */}
        <div className="flex gap-2 mb-6">
          <button
            onClick={() => setBrowseMode('by-channel')}
            className={`px-4 py-2 text-sm rounded-lg transition-colors ${
              browseMode === 'by-channel'
                ? 'bg-primary-500 text-white'
                : 'bg-white/10 text-gray-400 hover:bg-white/20'
            }`}
          >
            By Channel
          </button>
          <button
            onClick={() => setBrowseMode('by-date')}
            className={`px-4 py-2 text-sm rounded-lg transition-colors ${
              browseMode === 'by-date'
                ? 'bg-primary-500 text-white'
                : 'bg-white/10 text-gray-400 hover:bg-white/20'
            }`}
          >
            By Date
          </button>
        </div>

        {/* Channel selector (By Channel mode) */}
        {browseMode === 'by-channel' && (
          <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
            {channels?.map((ch) => (
              <button
                key={ch.id}
                onClick={() => setSelectedChannelId(ch.id)}
                className={`flex-shrink-0 px-4 py-2 text-sm rounded-lg transition-colors ${
                  selectedChannelId === ch.id
                    ? 'bg-primary-500 text-white'
                    : 'bg-white/10 text-gray-300 hover:bg-white/20'
                }`}
              >
                {ch.name}
              </button>
            ))}
          </div>
        )}

        {/* Date tabs (By Date mode) */}
        {browseMode === 'by-date' && (
          <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
            {dateTabs.map((tab) => (
              <button
                key={tab.value}
                onClick={() => setSelectedDate(tab.value)}
                className={`flex-shrink-0 px-4 py-2 text-sm rounded-lg transition-colors ${
                  selectedDate === tab.value
                    ? 'bg-primary-500 text-white'
                    : 'bg-white/10 text-gray-300 hover:bg-white/20'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        )}

        {/* Programs list */}
        {browseMode === 'by-channel' && !selectedChannelId && (
          <div className="text-center py-16">
            <p className="text-gray-400">Select a channel to browse catch-up programs</p>
          </div>
        )}

        {isLoading && (
          <div className="flex justify-center py-16">
            <svg className="w-8 h-8 animate-spin text-primary-500" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          </div>
        )}

        {!isLoading && error && (
          <div className="text-center py-16">
            <svg className="w-12 h-12 text-red-400 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z" />
            </svg>
            <p className="text-gray-400">
              {(error as Error).message?.includes('403')
                ? 'Content no longer available'
                : 'Failed to load catch-up programs'}
            </p>
          </div>
        )}

        {!isLoading && !error && programs && programs.length === 0 && (
          <div className="text-center py-16">
            <p className="text-gray-400">
              {browseMode === 'by-channel'
                ? 'No catch-up programs available for this channel'
                : 'No catch-up programs available for this date'}
            </p>
          </div>
        )}

        {!isLoading && programs && programs.length > 0 && (
          <div className="space-y-2">
            {programs.map((program) => {
              const e = program.schedule_entry
              const expiring = isExpiringSoon(program.expires_at)
              return (
                <button
                  key={e.id}
                  onClick={() => handlePlayProgram(program)}
                  className="w-full flex items-center gap-4 p-4 bg-surface-raised/50 hover:bg-surface-raised border border-white/5 rounded-lg transition-colors text-left group"
                >
                  <div className="flex-shrink-0 w-12 h-12 bg-primary-500/20 rounded-lg flex items-center justify-center">
                    <svg className="w-6 h-6 text-primary-400 group-hover:text-primary-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.347a1.125 1.125 0 0 1 0 1.972l-11.54 6.347a1.125 1.125 0 0 1-1.667-.986V5.653Z" />
                    </svg>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-white font-medium text-sm truncate">{e.title}</p>
                    <p className="text-gray-500 text-xs mt-0.5">
                      {formatTime(e.start_time)} – {formatTime(e.end_time)} · {formatDuration(e.start_time, e.end_time)}
                      {e.genre && ` · ${e.genre}`}
                    </p>
                  </div>
                  <div className="flex-shrink-0 text-right">
                    {expiring ? (
                      <span className="px-2 py-1 text-xs font-medium bg-amber-500/20 text-amber-400 rounded">
                        Expires today
                      </span>
                    ) : (
                      <span className="text-xs text-gray-500">
                        Expires {formatDate(program.expires_at)}
                      </span>
                    )}
                  </div>
                </button>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
