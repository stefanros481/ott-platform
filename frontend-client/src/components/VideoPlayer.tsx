import { useRef, useEffect, useState, useCallback } from 'react'
import shaka from 'shaka-player'

interface VideoPlayerProps {
  manifestUrl: string
  title: string
  isLive?: boolean
  clearKeys?: Record<string, string>
  onPositionUpdate?: (positionSeconds: number) => void
  onDurationChange?: (durationSeconds: number) => void
  onPlayStateChange?: (playing: boolean) => void
  startPosition?: number
  onEnded?: () => void
  onBack?: () => void
  onStartOver?: () => void
}

export default function VideoPlayer({
  manifestUrl,
  title,
  isLive = false,
  clearKeys,
  onPositionUpdate,
  onDurationChange: onDurationChangeProp,
  onPlayStateChange,
  startPosition,
  onEnded,
  onBack,
  onStartOver,
}: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const playerRef = useRef<shaka.Player | null>(null)
  const attachPromiseRef = useRef<Promise<void>>(Promise.resolve())
  const positionTimerRef = useRef<ReturnType<typeof setInterval>>()
  const onPositionUpdateRef = useRef(onPositionUpdate)
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [volume, setVolume] = useState(1)
  const [isMuted, setIsMuted] = useState(false)
  const [showControls, setShowControls] = useState(true)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const controlsTimerRef = useRef<ReturnType<typeof setTimeout>>()
  const containerRef = useRef<HTMLDivElement>(null)

  const hideControlsDelayed = useCallback(() => {
    if (controlsTimerRef.current) clearTimeout(controlsTimerRef.current)
    controlsTimerRef.current = setTimeout(() => {
      if (isPlaying) setShowControls(false)
    }, 5000)
  }, [isPlaying])

  const handleMouseMove = useCallback(() => {
    setShowControls(true)
    hideControlsDelayed()
  }, [hideControlsDelayed])

  // Keep ref in sync so unmount cleanup always uses the latest callback
  useEffect(() => {
    onPositionUpdateRef.current = onPositionUpdate
  }, [onPositionUpdate])

  // Create Shaka Player once on mount, destroy on unmount.
  // This avoids the race condition where async destroy() on the old player
  // hasn't released the <video> element before a new player tries to attach.
  useEffect(() => {
    const video = videoRef.current
    if (!video) return

    shaka.polyfill.installAll()
    if (!shaka.Player.isBrowserSupported()) {
      setError('Browser not supported for video playback')
      return
    }

    const player = new shaka.Player()
    playerRef.current = player

    // Store the attach promise so the load effect can wait for it
    attachPromiseRef.current = (async () => {
      await player.attach(video)

      // Attach JWT token to requests aimed at our API (manifest + DRM license)
      const apiBase = (import.meta.env.VITE_API_BASE_URL as string) || 'http://localhost:8000/api/v1'
      const apiOrigin = new URL(apiBase).origin
      player.getNetworkingEngine()?.registerRequestFilter((_type, request) => {
        if (request.uris.some(uri => uri.startsWith(apiOrigin))) {
          const token = localStorage.getItem('token')
          if (token) {
            request.headers['Authorization'] = `Bearer ${token}`
          }
        }
      })
    })()

    return () => {
      // Save final position before destroying the player
      if (video && onPositionUpdateRef.current) onPositionUpdateRef.current(Math.floor(video.currentTime))
      if (positionTimerRef.current) clearInterval(positionTimerRef.current)
      if (controlsTimerRef.current) clearTimeout(controlsTimerRef.current)
      playerRef.current = null
      player.destroy()
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Load manifest when URL or DRM config changes.
  // Reuses the persistent player instance — no destroy/create cycle.
  useEffect(() => {
    if (!manifestUrl) return
    let cancelled = false

    const loadManifest = async () => {
      // Wait for player to be attached to the video element
      await attachPromiseRef.current
      const player = playerRef.current
      const video = videoRef.current
      if (!player || !video || cancelled) return

      // Configure ClearKey DRM via direct key map (or clear it for live mode)
      player.configure({
        drm: clearKeys && Object.keys(clearKeys).length > 0
          ? { clearKeys }
          : { clearKeys: {} },
      })

      try {
        await player.load(manifestUrl)
        if (cancelled) return
        if (!isLive && startPosition && startPosition > 0) {
          video.currentTime = startPosition
        }
        video.play().catch(() => {})
      } catch (e) {
        if (cancelled) return
        const shakaError = e as shaka.util.Error
        if (shakaError.code === shaka.util.Error.Code.LOAD_INTERRUPTED) return
        if (shakaError.severity === shaka.util.Error.Severity.CRITICAL) {
          setError(`Playback error: Shaka Error ${shakaError.code}`)
        }
      }
    }

    loadManifest()

    return () => { cancelled = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [manifestUrl, clearKeys])

  // Position reporting
  useEffect(() => {
    if (!onPositionUpdate) return
    positionTimerRef.current = setInterval(() => {
      const video = videoRef.current
      if (video && !video.paused) {
        onPositionUpdate(Math.floor(video.currentTime))
      }
    }, 30000)
    return () => {
      if (positionTimerRef.current) clearInterval(positionTimerRef.current)
    }
  }, [onPositionUpdate])

  // Video event handlers
  useEffect(() => {
    const video = videoRef.current
    if (!video) return

    const onPlay = () => {
      setIsPlaying(true)
      onPlayStateChange?.(true)
    }
    const onPause = () => {
      setIsPlaying(false)
      onPlayStateChange?.(false)
      // Save position immediately on pause
      if (onPositionUpdate) onPositionUpdate(Math.floor(video.currentTime))
    }
    const onTimeUpdate = () => setCurrentTime(video.currentTime)
    const onDurationChange = () => {
      setDuration(video.duration)
      if (video.duration && isFinite(video.duration)) onDurationChangeProp?.(video.duration)
    }
    const onEndedHandler = () => {
      setIsPlaying(false)
      onPlayStateChange?.(false)
      if (onPositionUpdate) onPositionUpdate(Math.floor(video.currentTime))
      onEnded?.()
    }

    video.addEventListener('play', onPlay)
    video.addEventListener('pause', onPause)
    video.addEventListener('timeupdate', onTimeUpdate)
    video.addEventListener('durationchange', onDurationChange)
    video.addEventListener('ended', onEndedHandler)

    return () => {
      video.removeEventListener('play', onPlay)
      video.removeEventListener('pause', onPause)
      video.removeEventListener('timeupdate', onTimeUpdate)
      video.removeEventListener('durationchange', onDurationChange)
      video.removeEventListener('ended', onEndedHandler)
    }
  }, [onEnded, onPositionUpdate, onPlayStateChange, onDurationChangeProp])

  // Fullscreen change listener
  useEffect(() => {
    const onFsChange = () => setIsFullscreen(!!document.fullscreenElement)
    document.addEventListener('fullscreenchange', onFsChange)
    return () => document.removeEventListener('fullscreenchange', onFsChange)
  }, [])

  const togglePlay = () => {
    const video = videoRef.current
    if (!video) return
    if (video.paused) {
      video.play()
    } else {
      video.pause()
    }
  }

  const seek = (time: number) => {
    const video = videoRef.current
    if (!video) return
    video.currentTime = time
  }

  const rewind10 = () => {
    const video = videoRef.current
    if (!video) return
    video.currentTime = Math.max(0, video.currentTime - 10)
  }

  const forward10 = () => {
    const video = videoRef.current
    if (!video) return
    video.currentTime = Math.min(duration, video.currentTime + 10)
  }

  const startOver = () => {
    const video = videoRef.current
    if (!video) return
    if (isLive && playerRef.current) {
      const seekRange = playerRef.current.seekRange()
      video.currentTime = seekRange.start
    } else {
      video.currentTime = 0
    }
    if (video.paused) video.play()
  }

  const toggleMute = () => {
    const video = videoRef.current
    if (!video) return
    video.muted = !video.muted
    setIsMuted(video.muted)
  }

  const changeVolume = (val: number) => {
    const video = videoRef.current
    if (!video) return
    video.volume = val
    setVolume(val)
    if (val === 0) {
      video.muted = true
      setIsMuted(true)
    } else if (video.muted) {
      video.muted = false
      setIsMuted(false)
    }
  }

  const toggleFullscreen = async () => {
    if (!containerRef.current) return
    if (document.fullscreenElement) {
      await document.exitFullscreen()
    } else {
      await containerRef.current.requestFullscreen()
    }
  }

  const formatTime = (seconds: number): string => {
    if (!isFinite(seconds)) return '0:00'
    const h = Math.floor(seconds / 3600)
    const m = Math.floor((seconds % 3600) / 60)
    const s = Math.floor(seconds % 60)
    if (h > 0) {
      return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
    }
    return `${m}:${String(s).padStart(2, '0')}`
  }

  if (error) {
    return (
      <div className="w-full h-full bg-black flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-400 text-lg mb-4">{error}</p>
          {onBack && (
            <button onClick={onBack} className="px-4 py-2 bg-white/20 text-white rounded hover:bg-white/30">
              Go Back
            </button>
          )}
        </div>
      </div>
    )
  }

  return (
    <div
      ref={containerRef}
      className="relative w-full h-full bg-black cursor-pointer"
      onMouseMove={handleMouseMove}
      onClick={togglePlay}
    >
      <video ref={videoRef} className="w-full h-full" />

      {/* Controls overlay */}
      <div
        className={`absolute inset-0 transition-opacity duration-300 ${
          showControls ? 'opacity-100' : 'opacity-0 pointer-events-none'
        }`}
        onClick={e => e.stopPropagation()}
      >
        {/* Top gradient + back + title */}
        <div className="absolute top-0 left-0 right-0 bg-gradient-to-b from-black/70 to-transparent p-4 flex items-center gap-4">
          {onBack && (
            <button onClick={() => {
              const video = videoRef.current
              if (video && onPositionUpdate) onPositionUpdate(Math.floor(video.currentTime))
              onBack()
            }} className="p-1 hover:text-primary-400 transition-colors">
              <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5 3 12m0 0 7.5-7.5M3 12h18" />
              </svg>
            </button>
          )}
          <h2 className="text-white font-medium text-lg truncate">{title}</h2>
        </div>

        {/* Center play/pause */}
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <button
            onClick={togglePlay}
            className="w-16 h-16 flex items-center justify-center rounded-full bg-black/50 hover:bg-black/70 transition-colors pointer-events-auto"
          >
            {isPlaying ? (
              <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 24 24">
                <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" />
              </svg>
            ) : (
              <svg className="w-8 h-8 text-white ml-1" fill="currentColor" viewBox="0 0 24 24">
                <path d="M8 5v14l11-7z" />
              </svg>
            )}
          </button>
        </div>

        {/* Bottom controls */}
        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-4">
          {/* Seek bar — hidden for live */}
          {!isLive && (
            <div className="group/seek relative mb-3">
              <input
                type="range"
                min={0}
                max={duration || 0}
                value={currentTime}
                onChange={e => seek(Number(e.target.value))}
                className="w-full h-1 group-hover/seek:h-2 bg-white/30 rounded-full appearance-none cursor-pointer transition-all
                  [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:h-3
                  [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-primary-500
                  [&::-webkit-slider-thumb]:opacity-0 [&::-webkit-slider-thumb]:group-hover/seek:opacity-100
                  [&::-webkit-slider-thumb]:transition-opacity"
                style={{
                  background: `linear-gradient(to right, #6366f1 ${(currentTime / (duration || 1)) * 100}%, rgba(255,255,255,0.3) 0%)`,
                }}
              />
            </div>
          )}

          <div className="flex items-center justify-between">
            {/* Transport controls */}
            <div className="flex items-center gap-3">
              {/* Rewind 10s */}
              <button onClick={rewind10} className="text-white hover:text-primary-400 transition-colors" title="Rewind 10 seconds">
                <svg className="w-7 h-7" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 5V1L7 6l5 5V7c3.31 0 6 2.69 6 6s-2.69 6-6 6-6-2.69-6-6H4c0 4.42 3.58 8 8 8s8-3.58 8-8-3.58-8-8-8z" />
                  <text x="12" y="16" fontSize="8" fontWeight="bold" fontFamily="Arial,sans-serif" textAnchor="middle">10</text>
                </svg>
              </button>

              {/* Play/Pause */}
              <button onClick={togglePlay} className="text-white hover:text-primary-400 transition-colors" title={isPlaying ? 'Pause' : 'Play'}>
                {isPlaying ? (
                  <svg className="w-7 h-7" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" />
                  </svg>
                ) : (
                  <svg className="w-7 h-7" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M8 5v14l11-7z" />
                  </svg>
                )}
              </button>

              {/* Forward 10s */}
              <button onClick={forward10} className="text-white hover:text-primary-400 transition-colors" title="Forward 10 seconds">
                <svg className="w-7 h-7" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 5V1l5 5-5 5V7c-3.31 0-6 2.69-6 6s2.69 6 6 6 6-2.69 6-6h2c0 4.42-3.58 8-8 8s-8-3.58-8-8 3.58-8 8-8z" />
                  <text x="12" y="16" fontSize="8" fontWeight="bold" fontFamily="Arial,sans-serif" textAnchor="middle">10</text>
                </svg>
              </button>

              {/* Start Over */}
              <button onClick={onStartOver ?? startOver} className="text-white hover:text-primary-400 transition-colors" title="Start over">
                <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h5" />
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4 9c1.5-3.5 5-6 9-6 5.523 0 10 4.477 10 10s-4.477 10-10 10c-4.5 0-8.27-2.943-9.543-7" />
                </svg>
              </button>
            </div>

            {/* Time / Live badge */}
            <div className="flex items-center">
              {isLive ? (
                <span className="flex items-center gap-1.5 text-sm font-medium">
                  <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                  <span className="text-red-400">LIVE</span>
                </span>
              ) : (
                <span className="text-sm text-gray-300 tabular-nums">
                  {formatTime(currentTime)} / {formatTime(duration)}
                </span>
              )}
            </div>

            {/* Utility controls */}
            <div className="flex items-center gap-3">
              {/* Volume */}
              <div className="flex items-center gap-1 group/vol">
                <button onClick={toggleMute} className="text-white hover:text-primary-400 transition-colors">
                  {isMuted || volume === 0 ? (
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M17.25 9.75 19.5 12m0 0 2.25 2.25M19.5 12l2.25-2.25M19.5 12l-2.25 2.25m-10.5-6 4.72-3.72a.75.75 0 0 1 1.28.53v14.88a.75.75 0 0 1-1.28.53l-4.72-3.72H4.51c-.88 0-1.704-.507-1.938-1.354A9.009 9.009 0 0 1 2.25 12c0-.83.112-1.633.322-2.396C2.806 8.756 3.63 8.25 4.51 8.25H6.75Z" />
                    </svg>
                  ) : (
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M19.114 5.636a9 9 0 0 1 0 12.728M16.463 8.288a5.25 5.25 0 0 1 0 7.424M6.75 8.25l4.72-3.72a.75.75 0 0 1 1.28.53v14.88a.75.75 0 0 1-1.28.53l-4.72-3.72H4.51c-.88 0-1.704-.507-1.938-1.354A9.009 9.009 0 0 1 2.25 12c0-.83.112-1.633.322-2.396C2.806 8.756 3.63 8.25 4.51 8.25H6.75Z" />
                    </svg>
                  )}
                </button>
                <input
                  type="range"
                  min={0}
                  max={1}
                  step={0.05}
                  value={isMuted ? 0 : volume}
                  onChange={e => changeVolume(Number(e.target.value))}
                  className="w-0 group-hover/vol:w-20 transition-all duration-200 h-1 bg-white/30 rounded-full appearance-none cursor-pointer
                    [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:h-3
                    [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-white"
                />
              </div>

              {/* Fullscreen */}
              <button onClick={toggleFullscreen} className="text-white hover:text-primary-400 transition-colors">
                {isFullscreen ? (
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 9V4.5M9 9H4.5M9 9 3.75 3.75M9 15v4.5M9 15H4.5M9 15l-5.25 5.25M15 9h4.5M15 9V4.5M15 9l5.25-5.25M15 15h4.5M15 15v4.5m0-4.5 5.25 5.25" />
                  </svg>
                ) : (
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3.75v4.5m0-4.5h4.5m-4.5 0L9 9M3.75 20.25v-4.5m0 4.5h4.5m-4.5 0L9 15M20.25 3.75h-4.5m4.5 0v4.5m0-4.5L15 9m5.25 11.25h-4.5m4.5 0v-4.5m0 4.5L15 15" />
                  </svg>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
