import { type AccessOption, type UserAccess } from '../api/catalog'

interface TitleCardProps {
  title: string
  posterUrl: string | null
  landscapeUrl?: string | null
  titleType: string
  releaseYear: number | null
  ageRating: string | null
  onClick: () => void
  isNew?: boolean
  isEducational?: boolean
  accessOptions?: AccessOption[]
  userAccess?: UserAccess | null
}

function formatPrice(priceCents: number, currency: string): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency.toUpperCase(),
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(priceCents / 100)
}

/** Returns the lowest priced rent/buy option, or null. */
function lowestPaidOption(options: AccessOption[]): AccessOption | null {
  const paid = options.filter(
    o => (o.type === 'rent' || o.type === 'buy') && o.price_cents != null,
  )
  if (!paid.length) return null
  return paid.reduce((min, o) => (o.price_cents! < min.price_cents! ? o : min))
}

export default function TitleCard({
  title,
  posterUrl,
  titleType,
  releaseYear,
  ageRating,
  onClick,
  isNew,
  isEducational,
  accessOptions,
  userAccess,
}: TitleCardProps) {
  // Derive access badge
  const hasFreeOption = accessOptions?.some(o => o.type === 'free')
  const hasAccess = userAccess?.has_access === true
  const cheapestPaid = accessOptions ? lowestPaidOption(accessOptions) : null

  // Tier badge for locked SVOD-only titles (no TVOD offers, not free)
  const TIER_LABEL: Record<string, string> = { basic: 'Basic', standard: 'Standard', premium: 'Premium' }
  const TIER_STYLE: Record<string, string> = {
    basic:    'bg-blue-500/80 text-white',
    standard: 'bg-violet-500/80 text-white',
    premium:  'bg-amber-500/80 text-white',
  }
  const requiredTier = userAccess?.required_tier
  const showTierBadge = !hasAccess && !hasFreeOption && !cheapestPaid && !!requiredTier

  return (
    <button
      onClick={onClick}
      className="group relative flex-shrink-0 w-[160px] sm:w-[180px] md:w-[200px] focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 rounded-lg"
    >
      {/* Poster */}
      <div className="relative aspect-[2/3] rounded-lg overflow-hidden bg-surface-overlay">
        <img
          src={posterUrl || ''}
          alt={title}
          className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
          loading="lazy"
        />

        {/* Hover overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/30 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

        {/* NEW badge */}
        {isNew && (
          <span className="absolute top-2 left-2 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider bg-primary-500 text-white rounded">
            NEW
          </span>
        )}

        {/* Type badge */}
        <span className="absolute top-2 right-2 px-1.5 py-0.5 text-[10px] font-medium uppercase bg-black/60 text-gray-300 rounded">
          {titleType === 'series' ? 'Series' : 'Movie'}
        </span>

        {/* Educational badge */}
        {isEducational && (
          <span className="absolute top-8 right-2 px-1.5 py-0.5 text-[10px] font-medium bg-emerald-600/80 text-emerald-100 rounded">
            Educational
          </span>
        )}

        {/* Access badge — shown in top-left below NEW (or instead of it) */}
        {!isNew && hasFreeOption && !hasAccess && (
          <span className="absolute top-2 left-2 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider bg-green-600 text-white rounded">
            FREE
          </span>
        )}

        {/* Tier badge — shown for locked SVOD-only titles so the user knows which plan is needed */}
        {showTierBadge && requiredTier && (
          <span className={`absolute top-2 left-2 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider rounded ${TIER_STYLE[requiredTier] ?? 'bg-gray-600 text-white'}`}>
            {TIER_LABEL[requiredTier] ?? requiredTier}
          </span>
        )}

        {!hasAccess && !hasFreeOption && cheapestPaid && cheapestPaid.price_cents != null && cheapestPaid.currency && (
          <span className="absolute bottom-10 left-2 right-2 px-2 py-0.5 text-[10px] font-medium bg-black/70 text-gray-200 rounded text-center group-hover:opacity-0 transition-opacity">
            From {formatPrice(cheapestPaid.price_cents, cheapestPaid.currency)}
          </span>
        )}

        {/* Bottom info (visible on hover) */}
        <div className="absolute bottom-0 left-0 right-0 p-3 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
          <p className="text-sm font-semibold text-white leading-tight line-clamp-2">{title}</p>
          <div className="flex items-center gap-2 mt-1">
            <span className="text-xs text-gray-400">{releaseYear ?? ''}</span>
            <span className="text-xs text-gray-500">|</span>
            <span className="text-xs text-gray-400">{ageRating ?? ''}</span>
          </div>
          {/* Show price in hover overlay for unowned paid content */}
          {!hasAccess && !hasFreeOption && cheapestPaid && cheapestPaid.price_cents != null && cheapestPaid.currency && (
            <span className="mt-1 inline-block text-[10px] text-amber-300">
              From {formatPrice(cheapestPaid.price_cents, cheapestPaid.currency)}
            </span>
          )}
        </div>
      </div>

      {/* Title below card (always visible) */}
      <p className="mt-2 text-sm text-gray-300 truncate text-left">{title}</p>
    </button>
  )
}
