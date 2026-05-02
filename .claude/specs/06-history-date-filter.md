# Spec 06: History Date Filter

## Goal
Allow users to narrow the history tab to a specific date range (start date to end date) so they can review progress over a specific period without scrolling through all past sessions.

## Files
- `src/app.py` - add date range picker UI to the history tab; pass date params to `get_session_history()`.
- `src/tracker.py` - extend `get_session_history()` to accept optional `start_date` and `end_date` filters.

## Design

### Date Range Picker (History Tab)
Render two `st.date_input` widgets side-by-side (using `st.columns([1, 1])`) above the existing topic filter in the history tab.

- Left column: "From" date, default = 30 days before today.
- Right column: "To" date, default = today.
- Both are optional; leaving either blank omits that bound from the SQL query.
- Validation: if `start_date > end_date`, show `st.warning("Start date must be before end date.")` and skip the query.
- Date values stored in local widget state only (no `st.session_state` keys needed; Streamlit re-runs on change).

### DB Query Extension
`get_session_history()` gains two optional parameters: `start_date` and `end_date` (Python `date` objects). The SQL `WHERE` clause appends:
- `AND DATE(submitted_at) >= :start_date` when `start_date` is provided.
- `AND DATE(submitted_at) <= :end_date` when `end_date` is provided.

`submitted_at` is stored as ISO-8601 text (`YYYY-MM-DD HH:MM:SS`) in SQLite, so `DATE()` extracts the date part correctly without schema changes.

## Functions / Classes

| Name | Signature | Returns | Notes |
|------|-----------|---------|-------|
| `get_session_history` | `(user_id: int, topic: str \| None, limit: int = 50, start_date: date \| None = None, end_date: date \| None = None) -> list[dict]` | List of session dicts | `tracker.py`; existing signature extended; backward-compatible |
| `render_history_tab` | `() -> None` (modified) | None | `app.py`; reads date_input widget values, validates range, passes to `get_session_history()` |

## Constraints
- No schema changes to `sessions` table; filter uses `DATE(submitted_at)` on the existing text column.
- All DB ops via `tracker.py` only.
- No sidebar; all UI in main column.
- Date filter applies on top of the existing topic filter (both active simultaneously).
- Limit of 50 rows applies after both filters.
- If no sessions match the date range, render `st.info("No sessions found for the selected date range.")`.
- All new UI elements must match the existing dark theme and accent colors.
- Score and difficulty invariants unchanged.

## Acceptance Criteria
- History tab shows "From" and "To" date pickers above the topic filter.
- Default range is the last 30 days; both bounds are independently adjustable.
- Selecting a valid range filters the table to sessions with `submitted_at` within that range.
- Combining a date range with a topic filter returns only rows matching both conditions.
- Setting `start_date > end_date` shows a warning and renders no table.
- Clearing both date inputs (if widgets allow blank) falls back to showing all sessions up to the 50-row limit.
- No regression in skip, hint, or difficulty picker behavior.
