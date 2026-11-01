# Wine Notes

A GNOME desktop application for recording, rating, and managing personal wine tasting notes. Built with Python, GTK 4, Libadwaita, and SQLite.

![Wine Notes Icon](data/icons/hicolor/scalable/apps/org.jubba.WineNotes.svg)

## Features

- **Native GNOME Experience**: Follows the GNOME Human Interface Guidelines (HIG) with modern Libadwaita widgets (`Adw.NavigationSplitView`, `Adw.PreferencesPage`, `Adw.ToolbarView`, `Adw.AlertDialog`, `Adw.Toast`).
- **Local-First Storage**: Tasting notes are stored in a local SQLite database with WAL mode. The application runs fully offline and requires no external database or network service.
- **Comprehensive Tasting Model**:
  - **Sensory Impressions**: Detailed tasting notes (color, bouquet/nose, palate, acidity, tannins, finish).
  - **Ratings**: 0–100 score scale with 5-star visual indicators and qualitative classification.
  - **Terroir & Origin**: Producer, grape variety, vintage (or Non-Vintage), country, region, and sub-appellation.
  - **Service & Technical**: ABV %, optimal serving temperature, bottle size (standard, half, magnum), closure type (cork, screwcap, glass, synthetic), and organic/biodynamic certifications.
  - **Cellar & Pairing**: Purchase location, price paid, aging potential / drinking window, and food pairing recommendations.
- **Interactive Aroma Wheel**: Explore primary, secondary, and tertiary aromas plus wine faults using a Cairo-rendered flavor wheel. Selected descriptors are stored with each wine as structured keywords.
- **Real-Time Search & Filtering**:
  - Live search filtering across wine names, producers, grape varieties, regions, tasting notes, and aroma keywords.
  - Style filter pills (Red, White, Rosé, Sparkling, Dessert, Fortified).
  - Multi-attribute sorting (Date tasted, Rating, Vintage, Alphabetical).
- **Collection Statistics**: Overview of total wines tasted, average score, highest rated bottle, and style/country distribution.
- **Import & Export**: Back up and move your tasting notes using standard JSON and CSV files.
- **Accidental Deletion Protection**: Delete confirmation with instant toast undo.
- **Desktop Integration**: Includes a `.desktop` launcher and scalable SVG icon for GNOME Shell. Snap packaging is provided in `snap/`.

## Getting Started

### Prerequisites

The application uses Python 3 and native GNOME libraries available on modern Linux distributions such as Ubuntu 24.04+, Fedora, Debian, and Arch.

If they are not already installed:

```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1
```

### Launching the Application

Run from the repository root so the `winenotes` package is importable:

```bash
./main.py
# or
./app.py
# or
python3 main.py
```

### Data Location

The database is stored at `$XDG_DATA_HOME/wine-notes/wines.db`, defaulting to `~/.local/share/wine-notes/wines.db`. Set `WINE_NOTES_DB` to use a different location:

```bash
WINE_NOTES_DB=/tmp/wine-notes-test.db ./main.py
```

### Desktop Menu Integration

To add Wine Notes to your GNOME Applications menu:

```bash
mkdir -p ~/.local/share/icons/hicolor/scalable/apps/ ~/.local/share/applications/
cp data/icons/hicolor/scalable/apps/org.jubba.WineNotes.svg ~/.local/share/icons/hicolor/scalable/apps/
cp org.jubba.WineNotes.desktop ~/.local/share/applications/
update-desktop-database ~/.local/share/applications/
```

### Snap Package

A Snapcraft manifest is available for building and installing the application:

```bash
snapcraft
sudo snap install --dangerous wine-tasting-notes_*.snap
```

## Project Structure

```
wine-tasting-notes-app/
├── winenotes/
│   ├── __init__.py          # Package metadata and application ID
│   ├── app.py               # Adw.Application subclass and lifecycle
│   ├── window.py            # Main adaptive split view and collection actions
│   ├── db.py                # SQLite database manager (WAL mode, queries, migrations)
│   ├── models.py            # Wine dataclass, validation, and formatting helpers
│   ├── sample_data.py       # Sample wines seeded on an empty database
│   ├── wine_row.py          # Collection row item with badges and rating score
│   ├── wine_detail.py       # Wine detail pane
│   ├── wine_dialog.py       # Add and edit form
│   ├── aroma_wheel_data.py  # Aroma taxonomy and generated lookup maps
│   ├── tasting_wheel_widget.py  # Cairo-rendered interactive aroma wheel
│   ├── aroma_dialog.py      # Aroma wheel exploration and keyword selection
│   ├── stats_dialog.py      # Collection statistics dialog
│   ├── changelog_dialog.py  # In-app release history dialog
│   └── style.css            # Custom Libadwaita styling
├── tests/
│   └── test_winenotes.py    # Unit and integration test suite
├── data/icons/              # Application vector SVG icon
├── snap/                    # Snapcraft packaging and launcher assets
├── org.jubba.WineNotes.desktop
├── main.py                  # Direct launcher script
├── app.py                   # Root entry point
└── requirements.txt         # Optional developer tooling
```

## Running Tests

```bash
python3 -m unittest discover -s tests
```

GTK dialog tests require a working display session. For headless environments, use `xvfb-run -a` when available.

## Architecture

Wine Notes is a local, offline-first desktop application:

- Python 3 with PyGObject, GTK 4, and Libadwaita, using only the Python standard library for data handling.
- SQLite for durable local storage, with automatic backward-compatible schema migrations.
- A Cairo-drawn aroma wheel for interactive flavor exploration.
- No runtime pip dependencies, web server, or external database.

## License

MIT License. See [LICENSE](LICENSE).
