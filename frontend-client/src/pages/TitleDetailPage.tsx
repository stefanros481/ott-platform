import { useState, useRef, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuth } from '../context/AuthContext'
import { getTitleById, type AccessOption } from '../api/catalog'
import { getSimilarTitles } from '../api/recommendations'
import { rateTitle, getRating, addToWatchlist, removeFromWatchlist, getWatchlist } from '../api/viewing'
import { purchaseTitle } from '../api/entitlements'
import { verifyPin } from '../api/parentalControls'
import { upgradeSubscription } from '../api/auth'
import ContentRail from '../components/ContentRail'
import TitleCard from '../components/TitleCard'

// ── Helpers ──────────────────────────────────────────────────────────────────

function formatPrice(priceCents: number, currency: string): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency.toUpperCase(),
  }).format(priceCents / 100)
}

function formatExpiresAt(isoString: string): string {
  return new Date(isoString).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

// ── Purchase confirmation modal ───────────────────────────────────────────────

interface PurchaseModalProps {
  titleName: string
  offer: AccessOption
  onConfirm: () => void
  onCancel: () => void
  isPending: boolean
}

function PurchaseModal({ titleName, offer, onConfirm, onCancel, isPending }: PurchaseModalProps) {
  const price = offer.price_cents != null && offer.currency
    ? formatPrice(offer.price_cents, offer.currency)
    : null

  const windowLabel = offer.rental_window_hours
    ? `${offer.rental_window_hours}-hour rental window`
    : null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 px-4">
      <div className="w-full max-w-sm rounded-xl border border-white/10 bg-surface-raised p-6 shadow-2xl">
        <h2 className="mb-1 text-lg font-semibold text-white">
          {offer.type === 'rent' ? 'Rent' : 'Buy'} "{titleName}"
        </h2>

        {price && (
          <p className="mb-1 text-2xl font-bold text-white">{price}</p>
        )}

        {windowLabel && (
          <p className="mb-4 text-sm text-gray-400">{windowLabel}</p>
        )}

        {!windowLabel && (
          <p className="mb-4 text-sm text-gray-400">Own this title permanently.</p>
        )}

        <div className="flex flex-col gap-3">
          <button
            onClick={onConfirm}
            disabled={isPending}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary-600 px-4 py-3 text-sm font-semibold text-white transition-colors hover:bg-primary-500 disabled:opacity-60"
          >
            {isPending ? (
              <>
                <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Processing...
              </>
            ) : (
              `Confirm ${offer.type === 'rent' ? 'Rental' : 'Purchase'}`
            )}
          </button>
          <button
            onClick={onCancel}
            disabled={isPending}
            className="w-full rounded-lg px-4 py-3 text-sm font-medium text-gray-400 transition-colors hover:text-white disabled:opacity-60"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  )
}

// ── Upgrade PIN confirmation modal ────────────────────────────────────────────

interface UpgradePinModalProps {
  requiredTier: string
  requiredTierLabel: string
  onSuccess: () => void
  onClose: () => void
}

function UpgradePinModal({ requiredTier, requiredTierLabel, onSuccess, onClose }: UpgradePinModalProps) {
  const [pin, setPin] = useState(['', '', '', ''])
  const [pinError, setPinError] = useState<string | null>(null)
  const [isVerifying, setIsVerifying] = useState(false)
  const [isUpgrading, setIsUpgrading] = useState(false)
  const [upgraded, setUpgraded] = useState(false)
  const inputRefs = useRef<(HTMLInputElement | null)[]>([])

  useEffect(() => {
    setTimeout(() => inputRefs.current[0]?.focus(), 100)
  }, [])

  const handlePinChange = (index: number, value: string) => {
    if (!/^\d*$/.test(value)) return
    const digit = value.slice(-1)
    const newPin = [...pin]
    newPin[index] = digit
    setPin(newPin)
    setPinError(null)

    if (digit && index < 3) {
      inputRefs.current[index + 1]?.focus()
    }

    if (digit && index === 3 && newPin.every(d => d !== '')) {
      submitPin(newPin.join(''))
    }
  }

  const handleKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Backspace' && !pin[index] && index > 0) {
      inputRefs.current[index - 1]?.focus()
    }
  }

  const submitPin = async (pinCode: string) => {
    setIsVerifying(true)
    setPinError(null)
    try {
      const result = await verifyPin(pinCode)
      if (result.verified) {
        setIsUpgrading(true)
        await upgradeSubscription(requiredTier)
        setUpgraded(true)
        onSuccess()
      }
    } catch (err: unknown) {
      const error = err as { message?: string }
      const isWrongPin = !isUpgrading
      setPinError(isWrongPin ? (error.message || 'Incorrect PIN') : 'Upgrade failed. Please try again.')
      setPin(['', '', '', ''])
      setIsUpgrading(false)
      setTimeout(() => inputRefs.current[0]?.focus(), 100)
    } finally {
      setIsVerifying(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 px-4">
      <div className="w-full max-w-sm rounded-xl border border-white/10 bg-surface-raised p-6 shadow-2xl">
        {!upgraded ? (
          <>
            <h2 className="mb-1 text-lg font-semibold text-white">Confirm with PIN</h2>
            <p className="mb-5 text-sm text-gray-400">
              Enter your 4-digit PIN to upgrade to the{' '}
              <span className="font-medium text-white">{requiredTierLabel} Plan</span>.
            </p>

            <div className="flex justify-center gap-3 mb-4">
              {pin.map((digit, i) => (
                <input
                  key={i}
                  ref={el => { inputRefs.current[i] = el }}
                  type="password"
                  inputMode="numeric"
                  maxLength={1}
                  value={digit}
                  onChange={e => handlePinChange(i, e.target.value)}
                  onKeyDown={e => handleKeyDown(i, e)}
                  disabled={isVerifying || isUpgrading}
                  className="w-12 h-14 text-center text-xl font-bold text-white bg-surface-overlay border border-white/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all disabled:opacity-50"
                />
              ))}
            </div>

            {isUpgrading && (
              <p className="mb-4 text-center text-sm text-gray-400">Activating subscription…</p>
            )}

            {pinError && (
              <p className="mb-4 text-center text-sm text-red-400">{pinError}</p>
            )}

            <button
              onClick={onClose}
              disabled={isVerifying || isUpgrading}
              className="w-full rounded-lg px-4 py-3 text-sm font-medium text-gray-400 transition-colors hover:text-white disabled:opacity-60"
            >
              Cancel
            </button>
          </>
        ) : (
          <>
            <div className="mb-5 text-center">
              <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-green-500/20">
                <svg className="h-6 w-6 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
                </svg>
              </div>
              <h2 className="text-lg font-semibold text-white">Subscription Upgraded!</h2>
              <p className="mt-2 text-sm text-gray-400">
                You now have access to the{' '}
                <span className="font-medium text-white">{requiredTierLabel} Plan</span>.
                Enjoy watching!
              </p>
            </div>

            <button
              onClick={onClose}
              className="w-full rounded-lg bg-primary-600 px-4 py-3 text-sm font-semibold text-white transition-colors hover:bg-primary-500"
            >
              Watch Now
            </button>
          </>
        )}
      </div>
    </div>
  )
}

// ── Simple inline toast ───────────────────────────────────────────────────────

interface ToastState {
  message: string
  type: 'success' | 'error'
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function TitleDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { profile, isAuthenticated } = useAuth()
  const queryClient = useQueryClient()
  const [selectedSeason, setSelectedSeason] = useState(1)
  const [pendingOffer, setPendingOffer] = useState<AccessOption | null>(null)
  const [showUpgradePinModal, setShowUpgradePinModal] = useState(false)
  const [toast, setToast] = useState<ToastState | null>(null)

  function showToast(message: string, type: 'success' | 'error') {
    setToast({ message, type })
    setTimeout(() => setToast(null), 4000)
  }

  const { data: title, isLoading, error: titleError } = useQuery({
    queryKey: ['title', id, profile?.id],
    queryFn: () => getTitleById(id!, profile?.id),
    enabled: !!id,
    retry: (failureCount, error: any) => {
      if (error?.status === 403) return false
      return failureCount < 3
    },
  })

  const { data: similar } = useQuery({
    queryKey: ['similar', id, profile?.id],
    queryFn: () => getSimilarTitles(id!, profile?.id),
    enabled: !!id,
  })

  const { data: watchlist } = useQuery({
    queryKey: ['watchlist', profile?.id],
    queryFn: () => getWatchlist(profile!.id),
    enabled: !!profile,
  })

  const { data: ratingData } = useQuery({
    queryKey: ['rating', profile?.id, id],
    queryFn: () => getRating(profile!.id, id!),
    enabled: !!profile && !!id,
  })

  const userRating = ratingData?.rating ?? null
  const isInWatchlist = watchlist?.some(w => w.title_id === id)

  const watchlistMutation = useMutation({
    mutationFn: () => isInWatchlist
      ? removeFromWatchlist(profile!.id, id!)
      : addToWatchlist(profile!.id, id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['watchlist'] })
      queryClient.invalidateQueries({ queryKey: ['recommendations', 'home'] })
    },
  })

  const rateMutation = useMutation({
    mutationFn: (rating: 1 | -1) => rateTitle(profile!.id, { title_id: id!, rating }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rating', profile?.id, id] })
    },
  })

  const purchaseMutation = useMutation({
    mutationFn: ({ offerType }: { offerType: 'rent' | 'buy' }) =>
      purchaseTitle(id!, offerType),
    onSuccess: (data) => {
      setPendingOffer(null)
      const label = data.offer_type === 'rent'
        ? 'Rental activated! You now have access.'
        : 'Purchase complete! Enjoy the title.'
      showToast(label, 'success')
      // Refetch title so user_access is updated and Play button becomes active
      queryClient.invalidateQueries({ queryKey: ['title', id] })
    },
    onError: () => {
      setPendingOffer(null)
      showToast('Purchase failed. Please try again.', 'error')
    },
  })

  const isRestricted = (titleError as any)?.status === 403

  if (isRestricted) {
    return (
      <div className="min-h-screen pt-14 flex flex-col items-center justify-center px-4">
        <svg className="w-20 h-20 text-gray-600 mb-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 1 0-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 0 0 2.25-2.25v-6.75a2.25 2.25 0 0 0-2.25-2.25H6.75a2.25 2.25 0 0 0-2.25 2.25v6.75a2.25 2.25 0 0 0 2.25 2.25Z" />
        </svg>
        <h2 className="text-xl font-semibold text-white mb-2">Content not available for this profile</h2>
        <p className="text-gray-400 text-sm mb-6">This title is restricted based on the current profile's parental rating.</p>
        <button
          onClick={() => navigate(-1)}
          className="px-6 py-2.5 bg-surface-overlay text-white rounded-lg hover:bg-white/10 transition-colors"
        >
          Go Back
        </button>
      </div>
    )
  }

  if (isLoading || !title) {
    return (
      <div className="min-h-screen pt-14">
        <div className="relative w-full h-[50vh] bg-surface-raised animate-pulse" />
        <div className="max-w-screen-xl mx-auto px-4 sm:px-6 lg:px-8 -mt-20 relative z-10 space-y-4">
          <div className="h-10 w-80 bg-surface-overlay rounded animate-pulse" />
          <div className="h-5 w-60 bg-surface-overlay rounded animate-pulse" />
          <div className="h-20 w-full max-w-2xl bg-surface-overlay rounded animate-pulse" />
        </div>
      </div>
    )
  }

  const currentSeason = title.seasons.find(s => s.season_number === selectedSeason)

  // ── Access logic ─────────────────────────────────────────────────────────────
  const userAccess = title.user_access
  const hasAccess = userAccess?.has_access === true || userAccess?.access_type === 'free'
  const isRental = userAccess?.access_type === 'tvod_rent'
  const accessOptions = title.access_options ?? []
  const rentOption = accessOptions.find(o => o.type === 'rent')
  const buyOption = accessOptions.find(o => o.type === 'buy')

  // Tier display helpers
  const TIER_LABEL: Record<string, string> = { basic: 'Basic', standard: 'Standard', premium: 'Premium' }
  const requiredTier = userAccess?.required_tier
  const requiredTierLabel = requiredTier ? TIER_LABEL[requiredTier] ?? requiredTier : null

  // "Included with …" label shown below the active Play button
  const inclusionLabel: string | null = (() => {
    if (!hasAccess) return null
    if (userAccess?.access_type === 'free') return 'Free to watch'
    if (userAccess?.access_type === 'tvod_buy') return 'Purchased'
    if (userAccess?.access_type === 'svod' && requiredTierLabel) return `Included with ${requiredTierLabel} Plan`
    if (userAccess?.access_type === 'svod') return 'Included with your plan'
    return null
  })()

  function handlePlay() {
    if (title.title_type === 'movie') {
      navigate(`/play/movie/${title.id}`)
    } else if (currentSeason?.episodes.length) {
      const firstEpisode = currentSeason.episodes[0]
      if (firstEpisode) {
        navigate(`/play/episode/${firstEpisode.id}`)
      }
    }
  }

  return (
    <div className="min-h-screen pt-14 pb-12">
      {/* Purchase confirmation modal */}
      {pendingOffer && (
        <PurchaseModal
          titleName={title.title}
          offer={pendingOffer}
          onConfirm={() => purchaseMutation.mutate({ offerType: pendingOffer.type as 'rent' | 'buy' })}
          onCancel={() => setPendingOffer(null)}
          isPending={purchaseMutation.isPending}
        />
      )}

      {/* Upgrade PIN confirmation modal */}
      {showUpgradePinModal && requiredTier && requiredTierLabel && (
        <UpgradePinModal
          requiredTier={requiredTier}
          requiredTierLabel={requiredTierLabel}
          onSuccess={() => {
            queryClient.invalidateQueries({ queryKey: ['title', id] })
            queryClient.invalidateQueries({ queryKey: ['admin-users'] })
          }}
          onClose={() => setShowUpgradePinModal(false)}
        />
      )}

      {/* Inline toast */}
      {toast && (
        <div
          className={`fixed bottom-6 right-6 z-50 rounded-lg px-4 py-3 text-sm font-medium text-white shadow-lg transition-all ${
            toast.type === 'success' ? 'bg-green-600' : 'bg-red-600'
          }`}
        >
          {toast.message}
        </div>
      )}

      {/* Hero Section */}
      <div className="relative w-full h-[50vh] sm:h-[60vh] overflow-hidden">
        <img
          src={title.landscape_url || title.poster_url}
          alt={title.title}
          className="w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-surface via-surface/60 to-surface/20" />
        <div className="absolute inset-0 bg-gradient-to-r from-surface/80 via-transparent to-transparent" />
      </div>

      {/* Content */}
      <div className="max-w-screen-xl mx-auto px-4 sm:px-6 lg:px-8 -mt-32 relative z-10">
        {/* Title + Meta */}
        <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-white mb-3">{title.title}</h1>
        <div className="flex flex-wrap items-center gap-3 text-sm text-gray-400 mb-4">
          <span>{title.release_year}</span>
          {title.duration_minutes && (
            <>
              <span className="text-gray-600">|</span>
              <span>{Math.floor(title.duration_minutes / 60)}h {title.duration_minutes % 60}m</span>
            </>
          )}
          <span className="text-gray-600">|</span>
          <span className="px-2 py-0.5 border border-gray-600 rounded text-xs">{title.age_rating}</span>
          {title.genres.map(g => (
            <span key={g} className="px-2 py-0.5 bg-surface-overlay rounded-full text-xs">{g}</span>
          ))}
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center gap-3 mb-2">
          {hasAccess ? (
            /* User has access — show active Play button */
            <button
              onClick={handlePlay}
              className="flex items-center gap-2 px-8 py-3 bg-white text-black font-semibold rounded-md hover:bg-white/90 transition-colors"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M8 5v14l11-7z" />
              </svg>
              Play
            </button>
          ) : rentOption || buyOption ? (
            /* No access but TVOD options exist — show locked Play + rent/buy CTAs */
            <div className="flex flex-wrap items-center gap-3">
              <button
                disabled
                className="flex items-center gap-2 px-8 py-3 bg-white/20 text-white/40 font-semibold rounded-md cursor-not-allowed"
                title="Purchase or subscribe to watch"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 1 0-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 0 0 2.25-2.25v-6.75a2.25 2.25 0 0 0-2.25-2.25H6.75a2.25 2.25 0 0 0-2.25 2.25v6.75a2.25 2.25 0 0 0 2.25 2.25Z" />
                </svg>
                Play
              </button>

              {rentOption && rentOption.price_cents != null && rentOption.currency && (
                <button
                  onClick={() => setPendingOffer(rentOption)}
                  className="flex items-center gap-2 px-5 py-3 bg-white/10 text-white font-medium rounded-md hover:bg-white/20 transition-colors border border-white/20"
                >
                  Rent {formatPrice(rentOption.price_cents, rentOption.currency)}
                </button>
              )}

              {buyOption && buyOption.price_cents != null && buyOption.currency && (
                <button
                  onClick={() => setPendingOffer(buyOption)}
                  className="flex items-center gap-2 px-5 py-3 bg-primary-600 text-white font-semibold rounded-md hover:bg-primary-500 transition-colors"
                >
                  Buy {formatPrice(buyOption.price_cents, buyOption.currency)}
                </button>
              )}
            </div>
          ) : (
            /* No access and no purchase path — subscription / upgrade required */
            <button
              onClick={() => isAuthenticated ? setShowUpgradePinModal(true) : navigate('/login')}
              className="flex items-center gap-2 px-8 py-3 bg-primary-600 text-white font-semibold rounded-md hover:bg-primary-500 transition-colors"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 1 0-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 0 0 2.25-2.25v-6.75a2.25 2.25 0 0 0-2.25-2.25H6.75a2.25 2.25 0 0 0-2.25 2.25v6.75a2.25 2.25 0 0 0 2.25 2.25Z" />
              </svg>
              {isAuthenticated && requiredTierLabel
                ? `Upgrade to ${requiredTierLabel}`
                : 'Subscribe to Watch'}
            </button>
          )}

          <button
            onClick={() => watchlistMutation.mutate()}
            disabled={watchlistMutation.isPending}
            className={`flex items-center gap-2 px-5 py-3 font-medium rounded-md transition-colors ${
              isInWatchlist
                ? 'bg-primary-500/20 text-primary-400 border border-primary-500/50 hover:bg-primary-500/30'
                : 'bg-white/10 text-white hover:bg-white/20'
            }`}
          >
            {isInWatchlist ? (
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" />
              </svg>
            ) : (
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
              </svg>
            )}
            {isInWatchlist ? 'In My List' : 'My List'}
          </button>

          {/* Rate buttons */}
          <button
            onClick={() => rateMutation.mutate(1)}
            className={`p-3 rounded-full transition-colors ${
              userRating === 1
                ? 'bg-green-500/20 text-green-400'
                : 'bg-white/10 text-gray-400 hover:bg-white/20 hover:text-white'
            }`}
            title="I liked this"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6.633 10.25c.806 0 1.533-.446 2.031-1.08a9.041 9.041 0 0 1 2.861-2.4c.723-.384 1.35-.956 1.653-1.715a4.498 4.498 0 0 0 .322-1.672V3a.75.75 0 0 1 .75-.75 2.25 2.25 0 0 1 2.25 2.25c0 1.152-.26 2.243-.723 3.218-.266.558.107 1.282.725 1.282m0 0h3.126c1.026 0 1.945.694 2.054 1.715.045.422.068.85.068 1.285a11.95 11.95 0 0 1-2.649 7.521c-.388.482-.987.729-1.605.729H13.48c-.483 0-.964-.078-1.423-.23l-3.114-1.04a4.501 4.501 0 0 0-1.423-.23H5.904m10.598-9.75H14.25M5.904 18.5c.083.205.173.405.27.602.197.4-.078.898-.523.898h-.908c-.889 0-1.713-.518-1.972-1.368a12 12 0 0 1-.521-3.507c0-1.553.295-3.036.831-4.398C3.387 9.953 4.167 9.5 5 9.5h1.053c.472 0 .745.556.5.96a8.958 8.958 0 0 0-1.302 4.665c0 1.194.232 2.333.654 3.375Z" />
            </svg>
          </button>

          <button
            onClick={() => rateMutation.mutate(-1)}
            className={`p-3 rounded-full transition-colors ${
              userRating === -1
                ? 'bg-red-500/20 text-red-400'
                : 'bg-white/10 text-gray-400 hover:bg-white/20 hover:text-white'
            }`}
            title="Not for me"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M7.498 15.25H4.372c-1.026 0-1.945-.694-2.054-1.715a12.137 12.137 0 0 1-.068-1.285c0-2.848.992-5.464 2.649-7.521C5.287 4.247 5.886 4 6.504 4h4.016a4.5 4.5 0 0 1 1.423.23l3.114 1.04a4.5 4.5 0 0 0 1.423.23h1.294M7.498 15.25c.618 0 .991.724.725 1.282A7.471 7.471 0 0 0 7.5 19.75 2.25 2.25 0 0 0 9.75 22a.75.75 0 0 0 .75-.75v-.633c0-.573.11-1.14.322-1.672.304-.76.93-1.33 1.653-1.715a9.04 9.04 0 0 0 2.86-2.4c.498-.634 1.226-1.08 2.032-1.08h.384m-10.253 1.5H9.7m8.075-9.75c.01.05.027.1.05.148.593 1.2.925 2.55.925 3.977 0 1.31-.269 2.559-.754 3.695-.292.683.033 1.555.794 1.555h1.341c.816 0 1.6-.28 1.973-1.068a12.122 12.122 0 0 0 1.046-4.182c0-.169-.002-.337-.006-.505" />
            </svg>
          </button>
        </div>

        {/* Access label — "Included with Basic Plan", "Purchased", "Free to watch" */}
        {inclusionLabel && (
          <p className="mt-2 mb-1 text-sm text-gray-400 flex items-center gap-1.5">
            <svg className="w-4 h-4 text-green-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
            </svg>
            {inclusionLabel}
          </p>
        )}

        {/* "Available on [Plan]" hint for locked SVOD titles with no purchase path */}
        {!hasAccess && !rentOption && !buyOption && requiredTierLabel && (
          <p className="mt-2 mb-1 text-sm text-gray-500">
            Available on the <span className="text-white font-medium">{requiredTierLabel} Plan</span>
          </p>
        )}

        {/* Rental expiry badge */}
        {isRental && userAccess?.expires_at && (
          <p className="mb-4 text-sm text-amber-400">
            Rental expires: {formatExpiresAt(userAccess.expires_at)}
          </p>
        )}

        {/* Synopsis */}
        <p className="text-gray-300 text-base leading-relaxed max-w-3xl mb-8">
          {title.synopsis_long || title.synopsis_short}
        </p>

        {/* Cast */}
        {title.cast.length > 0 && (
          <div className="mb-10">
            <h3 className="text-lg font-semibold text-white mb-3">Cast</h3>
            <div className="flex flex-wrap gap-4">
              {title.cast.map((member, i) => (
                <div key={i} className="flex items-center gap-3 bg-surface-raised rounded-lg p-3 pr-5">
                  <div className="w-10 h-10 rounded-full bg-surface-overlay flex items-center justify-center text-sm font-bold text-gray-400">
                    {member.person_name.charAt(0)}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-white">{member.person_name}</p>
                    <p className="text-xs text-gray-500">{member.character_name || member.role}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Seasons & Episodes (for series) */}
        {title.title_type === 'series' && title.seasons.length > 0 && (
          <div className="mb-10">
            {/* Season tabs */}
            <div className="flex items-center gap-3 mb-4 overflow-x-auto" style={{ scrollbarWidth: 'none' }}>
              {title.seasons.map(s => (
                <button
                  key={s.season_number}
                  onClick={() => setSelectedSeason(s.season_number)}
                  className={`px-4 py-2 text-sm font-medium rounded-full whitespace-nowrap transition-colors ${
                    selectedSeason === s.season_number
                      ? 'bg-primary-500 text-white'
                      : 'bg-surface-overlay text-gray-400 hover:text-white hover:bg-white/10'
                  }`}
                >
                  Season {s.season_number}
                </button>
              ))}
            </div>

            {/* Episode list */}
            <div className="space-y-2">
              {currentSeason?.episodes.map(ep => (
                <button
                  key={ep.id}
                  onClick={() => hasAccess && navigate(`/play/episode/${ep.id}`)}
                  disabled={!hasAccess}
                  className={`w-full flex items-center gap-4 p-3 rounded-lg bg-surface-raised transition-colors text-left group ${
                    hasAccess
                      ? 'hover:bg-surface-overlay cursor-pointer'
                      : 'opacity-60 cursor-not-allowed'
                  }`}
                >
                  {/* Thumbnail */}
                  <div className="relative w-32 sm:w-40 aspect-video rounded overflow-hidden bg-surface-overlay shrink-0">
                    <div className="w-full h-full flex items-center justify-center">
                      <svg className="w-8 h-8 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="m15.75 10.5 4.72-4.72a.75.75 0 0 1 1.28.53v11.38a.75.75 0 0 1-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 0 0 2.25-2.25v-9a2.25 2.25 0 0 0-2.25-2.25h-9A2.25 2.25 0 0 0 2.25 7.5v9a2.25 2.25 0 0 0 2.25 2.25Z" />
                      </svg>
                    </div>
                    {/* Play icon overlay (only when access granted) */}
                    {hasAccess && (
                      <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity bg-black/40">
                        <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 24 24">
                          <path d="M8 5v14l11-7z" />
                        </svg>
                      </div>
                    )}
                    {/* Lock icon overlay (when no access) */}
                    {!hasAccess && (
                      <div className="absolute inset-0 flex items-center justify-center bg-black/50">
                        <svg className="w-6 h-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 1 0-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 0 0 2.25-2.25v-6.75a2.25 2.25 0 0 0-2.25-2.25H6.75a2.25 2.25 0 0 0-2.25 2.25v6.75a2.25 2.25 0 0 0 2.25 2.25Z" />
                        </svg>
                      </div>
                    )}
                  </div>

                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-bold text-gray-500">{ep.episode_number}</span>
                      <h4 className="text-sm font-medium text-white truncate">{ep.title}</h4>
                    </div>
                    <p className="text-xs text-gray-400 mt-0.5">{ep.duration_minutes} min</p>
                    <p className="text-xs text-gray-500 mt-1 line-clamp-2">{ep.synopsis}</p>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* More Like This */}
        {similar && similar.length > 0 && (
          <ContentRail title="More Like This">
            {similar.map(item => (
              <TitleCard
                key={item.id}
                title={item.title}
                posterUrl={item.poster_url}
                landscapeUrl={item.landscape_url}
                titleType={item.title_type}
                releaseYear={item.release_year}
                ageRating={item.age_rating}
                accessOptions={item.access_options}
                userAccess={item.user_access}
                onClick={() => navigate(`/title/${item.id}`)}
              />
            ))}
          </ContentRail>
        )}
      </div>
    </div>
  )
}
