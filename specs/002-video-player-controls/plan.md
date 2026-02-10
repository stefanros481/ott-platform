# Implementation Plan: Video Player Controls

**Branch**: `002-video-player-controls` | **Date**: 2026-02-09 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-video-player-controls/spec.md`

## Summary

Enhance the existing VideoPlayer component with four transport control buttons (Rewind 10s, Play/Pause, Forward 10s, Start Over), update the control bar auto-hide from 3s to 5s, and add live content differentiation (LIVE badge, hidden seek bar, live edge start). Two files modified: `VideoPlayer.tsx` (component) and `PlayerPage.tsx` (prop pass-through).

## Technical Context

**Language/Version**: TypeScript 5+ / React 18
**Primary Dependencies**: shaka-player 4.12+, React, Tailwind CSS 3+
**Storage**: N/A (UI-only, no data changes)
**Testing**: Manual browser testing (PoC — no test framework configured)
**Target Platform**: Web browser (Vite dev server)
**Project Type**: Web application (frontend-client)
**Performance Goals**: Control bar show/hide within 300ms, seek operations immediate
**Constraints**: Inline SVGs only (no icon library), existing Tailwind design patterns
**Scale/Scope**: 2 files modified, ~80 lines of new/changed code

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. PoC-First Quality | PASS | UI enhancement, no production hardening needed |
| II. Monolithic Simplicity | PASS | Frontend-only change, no backend modifications |
| III. AI-Native by Default | N/A | Transport controls are standard video player features |
| IV. Docker Compose as Truth | PASS | No infrastructure changes |
| V. Seed Data as Demo | N/A | No seed data changes |

**Technology compliance**: React + TypeScript + Tailwind CSS + Shaka Player — all match constitution stack.

## Project Structure

### Documentation (this feature)

```text
specs/002-video-player-controls/
├── plan.md              # This file
├── research.md          # Phase 0 output (minimal — no unknowns)
├── quickstart.md        # Phase 1 output
└── spec.md              # Feature specification
```

### Source Code (repository root)

```text
frontend-client/src/
├── components/
│   └── VideoPlayer.tsx      # PRIMARY — all control bar changes
└── pages/
    └── PlayerPage.tsx       # SECONDARY — isLive prop pass-through
```

**Structure Decision**: Existing web application structure. All changes within `frontend-client/src/`. No new files created — only modifications to 2 existing files.

## Implementation Details

### File: `frontend-client/src/components/VideoPlayer.tsx`

**Changes:**

1. **Props** — Add `isLive?: boolean` to `VideoPlayerProps` interface (default `false`)

2. **Auto-hide timer** — Change `hideControlsDelayed` timeout from `3000` to `5000`

3. **New control functions** — Add `rewind10()`, `forward10()`, `startOver()` alongside existing `togglePlay()` and `seek()`
   - `rewind10`: `video.currentTime = Math.max(0, video.currentTime - 10)`
   - `forward10`: `video.currentTime = Math.min(duration, video.currentTime + 10)`
   - `startOver`: For VOD → `video.currentTime = 0`; for live → `player.seekRange().start`; auto-plays if paused

4. **Live start position** — Skip `startPosition` application when `isLive` is true (Shaka starts at live edge by default)

5. **Bottom control bar layout** — Three groups:
   - Left: Rewind 10s → Play/Pause → Forward 10s → Start Over (transport)
   - Center: Time display (VOD) or LIVE badge with pulsing red dot (live)
   - Right: Volume → Fullscreen (utility, unchanged)

6. **Seek bar** — Conditionally hidden when `isLive` is true

7. **SVG icons** — Inline SVGs:
   - Rewind 10s: Counterclockwise circular arrow with "10" text
   - Forward 10s: Clockwise circular arrow with "10" text
   - Start Over: Refresh/restart arrow
   - Play/Pause: Existing icons (unchanged)

### File: `frontend-client/src/pages/PlayerPage.tsx`

**Changes:**

1. Add `isLive={type === 'live'}` prop to `<VideoPlayer>` invocation — evaluates to `false` for current `movie`/`episode` routes, `true` when live routes are added

## Verification

1. Navigate to title detail → click Play → video starts from 0:00
2. Hover over player → control bar shows with: Rewind 10s | Play/Pause | Forward 10s | Start Over
3. Stop mouse → controls hide after 5 seconds
4. Move mouse → controls reappear
5. Click Rewind 10s → position jumps back 10s (clamped to 0)
6. Click Forward 10s → position jumps forward 10s (clamped to duration)
7. Click Start Over → restarts from 0:00 and auto-plays
8. Click Play/Pause → toggles playback
9. Seek bar, volume, fullscreen still work
10. Bookmark reporting still fires every 10 seconds
