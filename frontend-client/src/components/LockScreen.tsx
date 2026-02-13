import { useState, useRef, useEffect, useCallback } from 'react'
import { verifyPin, grantExtraTime } from '../api/parentalControls'

interface LockScreenProps {
  profileId: string
  nextResetAt: string | null
  onUnlocked: () => void
}

type GrantPreset = { label: string; minutes: number | null }

const GRANT_PRESETS: GrantPreset[] = [
  { label: '+15 min', minutes: 15 },
  { label: '+30 min', minutes: 30 },
  { label: '+1 hour', minutes: 60 },
  { label: 'Unlimited for today', minutes: null },
]

const ACTIVITIES = [
  'Read a book or comic',
  'Play outside or do some exercise',
  'Draw, paint, or build something',
  'Play a board game with family',
]

function formatResetTime(isoString: string | null): string {
  if (!isoString) return ''
  try {
    const date = new Date(isoString)
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  } catch {
    return ''
  }
}

export default function LockScreen({ profileId, nextResetAt, onUnlocked }: LockScreenProps) {
  const [showPinEntry, setShowPinEntry] = useState(false)
  const [pin, setPin] = useState(['', '', '', ''])
  const [pinError, setPinError] = useState<string | null>(null)
  const [pinVerified, setPinVerified] = useState(false)
  const [pinToken, setPinToken] = useState<string | null>(null)
  const [granting, setGranting] = useState(false)
  const [grantSuccess, setGrantSuccess] = useState<string | null>(null)

  const inputRefs = useRef<(HTMLInputElement | null)[]>([])

  // Focus first input when PIN entry opens
  useEffect(() => {
    if (showPinEntry && !pinVerified) {
      setTimeout(() => inputRefs.current[0]?.focus(), 100)
    }
  }, [showPinEntry, pinVerified])

  const handlePinChange = useCallback(
    (index: number, value: string) => {
      if (!/^\d*$/.test(value)) return
      const digit = value.slice(-1)
      const newPin = [...pin]
      newPin[index] = digit
      setPin(newPin)
      setPinError(null)

      if (digit && index < 3) {
        inputRefs.current[index + 1]?.focus()
      }

      // Auto-submit when all 4 digits entered
      if (digit && index === 3 && newPin.every((d) => d !== '')) {
        handlePinSubmit(newPin.join(''))
      }
    },
    [pin],
  )

  const handleKeyDown = useCallback(
    (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === 'Backspace' && !pin[index] && index > 0) {
        inputRefs.current[index - 1]?.focus()
      }
    },
    [pin],
  )

  const handlePinSubmit = async (pinCode: string) => {
    setPinError(null)
    try {
      const result = await verifyPin(pinCode)
      if (result.verified) {
        setPinVerified(true)
        setPinToken(result.pin_token)
      }
    } catch (err: unknown) {
      const error = err as { message?: string; status?: number }
      // M-09: Server no longer sends attempt count — show generic error
      const msg = error.message || 'Incorrect PIN'
      setPinError(msg)
      setPin(['', '', '', ''])
      setTimeout(() => inputRefs.current[0]?.focus(), 100)
    }
  }

  const handleGrant = async (preset: GrantPreset) => {
    setGranting(true)
    try {
      await grantExtraTime(profileId, preset.minutes, undefined, pinToken ?? undefined)
      setGrantSuccess(preset.label)
      setTimeout(() => {
        onUnlocked()
      }, 1000)
    } catch (err: unknown) {
      const error = err as { message?: string }
      setPinError(error.message || 'Failed to grant extra time')
    } finally {
      setGranting(false)
    }
  }

  const resetPinEntry = () => {
    setShowPinEntry(false)
    setPin(['', '', '', ''])
    setPinError(null)
    setPinVerified(false)
    setPinToken(null)
    setGrantSuccess(null)
  }

  const resetTime = formatResetTime(nextResetAt)

  return (
    <div className="fixed inset-0 z-[70] flex items-center justify-center bg-gradient-to-br from-indigo-900 via-purple-900 to-pink-900">
      {/* Background decoration */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-10 left-10 w-64 h-64 rounded-full bg-yellow-400/10 blur-3xl" />
        <div className="absolute bottom-10 right-10 w-80 h-80 rounded-full bg-cyan-400/10 blur-3xl" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 rounded-full bg-purple-400/5 blur-3xl" />
      </div>

      <div className="relative z-10 text-center px-6 max-w-lg">
        {/* Big illustration placeholder */}
        <div className="text-8xl mb-6">&#127775;</div>

        <h1 className="text-3xl sm:text-4xl font-bold text-white mb-3">
          Great watching today!
        </h1>
        <p className="text-lg text-purple-200 mb-8">
          Time for something else. Here are some fun ideas:
        </p>

        {/* Activity suggestions */}
        <div className="grid grid-cols-2 gap-3 mb-8 max-w-sm mx-auto">
          {ACTIVITIES.map((activity, i) => (
            <div
              key={i}
              className="bg-white/10 backdrop-blur-sm rounded-xl p-3 text-sm text-purple-100 border border-white/10"
            >
              {activity}
            </div>
          ))}
        </div>

        {/* Reset time */}
        {resetTime && (
          <p className="text-sm text-purple-300 mb-6">
            Your time resets at <span className="font-semibold text-white">{resetTime}</span>
          </p>
        )}

        {/* Need more time button */}
        {!showPinEntry && (
          <button
            onClick={() => setShowPinEntry(true)}
            className="px-6 py-3 bg-white/15 hover:bg-white/25 text-white text-sm font-medium rounded-xl border border-white/20 backdrop-blur-sm transition-all"
          >
            Need more time? Ask a parent
          </button>
        )}

        {/* PIN entry modal */}
        {showPinEntry && !pinVerified && (
          <div className="mt-4 bg-surface-raised/90 backdrop-blur-md rounded-2xl p-6 border border-white/10 shadow-2xl max-w-xs mx-auto">
            <h3 className="text-lg font-semibold text-white mb-1">Parent PIN</h3>
            <p className="text-sm text-gray-400 mb-4">Enter the 4-digit parental PIN</p>

            <div className="flex justify-center gap-3 mb-4">
              {pin.map((digit, i) => (
                <input
                  key={i}
                  ref={(el) => { inputRefs.current[i] = el }}
                  type="password"
                  inputMode="numeric"
                  maxLength={1}
                  value={digit}
                  onChange={(e) => handlePinChange(i, e.target.value)}
                  onKeyDown={(e) => handleKeyDown(i, e)}
                  className="w-12 h-14 text-center text-xl font-bold text-white bg-surface-overlay border border-white/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
                />
              ))}
            </div>

            {pinError && (
              <p className="text-sm text-red-400 mb-2">
                {pinError}
              </p>
            )}

            <button
              onClick={resetPinEntry}
              className="text-sm text-gray-400 hover:text-white transition-colors"
            >
              Cancel
            </button>
          </div>
        )}

        {/* Grant presets (after PIN verified) */}
        {showPinEntry && pinVerified && !grantSuccess && (
          <div className="mt-4 bg-surface-raised/90 backdrop-blur-md rounded-2xl p-6 border border-white/10 shadow-2xl max-w-xs mx-auto">
            <h3 className="text-lg font-semibold text-white mb-1">
              Add More Time
            </h3>
            <p className="text-sm text-gray-400 mb-4">How much extra time?</p>

            <div className="flex flex-col gap-2">
              {GRANT_PRESETS.map((preset) => (
                <button
                  key={preset.label}
                  onClick={() => handleGrant(preset)}
                  disabled={granting}
                  className="w-full px-4 py-3 text-sm font-medium bg-white/10 hover:bg-white/20 text-white rounded-lg border border-white/10 transition-colors disabled:opacity-50"
                >
                  {preset.label}
                </button>
              ))}
            </div>

            {pinError && (
              <p className="text-sm text-red-400 mt-3">{pinError}</p>
            )}

            <button
              onClick={resetPinEntry}
              className="mt-3 text-sm text-gray-400 hover:text-white transition-colors"
            >
              Cancel
            </button>
          </div>
        )}

        {/* Grant success */}
        {grantSuccess && (
          <div className="mt-4 bg-emerald-900/50 backdrop-blur-md rounded-2xl p-6 border border-emerald-500/20 shadow-2xl max-w-xs mx-auto">
            <div className="text-4xl mb-2">&#9989;</div>
            <p className="text-emerald-100 font-medium">
              {grantSuccess} added!
            </p>
            <p className="text-sm text-emerald-300 mt-1">Resuming...</p>
          </div>
        )}
      </div>
    </div>
  )
}
