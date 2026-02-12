import { useState } from 'react'
import type { ContinueWatchingItem } from '../api/viewing'

interface ContinueWatchingCardProps {
  item: ContinueWatchingItem
  onResume: (contentType: string, contentId: string) => void
  onDismiss?: (bookmarkId: string) => void
}

export default function ContinueWatchingCard({
  item,
  onResume,
  onDismiss,
}: ContinueWatchingCardProps) {
  const [fading, setFading] = useState(false)

  const imageUrl = item.title_info.landscape_url || item.title_info.poster_url || ''
  const episodeInfo =
    item.title_info.season_number != null
      ? `S${item.title_info.season_number}E${item.title_info.episode_number}`
      : null

  const handleDismiss = (e: React.MouseEvent) => {
    e.stopPropagation()
    if (onDismiss) {
      setFading(true)
      setTimeout(() => onDismiss(item.id), 300)
    }
  }

  return (
    <button
      onClick={() => onResume(item.content_type, item.content_id)}
      className={`group relative flex-shrink-0 w-[200px] focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 rounded-lg text-left transition-opacity duration-300 ${fading ? 'opacity-0' : 'opacity-100'}`}
    >
      {/* Image */}
      <div className="relative aspect-video rounded-lg overflow-hidden bg-surface-overlay">
        <img
          src={imageUrl}
          alt={item.title_info.title}
          className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
          loading="lazy"
        />

        {/* Hover overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

        {/* Dismiss button */}
        <div
          onClick={handleDismiss}
          role="button"
          tabIndex={0}
          className="absolute top-1.5 right-1.5 p-1 rounded-full bg-black/70 text-gray-400 hover:text-white opacity-0 group-hover:opacity-100 transition-all z-10"
          title="Dismiss"
        >
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
          </svg>
        </div>

        {/* Up Next badge */}
        {item.next_episode && (
          <span className="absolute top-1.5 left-1.5 px-1.5 py-0.5 text-[10px] font-medium bg-primary-500/90 text-white rounded">
            Up Next: S{item.next_episode.season_number}E{item.next_episode.episode_number}
          </span>
        )}

        {/* Progress bar */}
        <div className="absolute bottom-0 left-0 right-0 h-1 bg-black/50">
          <div
            className="h-full bg-primary-500 rounded-r-full"
            style={{ width: `${Math.min(item.progress_percent, 100)}%` }}
          />
        </div>
      </div>

      {/* Title */}
      <p className="mt-2 text-sm text-gray-300 truncate">{item.title_info.title}</p>

      {/* Episode info */}
      {episodeInfo && (
        <p className="text-xs text-gray-500">{episodeInfo}</p>
      )}
    </button>
  )
}
