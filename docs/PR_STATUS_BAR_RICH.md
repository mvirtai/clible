# PR: Rich Status Bar & Main Menu Refresh

## Summary

Adds a Rich-based status bar that shows current user and session metadata, and refreshes it every time the main menu is shown after returning from submenus.

## Changes

### CLI (`app/cli.py`)

- Refresh status bar at the start of each main-menu loop iteration so the panel re-renders after coming back from submenus.

### Status Bar (`app/status_bar.py`)

- Render status with a Rich panel.
- Show user name and user ID.
- Show session name and meta (id, saved/temp, scope) or “no session” when none.
- Removed unused `self.db`; uses `AppState` + `QueryDB` lookups for current entities.

## Testing

- Manual: `uv run clible -u "vv"`
  - Panel renders immediately with user info.
  - Returning from submenus reprints the panel with up-to-date state.
  - No crashes observed.

## Notes

- Panel stays compact (padding 0).
- Designed to be low-noise but informative; can be extended with icons (💾/⏳) later.
