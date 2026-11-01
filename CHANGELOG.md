# Changelog

All notable changes to the Wine Tasting Notes application will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Develop

### [1.1.2] - 2026-11-02

### Changed
- Altered the contact form to link to github issues.
- Removed the in-app changelog dialog and hard-coded About release notes; the menu now links to `CHANGELOG.md` on GitHub.

### [1.1.1] - 2026-11-01

### Added
- Snap packaging (`snap/snapcraft.yaml`) using the GNOME extension and its content snap for the PyGObject, Pycairo, GTK 4, and Libadwaita runtime, so the aroma wheel renders without host `python3-gi-cairo`.
- Desktop launcher and application icon for the snap in `snap/gui/`.
- Added `AGENTS.md` for AI assistant workflows and `.gitignore` to exclude Workshop files.

### Fixed
- Aroma wheel segments bleeding into adjacent segments caused by stale Cairo path state from previous labels being connected into the next slice.
- Missing application icon in the About dialog when running from the snap by installing the hicolor icon into the snap runtime.

## [1.1.0] - 2026-10-30

### Added
- **Interactive Wine Tasting Aroma & Flavor Wheel**:
  - Full-featured circular visual flavor wheel rendered via Cairo in GTK 4, based on the classic wine aroma wheel taxonomy.
  - Three concentric hierarchical tiers:
    - **Tier 1 (Sources)**: Primary Aromas, Secondary Aromas, Tertiary Aromas, and Wine Faults.
    - **Tier 2 (Families)**: Flower, Citrus, Tree Fruit, Tropical Fruit, Red Fruit, Black Fruit, Dried Fruit, Noble Rot, Spice, Vegetable, Earth, Microbial, Oak Aging, General Aging, TCA (Corked), Sulfides & Mercaptans, Brettanomyces, Cooked, and Volatile Acidity.
    - **Tier 3 (Descriptors)**: 112 visual flavor and aroma descriptors arranged clockwise with distinctive color coding.
  - Dynamic wheel interaction with hover inspection, live path previews in the center hub, and click-to-toggle selection.
- **Structured Aroma Keyword Tags**:
  - Wines now store and persist structured flavor descriptors (`aroma_notes`) alongside freeform text notes.
  - Category-colored pill badges for tasting keywords displayed in the Wine Detail card and Wine Dialog.
  - Top flavor keywords displayed in the wine list row for at-a-glance scanning.
- **Aroma Wheel Exploration Dialog**:
  - Split-pane interface pairing the circular Cairo wheel with a search bar and category accordion browser.
  - Instant live search highlighting matching aroma sectors on the wheel.
  - Removable keyword chips tray with count and "Clear All" action.
  - "Append Keywords to Notes Description" helper that composes natural language tasting sentences into the notes editor.
- **Main Menu Quick Actions**:
  - Added "Wine Aroma Wheel Reference" to the main window menu for exploring flavors anytime.
  - Added "What's New (Changelog)" dialog to review version history in-app.
- **Search & Filter Enhancement**:
  - Global search now queries both freeform tasting notes and structured aroma keywords.
- **Data Export & Import**:
  - JSON and CSV export/import updated to include aroma keywords.

### Changed
- Improved SQLite database schema with automatic backward-compatible migration for existing databases.
- Updated curated sample wines with rich flavor descriptors and notes.
- Updated `Adw.AboutDialog` to include native release notes.

## [1.0.0] - 2026-10-29

### Added
- Initial release of Wine Tasting Notes GNOME application built with GTK 4 and Libadwaita.
- Adaptive split-view layout (`Adw.NavigationSplitView`) for desktop and mobile form factors.
- Wine collection management: record wine name, winery, origin (country, region, sub-region), vintage, grape variety, style (Red, White, Rosé, Sparkling, Dessert, Fortified), ABV, price, rating (0-100), serving temperature, closure type, and farming practices (Organic, Biodynamic).
- Fast local storage with zero-dependency SQLite and WAL mode.
- Collection statistics dialog with average rating, style distribution, top countries, and top grapes.
- Data import and export for JSON and CSV formats.
- Sample wine dataset seeding.
- Full dark mode and light mode theming integration.
