import { useEffect, useState } from 'react'

interface ResumeToastProps {
  positionSeconds: number
  onRestart: () => void
  onDismiss: () => void
}

function formatTime(seconds: number): string {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
  return `${m}:${String(s).padStart(2, '0')}`
}

export default function ResumeToast({ positionSeconds, onRestart, onDismiss }: ResumeToastProps) {
  const [visible, setVisible] = useState(true)

  // Auto-dismiss after 3 seconds
  useEffect(() => {
    const timer = setTimeout(() => {
      setVisible(false)
      onDismiss()
    }, 3000)
    return () => clearTimeout(timer)
  }, [onDismiss])

  if (!visible) return null

  return (
    <div className="absolute bottom-24 left-1/2 -translate-x-1/2 z-50 bg-black/90 border border-white/10 rounded-lg px-5 py-3 shadow-2xl flex items-center gap-4">
      <p className="text-white text-sm">
        Resuming from <span className="font-semibold text-primary-400">{formatTime(positionSeconds)}</span>
      </p>
      <button
        onClick={() => {
          setVisible(false)
          onRestart()
        }}
        className="text-xs text-gray-400 hover:text-white transition-colors underline underline-offset-2"
      >
        Start from beginning
      </button>
    </div>
  )
}
