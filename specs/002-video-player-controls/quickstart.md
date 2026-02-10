# Quickstart: Video Player Controls

**Feature**: 002-video-player-controls

## Prerequisites

- Docker Compose running (`docker compose up`)
- Frontend client accessible at `http://localhost:5173`
- At least one seeded title with a valid `hls_manifest_url`

## Verify Changes

1. **Start the stack**: `docker compose up` from repo root
2. **Login**: Navigate to `http://localhost:5173/login`, sign in with a test account
3. **Select a profile**: Choose any profile
4. **Navigate to a title**: Click any title card to reach the detail page
5. **Start playback**: Click the Play button

## Expected Behavior

### Control bar
- Hover over the video → control bar appears at the bottom
- Stop moving mouse → controls fade out after **5 seconds**
- Buttons visible (left to right): **Rewind 10s** | **Play/Pause** | **Forward 10s** | **Start Over**
- Center shows elapsed time / total duration
- Right side shows volume and fullscreen controls

### Transport controls
- **Rewind 10s**: Click to jump back 10 seconds (icon: counterclockwise arrow with "10")
- **Play/Pause**: Click to toggle playback (icon: triangle / two bars)
- **Forward 10s**: Click to jump forward 10 seconds (icon: clockwise arrow with "10")
- **Start Over**: Click to restart from beginning and auto-play (icon: refresh arrow)

### Files modified
- `frontend-client/src/components/VideoPlayer.tsx` — Control bar layout, new buttons, auto-hide timing, live support
- `frontend-client/src/pages/PlayerPage.tsx` — `isLive` prop pass-through
