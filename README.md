# 🍷 Wine Notes — GNOME Wine Tasting Application

An elegant, modern GNOME desktop application for recording, rating, and managing personal wine tasting notes. Built with Python, **GTK 4**, **Libadwaita**, and **SQLite**.

![Wine Notes Icon](data/icons/hicolor/scalable/apps/org.jubba.WineNotes.svg)

---

## ✨ Features

- **Native GNOME Experience**: Follows GNOME Human Interface Guidelines (HIG) with modern Libadwaita widgets (`Adw.NavigationSplitView`, `Adw.PreferencesPage`, `Adw.ToolbarView`, `Adw.AlertDialog`, `Adw.Toast`).
- **Zero Configuration & Embedded Storage**: Powered by local SQLite in WAL mode stored at `~/.local/share/wine-notes/wines.db`—no MySQL server, no `.env` setup, and no SSL certificates required.
- **Comprehensive Tasting Model**:
  - **Sensory Impressions**: Detailed tasting notes (color, bouquet/nose, palate, acidity, tannins, finish).
  - **Ratings**: 0–100 score scale with 5-star visual indicators and qualitative classification.
  - **Terroir & Origin**: Producer, grape variety, vintage (or Non-Vintage), country, region, and sub-appellation.
  - **Service & Technical**: ABV %, optimal serving temperature, bottle size (standard, half, magnum), closure type (cork, screwcap, glass, synthetic), and organic/biodynamic certifications.
  - **Cellar & Pairing**: Purchase location, price paid, aging potential / drinking window, and food pairing recommendations.
- **Real-Time Search & Filtering**:
  - Live search filtering across wine names, producers, grape varieties, regions, and tasting notes.
  - Style filter pills (Red, White, Rosé, Sparkling, Dessert, Fortified).
  - Multi-attribute sorting (Date tasted, Rating, Vintage, Alphabetical).
- **Collection Statistics**: Overview of total wines tasted, average score, highest rated bottle, and style/country distribution.
- **Import & Export**: Backup and migrate your tasting notes via standard JSON and CSV files.
- **Accidental Deletion Protection**: Delete confirmation with instant toast undo.
- **Desktop Integration**: Includes `.desktop` launcher and scalable SVG icon for GNOME Shell.

---

## 🚀 Getting Started

### Prerequisites

The application uses standard Python 3 and native GNOME libraries pre-installed on modern Linux distributions (such as Ubuntu 24.04+, Fedora, Debian, and Arch).

If not already installed:
```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1
```

### Launching the Application

Simply run:
```bash
./main.py
# or
./app.py
# or
python3 main.py
```

### Desktop Menu Integration

To integrate Wine Notes into your GNOME Applications menu:
```bash
mkdir -p ~/.local/share/icons/hicolor/scalable/apps/ ~/.local/share/applications/
cp data/icons/hicolor/scalable/apps/org.jubba.WineNotes.svg ~/.local/share/icons/hicolor/scalable/apps/
cp org.jubba.WineNotes.desktop ~/.local/share/applications/
update-desktop-database ~/.local/share/applications/
```

---

## 📁 Project Structure

```
wine-tasting-notes-app/
├── winenotes/
│   ├── __init__.py          # Package metadata & app ID (org.jubba.WineNotes)
│   ├── app.py               # Adw.Application subclass & lifecycle
│   ├── db.py                # SQLite database manager (WAL mode, queries, migrations)
│   ├── models.py            # Wine dataclass, validation & formatting helpers
│   ├── sample_data.py       # Curated real-world sample wines (Bordeaux, Burgundy, etc.)
│   ├── style.css            # Custom Libadwaita styling for badges, pills, and cards
│   ├── window.py            # Main Adw.ApplicationWindow with adaptive split view
│   ├── wine_detail.py       # Rich detail pane (PreferencesGroups, tasting notes card)
│   ├── wine_dialog.py       # Add & Edit modal dialog with Adw form controls
│   ├── wine_row.py          # Custom ListBox row item with badges and rating score
│   └── stats_dialog.py      # Collection tasting statistics modal
├── tests/
│   └── test_winenotes.py    # Unit & integration test suite
├── legacy/                  # Archived original Flask / MySQL prototype
│   ├── config.py
│   ├── flask_app.py
│   ├── simple_cli.py
│   └── templates/
├── data/icons/              # Application vector SVG icon
├── org.jubba.WineNotes.desktop
├── main.py                  # Direct launcher script
├── app.py                   # Root entry point
└── requirements.txt         # Environment prerequisites
```

---

## 🧪 Running Tests

Run the test suite:
```bash
python3 -m unittest discover -s tests
```

---

## 🏛️ Architecture Note (Why This Optimization?)

The previous prototype relied on Flask and a remote MySQL server with SSL certificates and manual browser form submissions. For a personal wine tasting notebook on GNOME Linux, this had several issues:
1. Required external database hosting, network connectivity, and running local web servers.
2. Clunky browser UI with full-page refreshes and disconnected theme styling.
3. Incomplete dependencies (`flask` and `mysql-connector-python` were missing or broken in the desktop environment).

The new architecture uses **Python + GTK 4 + Libadwaita + local SQLite**:
- **Zero external pip dependencies required** to run on a GNOME desktop.
- **Fast, offline-first local storage** with automatic sample seeding on first launch.
- **Instant responsive UI** with native GNOME dark/light theme switching, smooth animations, and desktop keyboard shortcuts.
- **Safely preserved history**: All original Flask scripts and templates remain archived under `legacy/`.

---

## 📜 License

MIT License.
