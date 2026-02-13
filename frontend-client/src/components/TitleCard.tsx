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
}: TitleCardProps) {
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

        {/* Bottom info (visible on hover) */}
        <div className="absolute bottom-0 left-0 right-0 p-3 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
          <p className="text-sm font-semibold text-white leading-tight line-clamp-2">{title}</p>
          <div className="flex items-center gap-2 mt-1">
            <span className="text-xs text-gray-400">{releaseYear ?? ''}</span>
            <span className="text-xs text-gray-500">|</span>
            <span className="text-xs text-gray-400">{ageRating ?? ''}</span>
          </div>
        </div>
      </div>

      {/* Title below card (always visible) */}
      <p className="mt-2 text-sm text-gray-300 truncate text-left">{title}</p>
    </button>
  )
}
