import { useState, useEffect, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useAuth } from '../context/AuthContext'
import { getChannels, getSchedule, type Channel, type ScheduleEntry } from '../api/epg'
import EpgGrid from '../components/EpgGrid'

function formatDateParam(date: Date): string {
  return date.toISOString().split('T')[0]!
}

function formatDateLabel(date: Date): string {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const d = new Date(date)
  d.setHours(0, 0, 0, 0)
  const diff = Math.round((d.getTime() - today.getTime()) / (1000 * 60 * 60 * 24))
  if (diff === 0) return 'Today'
  if (diff === -1) return 'Yesterday'
  if (diff === 1) return 'Tomorrow'
  return d.toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' })
}

export default function EpgPage() {
  const { profile } = useAuth()
  const [selectedDate, setSelectedDate] = useState(new Date())
  const [currentTime, setCurrentTime] = useState(new Date())
  // Update current time every minute
  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 60000)
    return () => clearInterval(timer)
  }, [])

  // Date options: today +/- 3 days
  const dateOptions = useMemo(() => {
    const dates: Date[] = []
    for (let i = -3; i <= 3; i++) {
      const d = new Date()
      d.setDate(d.getDate() + i)
      d.setHours(0, 0, 0, 0)
      dates.push(d)
    }
    return dates
  }, [])

  const { data: channels, isLoading: channelsLoading } = useQuery({
    queryKey: ['channels', profile?.id],
    queryFn: () => getChannels(profile?.id),
  })

  // Fetch schedule for all channels when channels or date changes
  const dateStr = formatDateParam(selectedDate)

  const { data: scheduleData = {}, isLoading: scheduleLoading } = useQuery({
    queryKey: ['schedule', dateStr, channels?.map(c => c.id).join(',')],
    queryFn: async () => {
      if (!channels?.length) return {} as Record<string, ScheduleEntry[]>
      const results = await Promise.all(
        channels.map(async (ch) => {
          try {
            const schedule = await getSchedule(ch.id, dateStr)
            return { channelId: ch.id, schedule }
          } catch {
            return { channelId: ch.id, schedule: [] as ScheduleEntry[] }
          }
        })
      )
      const data: Record<string, ScheduleEntry[]> = {}
      results.forEach(r => {
        data[r.channelId] = r.schedule
      })
      return data
    },
    enabled: !!channels?.length,
  })

  const isLoading = channelsLoading || scheduleLoading

  const handleProgramClick = (_entry: ScheduleEntry, _channel: Channel) => {
    // In a full implementation, this could navigate to the program detail or start playback
  }

  return (
    <div className="h-screen pt-14 flex flex-col">
      {/* Date selector */}
      <div className="flex items-center gap-2 px-4 py-3 bg-surface border-b border-white/5 overflow-x-auto shrink-0" style={{ scrollbarWidth: 'none' }}>
        {dateOptions.map(date => {
          const isSelected = formatDateParam(date) === formatDateParam(selectedDate)
          return (
            <button
              key={date.toISOString()}
              onClick={() => setSelectedDate(date)}
              className={`px-4 py-2 text-sm font-medium rounded-lg whitespace-nowrap transition-colors ${
                isSelected
                  ? 'bg-primary-500 text-white'
                  : 'bg-surface-raised text-gray-400 hover:text-white hover:bg-surface-overlay'
              }`}
            >
              {formatDateLabel(date)}
            </button>
          )
        })}
      </div>

      {/* EPG Grid */}
      <div className="flex-1 relative overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center h-full">
            <div className="flex flex-col items-center gap-4">
              <svg className="w-10 h-10 animate-spin text-primary-500" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              <p className="text-gray-400">Loading TV Guide...</p>
            </div>
          </div>
        ) : channels && channels.length > 0 ? (
          <EpgGrid
            channels={channels}
            scheduleData={scheduleData}
            currentTime={currentTime}
            onProgramClick={handleProgramClick}
          />
        ) : (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <svg className="w-16 h-16 text-gray-600 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 20.25h12m-7.5-3v3m3-3v3m-10.125-3h17.25c.621 0 1.125-.504 1.125-1.125V4.875c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125Z" />
              </svg>
              <p className="text-gray-400 text-lg">No channels available</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
