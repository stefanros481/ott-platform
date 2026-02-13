import { useState, useRef, useEffect, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getProfiles } from '../api/auth'
import { verifyPin, createPin, resetPin } from '../api/parentalControls'
import ViewingTimeSettings from '../components/ParentalControls/ViewingTimeSettings'
import RemoteGrant from '../components/ParentalControls/RemoteGrant'
import ViewingHistory from '../components/ParentalControls/ViewingHistory'
import WeeklyReport from '../components/ParentalControls/WeeklyReport'
import ProfileSummaryCard from '../components/ParentalControls/ProfileSummaryCard'

type PageState = 'loading' | 'pin-setup' | 'pin-entry' | 'pin-reset' | 'authenticated'
type ActiveSection = 'overview' | 'limits' | 'history' | 'report' | 'grant'

export default function ParentalControlsPage() {
  const [pageState, setPageState] = useState<PageState>('loading')
  const [activeSection, setActiveSection] = useState<ActiveSection>('overview')
  const [selectedProfileId, setSelectedProfileId] = useState<string | null>(null)

  // PIN entry state
  const [pin, setPin] = useState(['', '', '', ''])
  const [pinError, setPinError] = useState<string | null>(null)
  const [lockedUntil, setLockedUntil] = useState<string | null>(null)

  // PIN setup state
  const [newPin, setNewPin] = useState(['', '', '', ''])
  const [confirmPin, setConfirmPin] = useState(['', '', '', ''])
  const [setupStep, setSetupStep] = useState<'enter' | 'confirm'>('enter')
  const [setupError, setSetupError] = useState<string | null>(null)
  const [setupSaving, setSetupSaving] = useState(false)

  // PIN reset state
  const [resetPassword, setResetPassword] = useState('')
  const [resetNewPin, setResetNewPin] = useState(['', '', '', ''])
  const [resetError, setResetError] = useState<string | null>(null)
  const [resetSaving, setResetSaving] = useState(false)

  const pinInputRefs = useRef<(HTMLInputElement | null)[]>([])
  const setupInputRefs = useRef<(HTMLInputElement | null)[]>([])
  const confirmInputRefs = useRef<(HTMLInputElement | null)[]>([])
  const resetPinInputRefs = useRef<(HTMLInputElement | null)[]>([])

  const { data: profiles } = useQuery({
    queryKey: ['profiles'],
    queryFn: getProfiles,
  })

  const childProfiles = profiles?.filter((p) => p.is_kids) ?? []

  // Check if PIN is set on load
  useEffect(() => {
    const checkPinStatus = async () => {
      try {
        // Try verifying an empty/dummy pin to detect if pin is set
        await verifyPin('0000')
        // If it succeeds (unlikely but possible), user is authenticated
        setPageState('authenticated')
      } catch (err: unknown) {
        const error = err as { message?: string; status?: number }
        const msg = error.message || ''
        // If the error says "No PIN set", show setup flow
        if (msg.toLowerCase().includes('no pin')) {
          setPageState('pin-setup')
        } else {
          // PIN exists but verification failed (expected for dummy pin) — show entry
          setPageState('pin-entry')
        }
      }
    }
    checkPinStatus()
  }, [])

  // Focus first pin input when entering pin-entry state
  useEffect(() => {
    if (pageState === 'pin-entry') {
      setTimeout(() => pinInputRefs.current[0]?.focus(), 100)
    } else if (pageState === 'pin-setup') {
      setTimeout(() => setupInputRefs.current[0]?.focus(), 100)
    } else if (pageState === 'pin-reset') {
      // Focus password field (handled by autoFocus on input)
    }
  }, [pageState, setupStep])

  // PIN digit handlers
  const handleDigitChange = (
    index: number,
    value: string,
    digits: string[],
    setDigits: (d: string[]) => void,
    refs: React.MutableRefObject<(HTMLInputElement | null)[]>,
    onComplete?: (code: string) => void,
  ) => {
    if (!/^\d*$/.test(value)) return
    const digit = value.slice(-1)
    const newDigits = [...digits]
    newDigits[index] = digit
    setDigits(newDigits)

    if (digit && index < 3) {
      refs.current[index + 1]?.focus()
    }

    if (digit && index === 3 && newDigits.every((d) => d !== '')) {
      onComplete?.(newDigits.join(''))
    }
  }

  const handleDigitKeyDown = (
    index: number,
    e: React.KeyboardEvent<HTMLInputElement>,
    digits: string[],
    refs: React.MutableRefObject<(HTMLInputElement | null)[]>,
  ) => {
    if (e.key === 'Backspace' && !digits[index] && index > 0) {
      refs.current[index - 1]?.focus()
    }
  }

  // PIN entry submit
  const handlePinVerify = useCallback(async (code: string) => {
    setPinError(null)
    try {
      const result = await verifyPin(code)
      if (result.verified) {
        setPageState('authenticated')
      }
    } catch (err: unknown) {
      const error = err as { message?: string }
      const msg = error.message || 'Incorrect PIN'
      // Try to parse structured error
      try {
        const parsed = JSON.parse(msg)
        setPinError(parsed.detail || msg)
        if (parsed.locked_until) {
          setLockedUntil(parsed.locked_until)
        }
      } catch {
        setPinError(msg)
      }
      setPin(['', '', '', ''])
      setTimeout(() => pinInputRefs.current[0]?.focus(), 100)
    }
  }, [])

  // PIN setup submit
  const handleSetupComplete = useCallback(
    async (code: string) => {
      if (setupStep === 'enter') {
        setNewPin(code.split(''))
        setSetupStep('confirm')
        setConfirmPin(['', '', '', ''])
        setTimeout(() => confirmInputRefs.current[0]?.focus(), 100)
        return
      }
      // Confirm step
      const entered = newPin.join('')
      if (code !== entered) {
        setSetupError('PINs do not match. Try again.')
        setSetupStep('enter')
        setNewPin(['', '', '', ''])
        setConfirmPin(['', '', '', ''])
        setTimeout(() => setupInputRefs.current[0]?.focus(), 100)
        return
      }
      setSetupSaving(true)
      setSetupError(null)
      try {
        await createPin(code)
        setPageState('authenticated')
      } catch (err: unknown) {
        const error = err as { message?: string }
        setSetupError(error.message || 'Failed to create PIN')
        setSetupStep('enter')
        setNewPin(['', '', '', ''])
        setConfirmPin(['', '', '', ''])
      } finally {
        setSetupSaving(false)
      }
    },
    [setupStep, newPin],
  )

  // PIN reset submit
  const handleResetSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const pinCode = resetNewPin.join('')
    if (pinCode.length !== 4) {
      setResetError('Enter a 4-digit PIN')
      return
    }
    setResetSaving(true)
    setResetError(null)
    try {
      await resetPin(resetPassword, pinCode)
      setPageState('authenticated')
    } catch (err: unknown) {
      const error = err as { message?: string }
      setResetError(error.message || 'Failed to reset PIN')
    } finally {
      setResetSaving(false)
    }
  }

  const scrollToSection = (section: ActiveSection, profileId?: string) => {
    setActiveSection(section)
    if (profileId) setSelectedProfileId(profileId)
  }

  // Render 4-digit PIN input
  const renderPinInputs = (
    digits: string[],
    setDigits: (d: string[]) => void,
    refs: React.MutableRefObject<(HTMLInputElement | null)[]>,
    onComplete?: (code: string) => void,
  ) => (
    <div className="flex justify-center gap-3">
      {digits.map((digit, i) => (
        <input
          key={i}
          ref={(el) => { refs.current[i] = el }}
          type="password"
          inputMode="numeric"
          maxLength={1}
          value={digit}
          onChange={(e) => handleDigitChange(i, e.target.value, digits, setDigits, refs, onComplete)}
          onKeyDown={(e) => handleDigitKeyDown(i, e, digits, refs)}
          className="w-14 h-16 text-center text-2xl font-bold text-white bg-surface-overlay border border-white/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
        />
      ))}
    </div>
  )

  // ── Loading state ──
  if (pageState === 'loading') {
    return (
      <div className="min-h-screen bg-surface pt-20 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <svg className="w-8 h-8 animate-spin text-primary-500" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <p className="text-gray-400 text-sm">Checking parental controls...</p>
        </div>
      </div>
    )
  }

  // ── PIN Setup (first-time) ──
  if (pageState === 'pin-setup') {
    return (
      <div className="min-h-screen bg-surface pt-20 flex items-center justify-center px-4">
        <div className="bg-surface-raised rounded-xl p-8 max-w-sm w-full border border-white/10 shadow-2xl text-center">
          <div className="text-4xl mb-4">&#128274;</div>
          <h1 className="text-xl font-bold text-white mb-2">Set Up Parental Controls</h1>
          <p className="text-sm text-gray-400 mb-6">
            {setupStep === 'enter'
              ? 'Create a 4-digit PIN to protect parental settings.'
              : 'Confirm your PIN.'}
          </p>

          {setupStep === 'enter'
            ? renderPinInputs(newPin, setNewPin, setupInputRefs, (code) => handleSetupComplete(code))
            : renderPinInputs(confirmPin, setConfirmPin, confirmInputRefs, (code) => handleSetupComplete(code))}

          {setupError && <p className="text-sm text-red-400 mt-4">{setupError}</p>}
          {setupSaving && <p className="text-sm text-gray-400 mt-4">Creating PIN...</p>}
        </div>
      </div>
    )
  }

  // ── PIN Entry ──
  if (pageState === 'pin-entry') {
    return (
      <div className="min-h-screen bg-surface pt-20 flex items-center justify-center px-4">
        <div className="bg-surface-raised rounded-xl p-8 max-w-sm w-full border border-white/10 shadow-2xl text-center">
          <div className="text-4xl mb-4">&#128274;</div>
          <h1 className="text-xl font-bold text-white mb-2">Parental Controls</h1>
          <p className="text-sm text-gray-400 mb-6">Enter your 4-digit PIN to continue</p>

          {lockedUntil ? (
            <div>
              <p className="text-sm text-red-400 mb-2">Too many attempts. Try again later.</p>
              <p className="text-xs text-gray-500">
                Locked until {new Date(lockedUntil).toLocaleTimeString()}
              </p>
            </div>
          ) : (
            <>
              {renderPinInputs(pin, setPin, pinInputRefs, handlePinVerify)}
              {pinError && <p className="text-sm text-red-400 mt-4">{pinError}</p>}
            </>
          )}

          <button
            onClick={() => setPageState('pin-reset')}
            className="mt-6 text-sm text-primary-400 hover:text-primary-300 transition-colors"
          >
            Forgot PIN?
          </button>
        </div>
      </div>
    )
  }

  // ── PIN Reset ──
  if (pageState === 'pin-reset') {
    return (
      <div className="min-h-screen bg-surface pt-20 flex items-center justify-center px-4">
        <div className="bg-surface-raised rounded-xl p-8 max-w-sm w-full border border-white/10 shadow-2xl">
          <h1 className="text-xl font-bold text-white mb-2 text-center">Reset PIN</h1>
          <p className="text-sm text-gray-400 mb-6 text-center">
            Enter your account password and a new 4-digit PIN.
          </p>

          <form onSubmit={handleResetSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1.5">
                Account Password
              </label>
              <input
                type="password"
                value={resetPassword}
                onChange={(e) => setResetPassword(e.target.value)}
                required
                autoFocus
                className="w-full px-4 py-2.5 rounded-lg bg-surface-overlay border border-white/10 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500"
                placeholder="Enter your password"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1.5">
                New PIN
              </label>
              {renderPinInputs(resetNewPin, setResetNewPin, resetPinInputRefs)}
            </div>

            {resetError && <p className="text-sm text-red-400">{resetError}</p>}

            <div className="flex gap-3 pt-2">
              <button
                type="button"
                onClick={() => {
                  setPageState('pin-entry')
                  setResetPassword('')
                  setResetNewPin(['', '', '', ''])
                  setResetError(null)
                }}
                className="flex-1 py-2.5 text-sm font-medium text-gray-300 bg-surface-overlay rounded-lg hover:bg-white/10 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={resetSaving || !resetPassword || resetNewPin.some((d) => !d)}
                className="flex-1 py-2.5 text-sm font-semibold text-white bg-primary-500 rounded-lg hover:bg-primary-400 transition-colors disabled:opacity-50"
              >
                {resetSaving ? 'Resetting...' : 'Reset PIN'}
              </button>
            </div>
          </form>
        </div>
      </div>
    )
  }

  // ── Authenticated: Main Settings ──
  const sectionNav: { key: ActiveSection; label: string }[] = [
    { key: 'overview', label: 'Overview' },
    { key: 'limits', label: 'Time Limits' },
    { key: 'grant', label: 'Grant Time' },
    { key: 'history', label: 'History' },
    { key: 'report', label: 'Weekly Report' },
  ]

  return (
    <div className="min-h-screen bg-surface pt-20 pb-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-2xl font-bold text-white mb-1">Parental Controls</h1>
        <p className="text-sm text-gray-400 mb-6">
          Manage viewing time limits and monitor activity for child profiles.
        </p>

        {/* Section navigation */}
        <div className="flex gap-1 mb-8 overflow-x-auto border-b border-white/10 pb-px">
          {sectionNav.map(({ key, label }) => (
            <button
              key={key}
              onClick={() => setActiveSection(key)}
              className={`px-4 py-2 text-sm font-medium whitespace-nowrap transition-colors border-b-2 -mb-px ${
                activeSection === key
                  ? 'text-white border-primary-500'
                  : 'text-gray-500 border-transparent hover:text-gray-300'
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        {/* Overview section */}
        {activeSection === 'overview' && (
          <div>
            <h2 className="text-lg font-semibold text-white mb-4">Profile Overview</h2>
            {childProfiles.length === 0 ? (
              <p className="text-sm text-gray-500">
                No child profiles found. Create a kids profile in the profile selector to set up viewing limits.
              </p>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {childProfiles.map((profile) => (
                  <ProfileSummaryCard
                    key={profile.id}
                    profileId={profile.id}
                    profileName={profile.name}
                    isKids={profile.is_kids}
                    onEditLimits={() => scrollToSection('limits')}
                    onViewHistory={() => scrollToSection('history', profile.id)}
                    onGrantTime={() => scrollToSection('grant', profile.id)}
                  />
                ))}
              </div>
            )}
          </div>
        )}

        {/* Viewing Time Limits section */}
        {activeSection === 'limits' && profiles && (
          <div>
            <h2 className="text-lg font-semibold text-white mb-4">Viewing Time Limits</h2>
            <ViewingTimeSettings profiles={profiles} />
          </div>
        )}

        {/* Grant Time section */}
        {activeSection === 'grant' && (
          <div>
            <h2 className="text-lg font-semibold text-white mb-4">Grant Extra Time</h2>
            {childProfiles.length === 0 ? (
              <p className="text-sm text-gray-500">No child profiles to manage.</p>
            ) : (
              <div className="space-y-4">
                {childProfiles.map((profile) => (
                  <RemoteGrant
                    key={profile.id}
                    profileId={profile.id}
                    profileName={profile.name}
                  />
                ))}
              </div>
            )}
          </div>
        )}

        {/* History section */}
        {activeSection === 'history' && (
          <div>
            <h2 className="text-lg font-semibold text-white mb-4">Viewing History</h2>
            {childProfiles.length === 0 ? (
              <p className="text-sm text-gray-500">No child profiles to display.</p>
            ) : (
              <div className="space-y-8">
                {childProfiles
                  .filter((p) => !selectedProfileId || p.id === selectedProfileId)
                  .map((profile) => (
                    <ViewingHistory
                      key={profile.id}
                      profileId={profile.id}
                      profileName={profile.name}
                    />
                  ))}
                {selectedProfileId && (
                  <button
                    onClick={() => setSelectedProfileId(null)}
                    className="text-sm text-primary-400 hover:text-primary-300 transition-colors"
                  >
                    Show all profiles
                  </button>
                )}
              </div>
            )}
          </div>
        )}

        {/* Weekly Report section */}
        {activeSection === 'report' && (
          <div>
            <h2 className="text-lg font-semibold text-white mb-4">Weekly Report</h2>
            <WeeklyReport />
          </div>
        )}
      </div>
    </div>
  )
}
