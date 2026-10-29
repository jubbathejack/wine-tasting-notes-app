"""
SQLite database management for Wine Tasting Notes.
Zero-dependency, fast, robust local storage with WAL mode.
"""

from __future__ import annotations
import os
import sqlite3
import json
import csv
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from winenotes.models import Wine, COLOR_STYLES
from winenotes.sample_data import SAMPLE_WINES

SCHEMA = """
CREATE TABLE IF NOT EXISTS wines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    wine_name TEXT NOT NULL,
    winery TEXT NOT NULL,
    country TEXT NOT NULL,
    region TEXT,
    sub_region TEXT,
    vintage INTEGER,
    color_style TEXT NOT NULL CHECK(color_style IN ('Red', 'White', 'Rosé', 'Sparkling', 'Dessert', 'Fortified')),
    grape_variety TEXT NOT NULL,
    abv REAL,
    price REAL,
    tasting_date TEXT NOT NULL,
    rating INTEGER NOT NULL CHECK(rating >= 0 AND rating <= 100),
    tasting_notes TEXT NOT NULL,
    serving_temperature INTEGER,
    aging_potential TEXT,
    food_pairing TEXT,
    purchase_location TEXT,
    bottle_size REAL DEFAULT 0.75,
    closure_type TEXT CHECK(closure_type IN ('Cork', 'Screwcap', 'Glass', 'Synthetic', NULL)),
    organic INTEGER DEFAULT 0,
    biodynamic INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_wines_name ON wines(wine_name);
CREATE INDEX IF NOT EXISTS idx_wines_winery ON wines(winery);
CREATE INDEX IF NOT EXISTS idx_wines_color ON wines(color_style);
CREATE INDEX IF NOT EXISTS idx_wines_rating ON wines(rating);
CREATE INDEX IF NOT EXISTS idx_wines_date ON wines(tasting_date);
"""

class Database:
    def __init__(self, db_path: Optional[str | Path] = None):
        if db_path:
            self.db_path = Path(db_path)
        elif "WINE_NOTES_DB" in os.environ:
            self.db_path = Path(os.environ["WINE_NOTES_DB"])
        else:
            xdg_data = os.environ.get("XDG_DATA_HOME")
            base_dir = Path(xdg_data) if xdg_data else Path.home() / ".local" / "share"
            self.db_path = base_dir / "wine-notes" / "wines.db"

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def init_db(self) -> None:
        with self._get_connection() as conn:
            conn.executescript(SCHEMA)

    def count(self) -> int:
        with self._get_connection() as conn:
            row = conn.execute("SELECT COUNT(*) FROM wines").fetchone()
            return row[0] if row else 0

    def insert(self, wine: Wine) -> int:
        query = """
        INSERT INTO wines (
            wine_name, winery, country, region, sub_region, vintage,
            color_style, grape_variety, abv, price, tasting_date,
            rating, tasting_notes, serving_temperature, aging_potential,
            food_pairing, purchase_location, bottle_size, closure_type,
            organic, biodynamic
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            wine.wine_name.strip(),
            wine.winery.strip(),
            wine.country.strip(),
            wine.region.strip() if wine.region else None,
            wine.sub_region.strip() if wine.sub_region else None,
            wine.vintage,
            wine.color_style,
            wine.grape_variety.strip() if wine.grape_variety else "",
            wine.abv,
            wine.price,
            wine.tasting_date,
            wine.rating,
            wine.tasting_notes.strip(),
            wine.serving_temperature,
            wine.aging_potential.strip() if wine.aging_potential else None,
            wine.food_pairing.strip() if wine.food_pairing else None,
            wine.purchase_location.strip() if wine.purchase_location else None,
            wine.bottle_size if wine.bottle_size else 0.75,
            wine.closure_type,
            1 if wine.organic else 0,
            1 if wine.biodynamic else 0,
        )
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(query, params)
            wine_id = cur.lastrowid
            wine.id = wine_id
            return wine_id

    def update(self, wine: Wine) -> bool:
        if wine.id is None:
            raise ValueError("Wine must have an ID to update.")
        query = """
        UPDATE wines SET
            wine_name = ?, winery = ?, country = ?, region = ?, sub_region = ?,
            vintage = ?, color_style = ?, grape_variety = ?, abv = ?, price = ?,
            tasting_date = ?, rating = ?, tasting_notes = ?, serving_temperature = ?,
            aging_potential = ?, food_pairing = ?, purchase_location = ?,
            bottle_size = ?, closure_type = ?, organic = ?, biodynamic = ?,
            updated_at = datetime('now')
        WHERE id = ?
        """
        params = (
            wine.wine_name.strip(),
            wine.winery.strip(),
            wine.country.strip(),
            wine.region.strip() if wine.region else None,
            wine.sub_region.strip() if wine.sub_region else None,
            wine.vintage,
            wine.color_style,
            wine.grape_variety.strip() if wine.grape_variety else "",
            wine.abv,
            wine.price,
            wine.tasting_date,
            wine.rating,
            wine.tasting_notes.strip(),
            wine.serving_temperature,
            wine.aging_potential.strip() if wine.aging_potential else None,
            wine.food_pairing.strip() if wine.food_pairing else None,
            wine.purchase_location.strip() if wine.purchase_location else None,
            wine.bottle_size if wine.bottle_size else 0.75,
            wine.closure_type,
            1 if wine.organic else 0,
            1 if wine.biodynamic else 0,
            wine.id,
        )
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(query, params)
            return cur.rowcount > 0

    def delete(self, wine_id: int) -> bool:
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM wines WHERE id = ?", (wine_id,))
            return cur.rowcount > 0

    def get_by_id(self, wine_id: int) -> Optional[Wine]:
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM wines WHERE id = ?", (wine_id,)).fetchone()
            if row:
                return Wine.from_row(dict(row))
        return None

    def list_wines(
        self,
        search: str = "",
        style_filter: Optional[str] = None,
        sort_by: str = "date_desc",
    ) -> List[Wine]:
        clauses = []
        params: List[Any] = []

        if search and search.strip():
            term = f"%{search.strip()}%"
            clauses.append(
                "("
                "wine_name LIKE ? OR winery LIKE ? OR grape_variety LIKE ? "
                "OR region LIKE ? OR country LIKE ? OR tasting_notes LIKE ? OR CAST(vintage AS TEXT) LIKE ?"
                ")"
            )
            params.extend([term, term, term, term, term, term, term])

        if style_filter and style_filter != "All":
            clauses.append("color_style = ?")
            params.append(style_filter)

        where_clause = f"WHERE {' AND '.join(clauses)}" if clauses else ""

        sort_map = {
            "date_desc": "tasting_date DESC, id DESC",
            "date_asc": "tasting_date ASC, id ASC",
            "rating_desc": "rating DESC, tasting_date DESC",
            "rating_asc": "rating ASC, tasting_date DESC",
            "vintage_desc": "vintage DESC NULLS LAST, id DESC",
            "name_asc": "wine_name COLLATE NOCASE ASC",
        }
        order_by = sort_map.get(sort_by, "tasting_date DESC, id DESC")

        query = f"SELECT * FROM wines {where_clause} ORDER BY {order_by}"

        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [Wine.from_row(dict(r)) for r in rows]

    def get_stats(self) -> Dict[str, Any]:
        with self._get_connection() as conn:
            total = conn.execute("SELECT COUNT(*) FROM wines").fetchone()[0]
            if total == 0:
                return {
                    "total": 0,
                    "avg_rating": 0.0,
                    "highest_rating": None,
                    "styles": {},
                    "top_countries": [],
                    "top_grapes": [],
                }

            avg_rating = conn.execute("SELECT ROUND(AVG(rating), 1) FROM wines").fetchone()[0]
            highest_row = conn.execute(
                "SELECT wine_name, winery, rating, vintage FROM wines ORDER BY rating DESC, id DESC LIMIT 1"
            ).fetchone()
            highest = dict(highest_row) if highest_row else None

            styles = {s: 0 for s in COLOR_STYLES}
            for row in conn.execute("SELECT color_style, COUNT(*) as cnt FROM wines GROUP BY color_style"):
                styles[row["color_style"]] = row["cnt"]

            top_countries = [
                (r["country"], r["cnt"])
                for r in conn.execute(
                    "SELECT country, COUNT(*) as cnt FROM wines GROUP BY country ORDER BY cnt DESC LIMIT 5"
                )
            ]

            top_grapes = [
                (r["grape_variety"], r["cnt"])
                for r in conn.execute(
                    "SELECT grape_variety, COUNT(*) as cnt FROM wines WHERE grape_variety != '' "
                    "GROUP BY grape_variety ORDER BY cnt DESC LIMIT 5"
                )
            ]

            return {
                "total": total,
                "avg_rating": avg_rating or 0.0,
                "highest": highest,
                "styles": styles,
                "top_countries": top_countries,
                "top_grapes": top_grapes,
            }

    def seed_samples(self) -> int:
        count = 0
        for sample in SAMPLE_WINES:
            # Check if this wine already exists to prevent duplicate spam
            existing = self.list_wines(search=sample.wine_name)
            if not any(w.wine_name == sample.wine_name and w.winery == sample.winery for w in existing):
                self.insert(sample)
                count += 1
        return count

    def export_json(self, target_file: Path | str) -> int:
        wines = self.list_wines()
        data = [w.to_dict() for w in wines]
        path = Path(target_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return len(data)

    def import_json(self, source_file: Path | str) -> int:
        path = Path(source_file)
        if not path.exists():
            raise FileNotFoundError(f"File {source_file} does not exist.")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError("Invalid format: expected JSON array of wine objects.")

        imported = 0
        for item in data:
            if isinstance(item, dict):
                wine = Wine.from_row(item)
                wine.id = None  # Insert as new record
                self.insert(wine)
                imported += 1
        return imported

    def export_csv(self, target_file: Path | str) -> int:
        wines = self.list_wines()
        path = Path(target_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        fields = [
            "wine_name", "winery", "country", "region", "sub_region", "vintage",
            "color_style", "grape_variety", "abv", "price", "tasting_date",
            "rating", "tasting_notes", "serving_temperature", "aging_potential",
            "food_pairing", "purchase_location", "bottle_size", "closure_type",
            "organic", "biodynamic"
        ]
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for w in wines:
                d = w.to_dict()
                row = {k: d.get(k) for k in fields}
                writer.writerow(row)
        return len(wines)
