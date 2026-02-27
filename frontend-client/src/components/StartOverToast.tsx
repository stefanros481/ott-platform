import { useEffect, useState } from 'react'

interface StartOverToastProps {
  programTitle: string
  elapsedSeconds: number
  onAccept: () => void
  onDismiss: () => void
}

function formatElapsed(seconds: number): string {
  const m = Math.floor(seconds / 60)
  if (m < 60) return `${m} min`
  const h = Math.floor(m / 60)
  const rm = m % 60
  return rm > 0 ? `${h}h ${rm}m` : `${h}h`
}

export default function StartOverToast({
  programTitle,
  elapsedSeconds,
  onAccept,
  onDismiss,
}: StartOverToastProps) {
  const [countdown, setCountdown] = useState(10)

  useEffect(() => {
    if (countdown <= 0) {
      onDismiss()
      return
    }
    const timer = setTimeout(() => setCountdown(c => c - 1), 1000)
    return () => clearTimeout(timer)
  }, [countdown, onDismiss])

  return (
    <div className="absolute bottom-20 left-6 z-50 bg-surface-raised/95 backdrop-blur border border-white/10 rounded-xl p-5 max-w-sm shadow-2xl animate-in slide-in-from-bottom-4 duration-300">
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 w-10 h-10 rounded-full bg-primary-500/20 flex items-center justify-center">
          <svg className="w-5 h-5 text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12.75 15l3-3m0 0l-3-3m3 3h-7.5M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-white font-medium text-sm truncate">{programTitle}</p>
          <p className="text-gray-400 text-xs mt-0.5">
            Started {formatElapsed(elapsedSeconds)} ago
          </p>
        </div>
      </div>

      <div className="mt-4 flex gap-2">
        <button
          onClick={onAccept}
          className="flex-1 px-4 py-2.5 text-sm font-medium bg-primary-500 text-white rounded-lg hover:bg-primary-400 transition-colors"
        >
          Start from Beginning
        </button>
        <button
          onClick={onDismiss}
          className="px-4 py-2.5 text-sm font-medium text-gray-400 bg-white/5 rounded-lg hover:bg-white/10 hover:text-gray-200 transition-colors"
        >
          Live ({countdown}s)
        </button>
      </div>

      {/* Countdown progress bar */}
      <div className="mt-3 h-0.5 bg-white/10 rounded-full overflow-hidden">
        <div
          className="h-full bg-primary-500/50 transition-all duration-1000 ease-linear"
          style={{ width: `${(countdown / 10) * 100}%` }}
        />
      </div>
    </div>
  )
}
