# AGENTS.md

Guidance for agents contributing to Wine Notes, a GNOME desktop application for
recording and managing wine tasting notes.

## Project Summary

- Python 3 + PyGObject + GTK 4 + Libadwaita + SQLite.
- No runtime pip dependencies. GTK, Libadwaita, and cairo come from system
  packages or the Snap GNOME extension.
- Local, offline-first application. Do not introduce a server, network service,
  or external database.
- Entry points are `main.py` and `app.py`; both call `winenotes.app.main()`.

## Commands

Run from the repository root so the `winenotes` package is importable.

```bash
./main.py
python3 main.py
python3 -m unittest discover -s tests
python3 -m compileall -q winenotes tests
```

Use an isolated database when manually testing:

```bash
WINE_NOTES_DB=/tmp/wine-notes-test.db ./main.py
```

The test suite uses `unittest`; pytest is optional tooling, not the primary
runner. GTK dialog tests need a working display/session. If running headless,
use `xvfb-run -a` when available.

Optional style tools are listed in `requirements.txt` (`black`, `flake8`), but
there is no project config for them. Do not reformat unrelated files.

## Architecture

- `winenotes/__init__.py`: package version and application ID
  (`org.jubba.WineNotes`).
- `winenotes/app.py`: `Adw.Application` lifecycle, CSS loading, app-level
  actions, About dialog.
- `winenotes/window.py`: main adaptive split view, sidebar, collection actions,
  import/export flows.
- `winenotes/models.py`: `Wine` dataclass, validation, display helpers,
  row/dict conversion.
- `winenotes/db.py`: SQLite schema, connection handling, CRUD, search, stats,
  seeding, JSON/CSV import/export.
- `winenotes/sample_data.py`: seed wines used only when the database is empty.
- `winenotes/wine_row.py`, `wine_detail.py`, `wine_dialog.py`: collection row,
  detail pane, and add/edit form.
- `winenotes/aroma_wheel_data.py`: aroma taxonomy source data and generated
  lookup maps.
- `winenotes/tasting_wheel_widget.py`: custom Cairo-drawn interactive wheel.
- `winenotes/aroma_dialog.py`: aroma wheel exploration and keyword selection.
- `winenotes/stats_dialog.py`: collection statistics dialog.
- `winenotes/style.css`: custom Libadwaita CSS, loaded globally at startup.
- `tests/test_winenotes.py`: model, database, aroma data, and dialog tests.
- `snap/`: Snapcraft packaging and launcher assets.

## Data and Database Changes

- Database location defaults to
  `$XDG_DATA_HOME/wine-notes/wines.db` or `~/.local/share/wine-notes/wines.db`.
  `WINE_NOTES_DB` overrides it.
- SQLite runs in WAL mode. Use parameterized queries and the existing
  `_get_connection()` context manager.
- The schema lives in `db.py`. If adding a column, update all relevant places:
  `SCHEMA`, `Database.init_db()` migration, `insert()`, `update()`,
  export field lists, `Wine` fields, `Wine.from_row()`/`to_dict()`, UI forms,
  and tests.
- Existing databases must keep working. Add backward-compatible migrations in
  `init_db()` rather than replacing a table.
- Seed data must remain idempotent; `seed_samples()` already checks for existing
  wines.
- `is_sample` marks seeded sample wines in SQLite. It is intentionally not part
  of `Wine` or exports; use `insert(..., is_sample=True)` when restoring samples.
- `aroma_notes` is stored as a JSON string in SQLite and exposed as `List[str]`
  on `Wine`.

## Model Conventions

- `Wine` is the single source of truth for tasting-note fields.
- Ratings are integers from 0 to 100. Styles are defined by `COLOR_STYLES`;
  closures by `CLOSURE_TYPES`.
- Keep `validate()` messages user-facing and covered by tests when adding rules.
- Preserve `Wine.from_row()` tolerance for missing/legacy fields.

## GTK and UI Conventions

- This is GTK 4 / Libadwaita 1. Do not use GTK 3 patterns such as
  `Gtk.Dialog.run()`, `show_all()`, or legacy container packing.
- Use `Adw.Dialog` for modal dialogs and `present()` to show them.
- Use `Gtk.Box.append()`/`prepend()`, `set_child()`, and modern action/event
  APIs.
- Prefer native Libadwaita widgets already used in the codebase
  (`Adw.ToolbarView`, `Adw.PreferencesPage`, `Adw.AlertDialog`, `Adw.Toast`,
  `Adw.NavigationSplitView`).
- Add custom styling to `winenotes/style.css`; reuse existing classes where
  possible. Badge/category classes must stay in sync with data helpers.
- Keep UI text concise and consistent with existing GNOME-style labels.
- Do not block the GTK main loop with long-running work.

## Aroma Wheel

- `AROMA_CATEGORIES_DATA` is the source of truth. `SUBCATEGORIES`,
  `DESCRIPTOR_MAP`, `CATEGORY_MAP`, and ordered descriptor lists are generated
  from it at import time.
- Add or edit descriptors in `AROMA_CATEGORIES_DATA`; the wheel geometry is
  recomputed automatically.
- `DESCRIPTOR_MAP` keeps the first occurrence when a descriptor appears twice.
  The existing duplicate `"Dried Fruit"` is intentional. Avoid new duplicates
  unless the selection behavior is understood and tested.
- When adding a category, update the CSS category mapping in
  `aroma_wheel_data.py` and the matching class in `style.css` if needed.
- The wheel is Cairo-drawn in `TastingWheelWidget`; keep hit testing, drawing
  order, and angle normalization consistent when changing layout.

## Versioning and Releases

Keep these version references synchronized:

- `winenotes/__init__.py` (`__version__`)
- `snap/snapcraft.yaml` (`version`)
- `CHANGELOG.md` (Keep a Changelog format; use `## Develop` for unreleased work)

The in-app Changelog menu item links to `CHANGELOG.md` on GitHub; there is no
separate in-app release history to maintain. The changelog test expects the
published version strings to remain in `CHANGELOG.md`. Update that test when
changing the supported release history.

## Quality Checklist

Before finishing a change:

1. Run `python3 -m compileall -q winenotes tests`.
2. Run `python3 -m unittest discover -s tests`.
3. Manually smoke-test affected UI when possible, especially add/edit/delete,
   search/filter, aroma wheel selection, import/export, stats, and the
   changelog link.
4. If the schema changed, test against an existing database, not only a fresh
   one.
5. Do not commit generated databases, exports, caches, or Snap build artifacts.
6. Keep unrelated working-tree changes intact; the repository may contain
   in-progress edits.
