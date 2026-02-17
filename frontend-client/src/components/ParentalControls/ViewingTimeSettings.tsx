import { useState, useEffect, useCallback, useRef } from 'react'
import {
  getViewingTimeConfig,
  updateViewingTimeConfig,
  verifyPin,
  type ViewingTimeConfig,
  type ViewingTimeConfigUpdate,
} from '../../api/parentalControls'
import type { Profile } from '../../api/auth'

interface ViewingTimeSettingsProps {
  profiles: Profile[]
}

// Sensitive fields that require PIN verification to change (matches backend SENSITIVE_FIELDS)
const SENSITIVE_FIELDS = new Set(['reset_hour', 'educational_exempt'])

// Generate dropdown options: 15min to 8h in 15-min steps, plus "Unlimited"
function buildLimitOptions(): { label: string; value: number | null }[] {
  const options: { label: string; value: number | null }[] = []
  for (let m = 15; m <= 480; m += 15) {
    const h = Math.floor(m / 60)
    const mins = m % 60
    let label: string
    if (h === 0) {
      label = `${mins} min`
    } else if (mins === 0) {
      label = `${h}h`
    } else {
      label = `${h}h ${mins}m`
    }
    options.push({ label, value: m })
  }
  options.push({ label: 'Unlimited', value: null })
  return options
}

const LIMIT_OPTIONS = buildLimitOptions()

const RESET_HOURS = Array.from({ length: 24 }, (_, i) => ({
  label: `${String(i).padStart(2, '0')}:00`,
  value: i,
}))

/** Build an update payload containing only fields that actually changed. */
function buildDiff(
  config: ViewingTimeConfig | null,
  weekdayLimit: number | null,
  weekendLimit: number | null,
  resetHour: number,
  educationalExempt: boolean,
): ViewingTimeConfigUpdate {
  const update: ViewingTimeConfigUpdate = {}
  if (weekdayLimit !== config?.weekday_limit_minutes) update.weekday_limit_minutes = weekdayLimit
  if (weekendLimit !== config?.weekend_limit_minutes) update.weekend_limit_minutes = weekendLimit
  if (resetHour !== config?.reset_hour) update.reset_hour = resetHour
  if (educationalExempt !== config?.educational_exempt) update.educational_exempt = educationalExempt
  const tz = Intl.DateTimeFormat().resolvedOptions().timeZone
  if (tz !== config?.timezone) update.timezone = tz
  return update
}

/** Check whether an update payload touches any sensitive field. */
function touchesSensitiveField(update: ViewingTimeConfigUpdate): boolean {
  return Object.keys(update).some((k) => SENSITIVE_FIELDS.has(k))
}

interface ProfileEditorProps {
  profile: Profile
}

function ProfileEditor({ profile }: ProfileEditorProps) {
  const [config, setConfig] = useState<ViewingTimeConfig | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  // Local form state
  const [weekdayLimit, setWeekdayLimit] = useState<number | null>(null)
  const [weekendLimit, setWeekendLimit] = useState<number | null>(null)
  const [resetHour, setResetHour] = useState(6)
  const [educationalExempt, setEducationalExempt] = useState(false)

  // PIN prompt state
  const [showPinPrompt, setShowPinPrompt] = useState(false)
  const [pin, setPin] = useState(['', '', '', ''])
  const [pinError, setPinError] = useState<string | null>(null)
  const pinRefs = useRef<(HTMLInputElement | null)[]>([])

  const loadConfig = useCallback(async () => {
    setLoading(true)
    try {
      const data = await getViewingTimeConfig(profile.id)
      setConfig(data)
      setWeekdayLimit(data.weekday_limit_minutes)
      setWeekendLimit(data.weekend_limit_minutes)
      setResetHour(data.reset_hour)
      setEducationalExempt(data.educational_exempt)
    } catch {
      // Config may not exist yet — use defaults
      setWeekdayLimit(null)
      setWeekendLimit(null)
      setResetHour(6)
      setEducationalExempt(false)
    } finally {
      setLoading(false)
    }
  }, [profile.id])

  useEffect(() => {
    loadConfig()
  }, [loadConfig])

  // Focus first PIN input when prompt opens
  useEffect(() => {
    if (showPinPrompt) {
      setTimeout(() => pinRefs.current[0]?.focus(), 100)
    }
  }, [showPinPrompt])

  /** Save with an optional pin_token (for sensitive field changes). */
  const doSave = async (pinToken?: string) => {
    setSaving(true)
    setError(null)
    setSuccess(false)
    try {
      const update = buildDiff(config, weekdayLimit, weekendLimit, resetHour, educationalExempt)
      if (pinToken) update.pin_token = pinToken
      const updated = await updateViewingTimeConfig(profile.id, update)
      setConfig(updated)
      setSuccess(true)
      setTimeout(() => setSuccess(false), 3000)
    } catch (err: unknown) {
      const e = err as { message?: string }
      setError(e.message || 'Failed to save settings')
    } finally {
      setSaving(false)
    }
  }

  const handleSave = () => {
    const update = buildDiff(config, weekdayLimit, weekendLimit, resetHour, educationalExempt)
    if (touchesSensitiveField(update)) {
      // Need PIN verification first
      setShowPinPrompt(true)
      setPin(['', '', '', ''])
      setPinError(null)
    } else {
      doSave()
    }
  }

  const handlePinChange = useCallback(
    (index: number, value: string) => {
      if (!/^\d*$/.test(value)) return
      const digit = value.slice(-1)
      const newPin = [...pin]
      newPin[index] = digit
      setPin(newPin)
      setPinError(null)

      if (digit && index < 3) {
        pinRefs.current[index + 1]?.focus()
      }

      // Auto-submit when all 4 digits entered
      if (digit && index === 3 && newPin.every((d) => d !== '')) {
        handlePinSubmit(newPin.join(''))
      }
    },
    [pin],
  )

  const handlePinKeyDown = useCallback(
    (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === 'Backspace' && !pin[index] && index > 0) {
        pinRefs.current[index - 1]?.focus()
      }
    },
    [pin],
  )

  const handlePinSubmit = async (pinCode: string) => {
    setPinError(null)
    try {
      const result = await verifyPin(pinCode)
      if (result.verified && result.pin_token) {
        setShowPinPrompt(false)
        doSave(result.pin_token)
      } else {
        setPinError('Incorrect PIN')
        setPin(['', '', '', ''])
        setTimeout(() => pinRefs.current[0]?.focus(), 100)
      }
    } catch (err: unknown) {
      const error = err as { message?: string }
      setPinError(error.message || 'Incorrect PIN')
      setPin(['', '', '', ''])
      setTimeout(() => pinRefs.current[0]?.focus(), 100)
    }
  }

  const cancelPinPrompt = () => {
    setShowPinPrompt(false)
    setPin(['', '', '', ''])
    setPinError(null)
  }

  // Adult profiles (not kids) are unlimited and cannot be changed
  if (!profile.is_kids) {
    return (
      <div className="bg-surface-overlay rounded-lg p-4 border border-white/5">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-primary-700 flex items-center justify-center text-xs font-bold text-white uppercase">
            {profile.name.charAt(0)}
          </div>
          <div>
            <p className="text-sm font-medium text-white">{profile.name}</p>
            <p className="text-xs text-gray-500">Unlimited (cannot be changed)</p>
          </div>
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="bg-surface-overlay rounded-lg p-4 border border-white/5 animate-pulse">
        <div className="h-4 bg-white/10 rounded w-32 mb-3" />
        <div className="h-8 bg-white/10 rounded w-full" />
      </div>
    )
  }

  const browserTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone
  const hasChanges =
    config === null ||
    weekdayLimit !== config.weekday_limit_minutes ||
    weekendLimit !== config.weekend_limit_minutes ||
    resetHour !== config.reset_hour ||
    educationalExempt !== config.educational_exempt ||
    browserTimezone !== config.timezone

  return (
    <div className="bg-surface-overlay rounded-lg p-4 border border-white/5 relative">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-8 h-8 rounded-full bg-amber-600 flex items-center justify-center text-xs font-bold text-white uppercase">
          {profile.name.charAt(0)}
        </div>
        <p className="text-sm font-medium text-white">{profile.name}</p>
        {profile.is_kids && (
          <span className="text-[10px] font-medium uppercase px-1.5 py-0.5 bg-amber-500/20 text-amber-400 rounded">
            Kids
          </span>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
        {/* Weekday limit */}
        <div>
          <label className="block text-xs font-medium text-gray-400 mb-1">
            Weekday Limit
          </label>
          <select
            value={weekdayLimit === null ? 'unlimited' : String(weekdayLimit)}
            onChange={(e) =>
              setWeekdayLimit(e.target.value === 'unlimited' ? null : Number(e.target.value))
            }
            className="w-full px-3 py-2 text-sm bg-surface border border-white/10 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            {LIMIT_OPTIONS.map((opt) => (
              <option key={opt.value ?? 'unlimited'} value={opt.value === null ? 'unlimited' : String(opt.value)}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        {/* Weekend limit */}
        <div>
          <label className="block text-xs font-medium text-gray-400 mb-1">
            Weekend Limit
          </label>
          <select
            value={weekendLimit === null ? 'unlimited' : String(weekendLimit)}
            onChange={(e) =>
              setWeekendLimit(e.target.value === 'unlimited' ? null : Number(e.target.value))
            }
            className="w-full px-3 py-2 text-sm bg-surface border border-white/10 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            {LIMIT_OPTIONS.map((opt) => (
              <option key={opt.value ?? 'unlimited'} value={opt.value === null ? 'unlimited' : String(opt.value)}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        {/* Reset hour */}
        <div>
          <label className="block text-xs font-medium text-gray-400 mb-1">
            Daily Reset Time
          </label>
          <select
            value={String(resetHour)}
            onChange={(e) => setResetHour(Number(e.target.value))}
            className="w-full px-3 py-2 text-sm bg-surface border border-white/10 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            {RESET_HOURS.map((opt) => (
              <option key={opt.value} value={String(opt.value)}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        {/* Educational exemption */}
        <div className="flex items-end">
          <label className="flex items-center gap-3 cursor-pointer pb-2">
            <input
              type="checkbox"
              checked={educationalExempt}
              onChange={(e) => setEducationalExempt(e.target.checked)}
              className="w-4 h-4 rounded border-white/20 bg-surface text-primary-500 focus:ring-primary-500 focus:ring-offset-0"
            />
            <span className="text-sm text-gray-300">
              Educational content exempt
            </span>
          </label>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <button
          onClick={handleSave}
          disabled={saving || !hasChanges}
          className="px-4 py-2 text-sm font-medium bg-primary-500 text-white rounded-lg hover:bg-primary-400 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {saving ? 'Saving...' : 'Save'}
        </button>
        {success && <span className="text-sm text-emerald-400">Saved</span>}
        {error && <span className="text-sm text-red-400">{error}</span>}
      </div>

      {/* PIN prompt overlay */}
      {showPinPrompt && (
        <div className="absolute inset-0 z-10 flex items-center justify-center bg-black/60 backdrop-blur-sm rounded-lg">
          <div className="bg-surface-raised rounded-xl p-6 border border-white/10 shadow-2xl max-w-xs w-full mx-4">
            <h3 className="text-lg font-semibold text-white mb-1">Parent PIN</h3>
            <p className="text-sm text-gray-400 mb-4">
              PIN required to change protected settings
            </p>

            <div className="flex justify-center gap-3 mb-4">
              {pin.map((digit, i) => (
                <input
                  key={i}
                  ref={(el) => { pinRefs.current[i] = el }}
                  type="password"
                  inputMode="numeric"
                  maxLength={1}
                  value={digit}
                  onChange={(e) => handlePinChange(i, e.target.value)}
                  onKeyDown={(e) => handlePinKeyDown(i, e)}
                  className="w-12 h-14 text-center text-xl font-bold text-white bg-surface-overlay border border-white/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
                />
              ))}
            </div>

            {pinError && (
              <p className="text-sm text-red-400 text-center mb-3">{pinError}</p>
            )}

            <button
              onClick={cancelPinPrompt}
              className="w-full text-sm text-gray-400 hover:text-white transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default function ViewingTimeSettings({ profiles }: ViewingTimeSettingsProps) {
  return (
    <div className="space-y-4">
      {profiles.map((profile) => (
        <ProfileEditor key={profile.id} profile={profile} />
      ))}
    </div>
  )
}
