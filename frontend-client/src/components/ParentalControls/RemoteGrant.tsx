import { useState } from 'react'
import { grantExtraTime } from '../../api/parentalControls'
import { getBalance, type ViewingTimeBalance } from '../../api/viewingTime'

interface RemoteGrantProps {
  profileId: string
  profileName: string
}

type GrantPreset = { label: string; minutes: number | null }

const GRANT_PRESETS: GrantPreset[] = [
  { label: '+15 min', minutes: 15 },
  { label: '+30 min', minutes: 30 },
  { label: '+1 hour', minutes: 60 },
  { label: 'Unlimited', minutes: null },
]

export default function RemoteGrant({ profileId, profileName }: RemoteGrantProps) {
  const [granting, setGranting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [confirmResult, setConfirmResult] = useState<{
    granted: string
    balance: ViewingTimeBalance | null
  } | null>(null)

  const handleGrant = async (preset: GrantPreset) => {
    setGranting(true)
    setError(null)
    setConfirmResult(null)
    try {
      // No PIN needed — parent is already authenticated on parental controls page
      await grantExtraTime(profileId, preset.minutes)
      // Fetch updated balance
      let balance: ViewingTimeBalance | null = null
      try {
        balance = await getBalance(profileId)
      } catch {
        // Non-critical if balance fetch fails
      }
      setConfirmResult({ granted: preset.label, balance })
      setTimeout(() => setConfirmResult(null), 5000)
    } catch (err: unknown) {
      const e = err as { message?: string }
      setError(e.message || 'Failed to grant extra time')
    } finally {
      setGranting(false)
    }
  }

  return (
    <div className="bg-surface-overlay rounded-lg p-4 border border-white/5">
      <div className="flex items-center gap-3 mb-3">
        <div className="w-8 h-8 rounded-full bg-amber-600 flex items-center justify-center text-xs font-bold text-white uppercase">
          {profileName.charAt(0)}
        </div>
        <div>
          <p className="text-sm font-medium text-white">{profileName}</p>
          <p className="text-xs text-gray-500">Grant extra viewing time</p>
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        {GRANT_PRESETS.map((preset) => (
          <button
            key={preset.label}
            onClick={() => handleGrant(preset)}
            disabled={granting}
            className="px-3 py-1.5 text-xs font-medium bg-white/10 hover:bg-white/20 text-white rounded-lg border border-white/10 transition-colors disabled:opacity-50"
          >
            {preset.label}
          </button>
        ))}
      </div>

      {error && <p className="text-sm text-red-400 mt-2">{error}</p>}

      {confirmResult && (
        <div className="mt-3 p-3 bg-emerald-900/30 border border-emerald-500/20 rounded-lg">
          <p className="text-sm text-emerald-300">
            {confirmResult.granted} granted to {profileName}
          </p>
          {confirmResult.balance && confirmResult.balance.remaining_minutes !== null && (
            <p className="text-xs text-emerald-400 mt-1">
              Current balance: {confirmResult.balance.remaining_minutes} minutes remaining
            </p>
          )}
          {confirmResult.balance && confirmResult.balance.is_unlimited_override && (
            <p className="text-xs text-emerald-400 mt-1">
              Current balance: Unlimited for today
            </p>
          )}
        </div>
      )}
    </div>
  )
}
