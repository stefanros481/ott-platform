interface ViewingTimeIndicatorProps {
  remainingMinutes: number | null
  hasLimits: boolean
  isUnlimitedOverride: boolean
}

function formatRemaining(minutes: number): string {
  if (minutes >= 60) {
    const h = Math.floor(minutes / 60)
    const m = minutes % 60
    return m > 0 ? `${h}h ${m}m left today` : `${h}h left today`
  }
  return `${minutes}m left today`
}

export default function ViewingTimeIndicator({
  remainingMinutes,
  hasLimits,
  isUnlimitedOverride,
}: ViewingTimeIndicatorProps) {
  // Hidden when no limits configured
  if (!hasLimits) return null

  // Show "Unlimited" for unlimited-override days
  if (isUnlimitedOverride || remainingMinutes === null) {
    return (
      <span className="text-xs text-gray-400 px-2 py-0.5 rounded-full bg-white/5">
        Unlimited
      </span>
    )
  }

  // Color based on remaining time
  let colorClass = 'text-gray-300 bg-white/5'
  if (remainingMinutes <= 15) {
    colorClass = 'text-red-400 bg-red-500/10'
  } else if (remainingMinutes <= 30) {
    colorClass = 'text-amber-400 bg-amber-500/10'
  }

  return (
    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${colorClass}`}>
      {formatRemaining(remainingMinutes)}
    </span>
  )
}
