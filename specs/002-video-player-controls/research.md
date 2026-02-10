# Research: Video Player Controls

**Feature**: 002-video-player-controls
**Date**: 2026-02-09

## Findings

No NEEDS CLARIFICATION items were identified. All technologies and patterns are already established in the codebase.

### Decision 1: Transport control icons

- **Decision**: Use inline SVGs with circular arrow + "10" text for rewind/forward, refresh arrow for start over
- **Rationale**: Project uses no icon library — all existing icons are inline SVGs. Circular arrow with text number is the standard pattern used by YouTube, Netflix, and most streaming players for skip-back/skip-forward
- **Alternatives considered**: Heroicons (project doesn't use them as a library), simple arrow icons without "10" label (less clear), Lucide icons (would add dependency)

### Decision 2: Auto-hide timer duration

- **Decision**: 5 seconds (per spec requirement)
- **Rationale**: Industry standard ranges from 3-5s. The existing implementation used 3s. The spec explicitly requires 5s, which gives viewers more time to locate controls
- **Alternatives considered**: Keeping 3s (doesn't meet spec)

### Decision 3: Live content seek behavior

- **Decision**: Use Shaka Player's `seekRange().start` for Start Over on live content
- **Rationale**: Shaka Player exposes the live buffer range via `seekRange()`. This is the correct API to find the earliest seekable point in a live stream
- **Alternatives considered**: Hardcoding a time offset (fragile, depends on buffer size), disabling Start Over for live (reduces functionality)

### Decision 4: Control bar layout (3-group design)

- **Decision**: Transport controls left, time/LIVE center, utility controls right
- **Rationale**: Standard video player convention. Matches Netflix, YouTube, Disney+ patterns. Transport controls are most frequently used so they're on the primary side (left)
- **Alternatives considered**: Single left-aligned row (crowded), centered transport with time beside (unusual pattern)
