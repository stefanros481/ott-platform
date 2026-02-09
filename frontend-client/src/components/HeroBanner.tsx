import { useState, useEffect, useCallback } from 'react'

interface HeroItem {
  id: string
  title: string
  synopsis: string
  landscapeUrl: string | null
  posterUrl: string
}

interface HeroBannerProps {
  items: HeroItem[]
  onPlay: (id: string) => void
  onMoreInfo: (id: string) => void
}

export default function HeroBanner({ items, onPlay, onMoreInfo }: HeroBannerProps) {
  const [activeIndex, setActiveIndex] = useState(0)

  const advance = useCallback(() => {
    setActiveIndex(prev => (prev + 1) % items.length)
  }, [items.length])

  useEffect(() => {
    if (items.length <= 1) return
    const timer = setInterval(advance, 5000)
    return () => clearInterval(timer)
  }, [advance, items.length])

  if (items.length === 0) return null

  const item = items[activeIndex]
  if (!item) return null

  return (
    <div className="relative w-full h-[50vh] sm:h-[60vh] lg:h-[70vh] overflow-hidden">
      {/* Background image */}
      <div className="absolute inset-0">
        <img
          src={item.landscapeUrl || item.posterUrl}
          alt={item.title}
          className="w-full h-full object-cover"
        />
        {/* Gradient overlays */}
        <div className="absolute inset-0 bg-gradient-to-t from-surface via-surface/50 to-transparent" />
        <div className="absolute inset-0 bg-gradient-to-r from-surface/80 via-transparent to-transparent" />
      </div>

      {/* Content */}
      <div className="absolute bottom-0 left-0 right-0 p-6 sm:p-10 lg:p-16">
        <div className="max-w-2xl">
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-white mb-3 leading-tight">
            {item.title}
          </h1>
          <p className="text-sm sm:text-base text-gray-300 line-clamp-3 mb-6 max-w-xl">
            {item.synopsis}
          </p>
          <div className="flex items-center gap-3">
            <button
              onClick={() => onPlay(item.id)}
              className="flex items-center gap-2 px-6 py-2.5 bg-white text-black font-semibold rounded-md hover:bg-white/90 transition-colors"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M8 5v14l11-7z" />
              </svg>
              Play
            </button>
            <button
              onClick={() => onMoreInfo(item.id)}
              className="flex items-center gap-2 px-6 py-2.5 bg-white/20 text-white font-semibold rounded-md hover:bg-white/30 transition-colors backdrop-blur-sm"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="m11.25 11.25.041-.02a.75.75 0 0 1 1.063.852l-.708 2.836a.75.75 0 0 0 1.063.853l.041-.021M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9-3.75h.008v.008H12V8.25Z" />
              </svg>
              More Info
            </button>
          </div>
        </div>

        {/* Dots indicator */}
        {items.length > 1 && (
          <div className="flex items-center gap-2 mt-6">
            {items.map((_, idx) => (
              <button
                key={idx}
                onClick={() => setActiveIndex(idx)}
                className={`h-1 rounded-full transition-all duration-300 ${
                  idx === activeIndex ? 'w-8 bg-white' : 'w-4 bg-white/40 hover:bg-white/60'
                }`}
                aria-label={`Go to slide ${idx + 1}`}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
