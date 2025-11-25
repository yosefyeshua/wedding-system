## Purpose
This repo is a small Flask-based wedding planning helper (tasks + budget). These instructions give an AI coding agent the minimal, actionable context to make safe, project-specific changes quickly.

## Big picture
- **Single-module Flask app**: main logic lives in `app.py` (no blueprints). UI is server-rendered via Jinja templates in `templates/`.
- **Persistence**: local SQLite file `database.db` (created with `create_db.py`). DB access is direct via `sqlite3` and `get_db_connection()` in `app.py`.
- **Language & UI**: templates and user-facing strings are in Hebrew. Status values are Hebrew literals (`"חדש"`, `"בתהליך"`, `"בוצע"`).

## Quick dev & debug commands (Windows PowerShell)
- Create DB schema (run once):
  `python .\create_db.py`
- Run the app (dev):
  `python .\app.py`  # serves on port 5001 by default (debug=True)
- Dependencies: install Flask in a venv: `python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install Flask`

## Key files and what to change where
- `app.py`: all HTTP routes and business logic. Important functions:
  - `get_db_connection()` — opens `database.db` and sets `row_factory` to `sqlite3.Row`.
  - Routes: `/tasks`, `/tasks/create` (POST), `/tasks/<id>/edit` (POST), `/tasks/<id>/delete` (POST), `/budget`, `/budget/add` (POST).
- `create_db.py`: creates `tasks(id,title,status)` and `expenses(id,description,amount)` tables. Run this to create `database.db`.
- `templates/tasks.html`, `templates/budget.html`: Jinja templates. Templates expect `tasks`, `expenses`, and `total` variables from routes.

## Data flows & conventions (examples from code)
- Read flow: routes call `get_db_connection()`, perform `SELECT` and pass rows to `render_template()`.
- Write flow: POST handlers call `execute(...)`, `conn.commit()`, `conn.close()` and redirect.
- Status values are stored as plain text in the `tasks.status` column; code compares exact Hebrew strings (do not localize these without updating UI and tests).
- Template usage: forms post directly to route paths (no JS required). Example: task edit form posts to `/tasks/{{ task.id }}/edit`.

## Integration points / external dependencies
- No external APIs. Only runtime dependency is `Flask` (plus Python stdlib `sqlite3`).
- The app expects to run with CWD = repo root so `database.db` is at the project root.

## Safety notes for automated edits
- Do not change the DB filename unless you update `create_db.py` and all `sqlite3.connect(...)` calls.
- Preserve Hebrew status literals or update both templates and route logic together.
- The app currently runs `debug=True` in `app.py`. If creating PRs for production changes, flip debug off and add environment-based config.

## Where to add tests or new features
- Small features: add route handlers in `app.py` and corresponding template fragments in `templates/`.
- For DB migrations or schema changes, update `create_db.py` and include a migration step that preserves existing data.

## Example edits an AI agent might make
- Add a `completed_at` timestamp to `tasks`: update `create_db.py`, modify `app.py` insert/update queries, and add a column display in `templates/tasks.html`.
- Add server-side validation for `amount` in `/budget/add`: validate numeric and return errors to template.

## Questions for maintainers
- Should `debug=True` be removed for staging/production? Where should a `.env` file live?
- Any preferred coding style or branching/PR workflow? (no CI config found)

Please review and tell me which parts you want expanded or adjusted.
