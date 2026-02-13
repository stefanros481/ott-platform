import { useState, useEffect } from 'react'
import { getBalance, type ViewingTimeBalance } from '../../api/viewingTime'

interface ProfileSummaryCardProps {
  profileId: string
  profileName: string
  isKids: boolean
  onEditLimits?: () => void
  onViewHistory?: () => void
  onGrantTime?: () => void
}

function formatDuration(minutes: number): string {
  if (minutes < 60) return `${minutes}m`
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  return m > 0 ? `${h}h ${m}m` : `${h}h`
}

export default function ProfileSummaryCard({
  profileId,
  profileName,
  isKids,
  onEditLimits,
  onViewHistory,
  onGrantTime,
}: ProfileSummaryCardProps) {
  const [balance, setBalance] = useState<ViewingTimeBalance | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      try {
        const data = await getBalance(profileId)
        setBalance(data)
      } catch {
        // Silently handle
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [profileId])

  if (loading) {
    return (
      <div className="bg-surface-overlay rounded-lg p-4 border border-white/5 animate-pulse">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-10 h-10 rounded-full bg-white/10" />
          <div className="h-4 bg-white/10 rounded w-24" />
        </div>
        <div className="h-3 bg-white/10 rounded w-full mb-2" />
        <div className="h-3 bg-white/10 rounded w-2/3" />
      </div>
    )
  }

  const hasLimits = balance?.has_limits ?? false
  const usedMinutes = balance?.used_minutes ?? 0
  const limitMinutes = balance?.limit_minutes ?? null
  const remainingMinutes = balance?.remaining_minutes ?? null
  const isUnlimited = balance?.is_unlimited_override ?? false

  // Derive status
  let statusLabel = 'Idle'
  let statusColor = 'bg-gray-500'
  if (balance) {
    if (!hasLimits || isUnlimited) {
      statusLabel = 'Unlimited'
      statusColor = 'bg-gray-500'
    } else if (remainingMinutes !== null && remainingMinutes <= 0) {
      statusLabel = 'Locked'
      statusColor = 'bg-red-500'
    } else if (remainingMinutes !== null && remainingMinutes <= 15) {
      statusLabel = 'Low time'
      statusColor = 'bg-amber-500'
    } else {
      statusLabel = 'Active'
      statusColor = 'bg-emerald-500'
    }
  }

  const progressPct = limitMinutes && limitMinutes > 0 ? Math.min((usedMinutes / limitMinutes) * 100, 100) : 0
  let barColor = 'bg-primary-500'
  if (progressPct >= 90) barColor = 'bg-red-500'
  else if (progressPct >= 70) barColor = 'bg-amber-500'

  return (
    <div className="bg-surface-overlay rounded-lg p-4 border border-white/5">
      {/* Header */}
      <div className="flex items-center gap-3 mb-3">
        <div className="w-10 h-10 rounded-full bg-amber-600 flex items-center justify-center text-sm font-bold text-white uppercase">
          {profileName.charAt(0)}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <p className="text-sm font-medium text-white truncate">{profileName}</p>
            {isKids && (
              <span className="text-[10px] font-medium uppercase px-1.5 py-0.5 bg-amber-500/20 text-amber-400 rounded shrink-0">
                Kids
              </span>
            )}
          </div>
          <div className="flex items-center gap-1.5 mt-0.5">
            <div className={`w-1.5 h-1.5 rounded-full ${statusColor}`} />
            <span className="text-xs text-gray-500">{statusLabel}</span>
          </div>
        </div>
      </div>

      {/* Usage bar */}
      {hasLimits && !isUnlimited && limitMinutes && (
        <div className="mb-3">
          <div className="flex justify-between text-xs text-gray-500 mb-1">
            <span>Used: {formatDuration(usedMinutes)}</span>
            <span>Limit: {formatDuration(limitMinutes)}</span>
          </div>
          <div className="h-2 bg-white/10 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all ${barColor}`}
              style={{ width: `${Math.max(progressPct, 1)}%` }}
            />
          </div>
          {remainingMinutes !== null && (
            <p className="text-xs text-gray-500 mt-1">
              {remainingMinutes > 0
                ? `${formatDuration(remainingMinutes)} remaining`
                : 'Time limit reached'}
            </p>
          )}
        </div>
      )}

      {!hasLimits && (
        <p className="text-xs text-gray-500 mb-3">No limits configured</p>
      )}

      {isUnlimited && hasLimits && (
        <p className="text-xs text-gray-500 mb-3">Unlimited override active</p>
      )}

      {/* Quick links */}
      {isKids && (
        <div className="flex flex-wrap gap-2">
          {onEditLimits && (
            <button
              onClick={onEditLimits}
              className="text-xs text-primary-400 hover:text-primary-300 transition-colors"
            >
              Edit Limits
            </button>
          )}
          {onViewHistory && (
            <button
              onClick={onViewHistory}
              className="text-xs text-primary-400 hover:text-primary-300 transition-colors"
            >
              View History
            </button>
          )}
          {onGrantTime && (
            <button
              onClick={onGrantTime}
              className="text-xs text-primary-400 hover:text-primary-300 transition-colors"
            >
              Grant Time
            </button>
          )}
        </div>
      )}
    </div>
  )
}
