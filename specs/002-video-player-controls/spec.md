# Feature Specification: Video Player Controls

**Feature Branch**: `002-video-player-controls`
**Created**: 2026-02-09
**Status**: Draft
**Input**: User description: "I want to develop video player functionality based on the generic-juggling-rain plan in the /plans folder."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Play On-Demand Content from Beginning (Priority: P1)

A viewer navigates to a movie or episode detail page and clicks Play. The video player opens and begins playing the content from the very beginning (position 0:00). The viewer sees the video fill the screen with a control bar overlaid at the bottom.

**Why this priority**: Playback from the beginning is the core video player function — without it, no other control features are meaningful.

**Independent Test**: Can be tested by navigating to any title with a valid playback URL, pressing Play, and confirming video starts at 0:00.

**Acceptance Scenarios**:

1. **Given** a movie with a valid playback URL, **When** the viewer clicks Play on the title detail page, **Then** the video player opens and playback starts from the beginning (0:00)
2. **Given** an episode with a valid playback URL, **When** the viewer clicks Play, **Then** the video player opens and playback starts from the beginning (0:00)
3. **Given** a title with no playback URL, **When** the viewer reaches the player page, **Then** an appropriate error message is displayed with an option to go back

---

### User Story 2 - Transport Controls (Rewind, Play/Pause, Forward, Start Over) (Priority: P1)

While watching content, the viewer uses transport controls to navigate playback. The control bar displays four buttons in order from left to right: Rewind 10 seconds, Play/Pause, Forward 10 seconds, and Start Over. Each button has a recognizable icon that clearly communicates its purpose.

**Why this priority**: Transport controls are essential to the viewing experience — viewers need the ability to pause, skip, and restart content.

**Independent Test**: Can be tested by playing any content, hovering to reveal the control bar, and clicking each button to verify its behavior.

**Acceptance Scenarios**:

1. **Given** a video is playing, **When** the viewer clicks Rewind 10s, **Then** playback jumps back 10 seconds from the current position
2. **Given** a video is at position less than 10 seconds, **When** the viewer clicks Rewind 10s, **Then** playback jumps to the beginning (0:00) rather than a negative value
3. **Given** a video is playing, **When** the viewer clicks Play/Pause, **Then** playback pauses and the icon changes to indicate Play state
4. **Given** a video is paused, **When** the viewer clicks Play/Pause, **Then** playback resumes and the icon changes to indicate Pause state
5. **Given** a video is playing, **When** the viewer clicks Forward 10s, **Then** playback jumps forward 10 seconds from the current position
6. **Given** a video is near the end (less than 10 seconds remaining), **When** the viewer clicks Forward 10s, **Then** playback jumps to the end of the content
7. **Given** a video is playing or paused, **When** the viewer clicks Start Over, **Then** playback restarts from the beginning (0:00) and automatically begins playing

---

### User Story 3 - Control Bar Visibility on Hover (Priority: P1)

While watching content, the control bar appears when the viewer moves their mouse over the video player and automatically hides after 5 seconds of mouse inactivity. This keeps the viewing experience immersive while providing easy access to controls.

**Why this priority**: Control visibility is fundamental to the player UX — without it, viewers either can't access controls or controls permanently obstruct the video.

**Independent Test**: Can be tested by playing content, moving the mouse to show controls, then stopping mouse movement and timing the 5-second hide delay.

**Acceptance Scenarios**:

1. **Given** a video is playing with controls hidden, **When** the viewer moves the mouse over the player, **Then** the control bar becomes visible
2. **Given** controls are visible, **When** the viewer stops moving the mouse for 5 seconds, **Then** the control bar fades out
3. **Given** the video is paused, **When** the viewer stops moving the mouse, **Then** the control bar remains visible (does not auto-hide while paused)
4. **Given** controls are hidden, **When** the viewer moves the mouse again, **Then** the control bar reappears immediately

---

### User Story 4 - Live Content Playback (Priority: P2)

A viewer plays live content (when available). The video starts at the live point (current broadcast position) rather than the beginning. The seek bar is hidden since arbitrary seeking is not applicable for live streams, and a "LIVE" badge is displayed instead of the time counter.

**Why this priority**: Live content playback is a future capability (no live routes exist yet), but the player architecture should support it from the start.

**Independent Test**: Can be tested by navigating to a live content URL (when live routes are added) and confirming playback starts at the live edge with the LIVE badge visible.

**Acceptance Scenarios**:

1. **Given** a live stream, **When** the player loads, **Then** playback begins at the live edge (most recent point in the broadcast)
2. **Given** a live stream is playing, **When** the viewer looks at the control bar, **Then** a "LIVE" badge with a pulsing red dot is shown instead of the elapsed/total time
3. **Given** a live stream is playing, **When** the control bar is visible, **Then** the seek bar is hidden
4. **Given** a live stream, **When** the viewer clicks Start Over, **Then** playback jumps to the beginning of the available live buffer

---

### Edge Cases

- What happens when the viewer rapidly clicks Rewind or Forward multiple times? Each click should incrementally adjust position by 10 seconds.
- What happens when the viewer clicks Forward 10s at the very end of the content? Playback should move to the end, triggering the ended event.
- What happens when Start Over is clicked while the video is paused? Playback should restart from 0:00 and automatically begin playing.
- What happens when the viewer moves the mouse while the 5-second hide timer is counting down? The timer should reset, keeping controls visible for another 5 seconds.
- What happens when the playback URL fails to load? An error state should be shown with an option to go back.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The player MUST start on-demand content (movies and episodes) from the beginning (position 0:00)
- **FR-002**: The player MUST start live content at the live edge (current broadcast point)
- **FR-003**: The control bar MUST contain, from left to right: Rewind 10s, Play/Pause, Forward 10s, Start Over buttons
- **FR-004**: Each control button MUST have a visually distinct icon that communicates its function without text labels
- **FR-005**: The Rewind 10s button MUST move playback position back by 10 seconds, clamped to 0:00
- **FR-006**: The Forward 10s button MUST move playback position forward by 10 seconds, clamped to content duration
- **FR-007**: The Play/Pause button MUST toggle between playing and paused states with corresponding icon changes
- **FR-008**: The Start Over button MUST restart playback from the beginning and auto-play
- **FR-009**: The control bar MUST appear when the viewer hovers (moves mouse) over the player area
- **FR-010**: The control bar MUST automatically hide after 5 seconds of mouse inactivity during playback
- **FR-011**: The control bar MUST remain visible while the video is paused (no auto-hide)
- **FR-012**: For live content, the seek bar MUST be hidden
- **FR-013**: For live content, a "LIVE" badge MUST be displayed in place of the time counter
- **FR-014**: For on-demand content, a seek bar and elapsed/total time display MUST remain available
- **FR-015**: Existing player features (volume control, fullscreen toggle, seek bar) MUST continue to work

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Viewers can play on-demand content starting from the beginning in 100% of cases where a valid playback URL exists
- **SC-002**: All four transport control buttons are visible in the control bar when hovering over the player
- **SC-003**: The control bar hides within 5 seconds (with 0.5 second tolerance) after the last mouse movement during playback
- **SC-004**: Rewind and Forward buttons adjust playback position by exactly 10 seconds per click
- **SC-005**: Start Over returns playback to 0:00 and resumes playing within 1 second
- **SC-006**: All existing player functionality (volume, fullscreen, seek bar, bookmark reporting) remains fully operational after the changes
