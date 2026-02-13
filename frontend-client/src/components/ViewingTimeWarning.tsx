import { useEffect, useState, useCallback } from 'react'

interface ViewingTimeWarningProps {
  showWarning15: boolean
  showWarning5: boolean
  onDismiss15: () => void
  onDismiss5: () => void
  /** Actual remaining minutes to display in the warning */
  remainingMinutes?: number | null
  /** When true, shows the educational exemption indicator instead of warnings */
  isEducational?: boolean
  /** Callback when educational indicator has been shown */
  onEducationalShown?: () => void
}

const AUTO_DISMISS_MS = 10_000
const EDUCATIONAL_DISMISS_MS = 5_000

export default function ViewingTimeWarning({
  showWarning15,
  showWarning5,
  onDismiss15,
  onDismiss5,
  remainingMinutes,
  isEducational,
  onEducationalShown,
}: ViewingTimeWarningProps) {
  const [showEducational, setShowEducational] = useState(false)
  const [educationalShownOnce, setEducationalShownOnce] = useState(false)

  // T031: Educational exemption indicator — show only once per session
  useEffect(() => {
    if (isEducational && !educationalShownOnce) {
      setShowEducational(true)
      setEducationalShownOnce(true)
      onEducationalShown?.()
      const timer = setTimeout(() => setShowEducational(false), EDUCATIONAL_DISMISS_MS)
      return () => clearTimeout(timer)
    }
  }, [isEducational, educationalShownOnce, onEducationalShown])

  // Auto-dismiss warning_15 after 10s
  useEffect(() => {
    if (!showWarning15) return
    const timer = setTimeout(onDismiss15, AUTO_DISMISS_MS)
    return () => clearTimeout(timer)
  }, [showWarning15, onDismiss15])

  // Auto-dismiss warning_5 after 10s
  useEffect(() => {
    if (!showWarning5) return
    const timer = setTimeout(onDismiss5, AUTO_DISMISS_MS)
    return () => clearTimeout(timer)
  }, [showWarning5, onDismiss5])

  const handleDismiss = useCallback(
    (level: 15 | 5) => {
      if (level === 15) onDismiss15()
      else onDismiss5()
    },
    [onDismiss15, onDismiss5],
  )

  // Educational indicator takes priority
  if (showEducational) {
    return (
      <div className="fixed top-20 left-1/2 -translate-x-1/2 z-[60] animate-fade-in">
        <div className="flex items-center gap-3 bg-emerald-900/90 border border-emerald-500/30 backdrop-blur-sm rounded-lg px-4 py-3 shadow-lg">
          <span className="text-emerald-400 text-lg">&#127891;</span>
          <p className="text-sm text-emerald-100">
            This doesn't count toward your daily limit
          </p>
        </div>
      </div>
    )
  }

  if (showWarning5) {
    return (
      <div className="fixed top-20 left-1/2 -translate-x-1/2 z-[60] animate-fade-in">
        <div className="flex items-center gap-3 bg-red-900/90 border border-red-500/30 backdrop-blur-sm rounded-lg px-4 py-3 shadow-lg max-w-md">
          <span className="text-red-400 text-xl">&#9200;</span>
          <div className="flex-1">
            <p className="text-sm font-medium text-red-100">
              {remainingMinutes != null ? Math.ceil(remainingMinutes) : 5} minutes left — ask a parent for more time
            </p>
          </div>
          <button
            onClick={() => handleDismiss(5)}
            className="p-1 text-red-400 hover:text-red-200 transition-colors"
            aria-label="Dismiss"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
    )
  }

  if (showWarning15) {
    return (
      <div className="fixed top-20 left-1/2 -translate-x-1/2 z-[60] animate-fade-in">
        <div className="flex items-center gap-3 bg-amber-900/80 border border-amber-500/30 backdrop-blur-sm rounded-lg px-4 py-3 shadow-lg max-w-md">
          <span className="text-amber-400 text-lg">&#9201;</span>
          <div className="flex-1">
            <p className="text-sm text-amber-100">
              {remainingMinutes != null ? Math.ceil(remainingMinutes) : 15} minutes of viewing time left today
            </p>
          </div>
          <button
            onClick={() => handleDismiss(15)}
            className="p-1 text-amber-400 hover:text-amber-200 transition-colors"
            aria-label="Dismiss"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
    )
  }

  return null
}
