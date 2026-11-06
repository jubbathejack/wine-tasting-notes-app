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
from contextlib import contextmanager
from typing import Optional, List, Dict, Any
from winenotes.models import Wine, COLOR_STYLES
from winenotes.sample_data import SAMPLE_WINES

SCHEMA = """
CREATE TABLE IF NOT EXISTS wines (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    wine_name           TEXT NOT NULL,
    winery              TEXT NOT NULL,
    country             TEXT NOT NULL,
    region              TEXT,
    sub_region          TEXT,
    vintage             INTEGER,
    color_style         TEXT NOT NULL CHECK(color_style IN ('Red', 'White', 'Rosé', 'Sparkling', 'Dessert', 'Fortified')),
    grape_variety       TEXT NOT NULL DEFAULT '',
    abv                 REAL,
    bottle_size         REAL DEFAULT 0.75,
    closure_type        TEXT CHECK(closure_type IN ('Cork', 'Screwcap', 'Glass', 'Synthetic', NULL)),
    organic             INTEGER NOT NULL DEFAULT 0,
    biodynamic          INTEGER NOT NULL DEFAULT 0,
    price               REAL,
    purchase_location   TEXT,
    purchase_date       TEXT,
    in_cellar           INTEGER NOT NULL DEFAULT 0,
    bottles             INTEGER NOT NULL DEFAULT 1,
    storage_location    TEXT,
    drink_from          INTEGER,
    drink_until         INTEGER,
    tasting_date        TEXT,
    rating              INTEGER CHECK(rating IS NULL OR (rating >= 0 AND rating <= 100)),
    tasting_notes       TEXT,
    serving_temperature INTEGER,
    food_pairing        TEXT,
    aging_potential     TEXT,
    aroma_notes         TEXT NOT NULL DEFAULT '[]',
    is_sample           INTEGER NOT NULL DEFAULT 0,
    created_at          TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at          TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_wines_name ON wines(wine_name);
CREATE INDEX IF NOT EXISTS idx_wines_winery ON wines(winery);
CREATE INDEX IF NOT EXISTS idx_wines_color ON wines(color_style);
CREATE INDEX IF NOT EXISTS idx_wines_rating ON wines(rating);
CREATE INDEX IF NOT EXISTS idx_wines_date ON wines(tasting_date);
CREATE INDEX IF NOT EXISTS idx_wines_cellar ON wines(in_cellar);

CREATE TABLE IF NOT EXISTS cellar_locations (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
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

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA foreign_keys = ON;")
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def init_db(self) -> None:
        with self._get_connection() as conn:
            row = conn.execute("PRAGMA user_version").fetchone()
            version = row[0] if row else 0
            if version < 2:
                conn.executescript("""
                    DROP TABLE IF EXISTS wines;
                    DROP TABLE IF EXISTS cellar_locations;
                """)
                conn.executescript(SCHEMA)
                conn.execute("PRAGMA user_version = 2;")
            else:
                conn.executescript(SCHEMA)

    def count(self) -> int:
        with self._get_connection() as conn:
            row = conn.execute("SELECT COUNT(*) FROM wines").fetchone()
            return row[0] if row else 0

    def insert(self, wine: Wine, is_sample: bool = False, in_cellar: Optional[bool] = None) -> int:
        target_cellar = wine.in_cellar if in_cellar is None else in_cellar
        wine.in_cellar = target_cellar

        query = """
        INSERT INTO wines (
            wine_name, winery, country, region, sub_region, vintage,
            color_style, grape_variety, abv, bottle_size, closure_type,
            organic, biodynamic, price, purchase_location, purchase_date,
            in_cellar, bottles, storage_location, drink_from, drink_until,
            tasting_date, rating, tasting_notes, serving_temperature,
            food_pairing, aging_potential, aroma_notes, is_sample
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            wine.bottle_size if wine.bottle_size else 0.75,
            wine.closure_type,
            1 if wine.organic else 0,
            1 if wine.biodynamic else 0,
            wine.price,
            wine.purchase_location.strip() if wine.purchase_location else None,
            wine.purchase_date.strip() if wine.purchase_date else None,
            1 if target_cellar else 0,
            wine.bottles if wine.bottles is not None else 1,
            wine.storage_location.strip() if wine.storage_location else None,
            wine.drink_from,
            wine.drink_until,
            wine.tasting_date.strip() if wine.tasting_date else None,
            wine.rating,
            wine.tasting_notes.strip() if wine.tasting_notes else None,
            wine.serving_temperature,
            wine.food_pairing.strip() if wine.food_pairing else None,
            wine.aging_potential.strip() if wine.aging_potential else None,
            json.dumps(wine.aroma_notes or []),
            1 if is_sample else 0,
        )
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(query, params)
            wine_id = cur.lastrowid
            wine.id = wine_id

        if target_cellar and wine.storage_location:
            self._upsert_cellar_location(wine.storage_location)

        return wine_id

    def update(self, wine: Wine) -> bool:
        if wine.id is None:
            raise ValueError("Wine must have an ID to update.")
        query = """
        UPDATE wines SET
            wine_name = ?, winery = ?, country = ?, region = ?, sub_region = ?,
            vintage = ?, color_style = ?, grape_variety = ?, abv = ?,
            bottle_size = ?, closure_type = ?, organic = ?, biodynamic = ?,
            price = ?, purchase_location = ?, purchase_date = ?,
            in_cellar = ?, bottles = ?, storage_location = ?,
            drink_from = ?, drink_until = ?, tasting_date = ?,
            rating = ?, tasting_notes = ?, serving_temperature = ?,
            food_pairing = ?, aging_potential = ?, aroma_notes = ?,
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
            wine.bottle_size if wine.bottle_size else 0.75,
            wine.closure_type,
            1 if wine.organic else 0,
            1 if wine.biodynamic else 0,
            wine.price,
            wine.purchase_location.strip() if wine.purchase_location else None,
            wine.purchase_date.strip() if wine.purchase_date else None,
            1 if wine.in_cellar else 0,
            wine.bottles if wine.bottles is not None else 1,
            wine.storage_location.strip() if wine.storage_location else None,
            wine.drink_from,
            wine.drink_until,
            wine.tasting_date.strip() if wine.tasting_date else None,
            wine.rating,
            wine.tasting_notes.strip() if wine.tasting_notes else None,
            wine.serving_temperature,
            wine.food_pairing.strip() if wine.food_pairing else None,
            wine.aging_potential.strip() if wine.aging_potential else None,
            json.dumps(wine.aroma_notes or []),
            wine.id,
        )
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(query, params)
            updated = cur.rowcount > 0

        if updated and wine.in_cellar and wine.storage_location:
            self._upsert_cellar_location(wine.storage_location)

        return updated

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

    def list_tasted(
        self,
        search: str = "",
        style_filter: Optional[str] = None,
        sort_by: str = "date_desc",
    ) -> List[Wine]:
        return self._query_wines(in_cellar=0, search=search, style_filter=style_filter, sort_by=sort_by)

    def list_cellar(
        self,
        search: str = "",
        style_filter: Optional[str] = None,
        sort_by: str = "name_asc",
    ) -> List[Wine]:
        return self._query_wines(in_cellar=1, search=search, style_filter=style_filter, sort_by=sort_by)

    def list_wines(
        self,
        search: str = "",
        style_filter: Optional[str] = None,
        sort_by: str = "date_desc",
    ) -> List[Wine]:
        """Legacy alias: returns tasted wines (in_cellar=0)."""
        return self.list_tasted(search=search, style_filter=style_filter, sort_by=sort_by)

    def list_all(
        self,
        search: str = "",
        style_filter: Optional[str] = None,
        sort_by: str = "name_asc",
    ) -> List[Wine]:
        return self._query_wines(in_cellar=None, search=search, style_filter=style_filter, sort_by=sort_by)

    def _query_wines(
        self,
        in_cellar: Optional[int],
        search: str = "",
        style_filter: Optional[str] = None,
        sort_by: str = "date_desc",
    ) -> List[Wine]:
        clauses = []
        params: List[Any] = []

        if in_cellar is not None:
            clauses.append("in_cellar = ?")
            params.append(in_cellar)

        if search and search.strip():
            term = f"%{search.strip()}%"
            clauses.append(
                "("
                "wine_name LIKE ? OR winery LIKE ? OR grape_variety LIKE ? "
                "OR region LIKE ? OR country LIKE ? OR tasting_notes LIKE ? "
                "OR aroma_notes LIKE ? OR storage_location LIKE ? OR CAST(vintage AS TEXT) LIKE ?"
                ")"
            )
            params.extend([term, term, term, term, term, term, term, term, term])

        if style_filter and style_filter != "All" and style_filter != "All Styles":
            clauses.append("color_style = ?")
            params.append(style_filter)

        where_clause = f"WHERE {' AND '.join(clauses)}" if clauses else ""

        sort_map = {
            "date_desc": "tasting_date DESC NULLS LAST, id DESC",
            "date_asc": "tasting_date ASC NULLS LAST, id ASC",
            "rating_desc": "rating DESC NULLS LAST, tasting_date DESC NULLS LAST",
            "rating_asc": "rating ASC NULLS LAST, tasting_date DESC NULLS LAST",
            "vintage_desc": "vintage DESC NULLS LAST, id DESC",
            "name_asc": "wine_name COLLATE NOCASE ASC",
            "drink_from_asc": "drink_from ASC NULLS LAST, wine_name COLLATE NOCASE ASC",
            "date_added_desc": "created_at DESC, id DESC",
        }
        order_by = sort_map.get(sort_by, "id DESC")

        query = f"SELECT * FROM wines {where_clause} ORDER BY {order_by}"

        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [Wine.from_row(dict(r)) for r in rows]

    def decrement_or_delete_cellar(self, wine_id: int) -> int:
        with self._get_connection() as conn:
            row = conn.execute("SELECT bottles FROM wines WHERE id = ? AND in_cellar = 1", (wine_id,)).fetchone()
            if not row:
                return 0
            bottles = row[0]
            if bottles <= 1:
                conn.execute("DELETE FROM wines WHERE id = ?", (wine_id,))
                return 0
            else:
                conn.execute(
                    "UPDATE wines SET bottles = bottles - 1, updated_at = datetime('now') WHERE id = ?",
                    (wine_id,),
                )
                return bottles - 1

    def get_cellar_locations(self) -> List[str]:
        with self._get_connection() as conn:
            rows = conn.execute("SELECT name FROM cellar_locations ORDER BY name COLLATE NOCASE").fetchall()
            return [r[0] for r in rows]

    def _upsert_cellar_location(self, name: str) -> None:
        if not name or not name.strip():
            return
        with self._get_connection() as conn:
            conn.execute("INSERT OR IGNORE INTO cellar_locations (name) VALUES (?)", (name.strip(),))

    def get_stats(self) -> Dict[str, Any]:
        with self._get_connection() as conn:
            tasted_total = conn.execute("SELECT COUNT(*) FROM wines WHERE in_cellar = 0").fetchone()[0]
            cellar_count = conn.execute("SELECT COUNT(*) FROM wines WHERE in_cellar = 1").fetchone()[0]
            cellar_bottles_row = conn.execute("SELECT SUM(bottles) FROM wines WHERE in_cellar = 1").fetchone()
            cellar_bottles = cellar_bottles_row[0] if (cellar_bottles_row and cellar_bottles_row[0] is not None) else 0

            if tasted_total == 0:
                return {
                    "total": 0,
                    "avg_rating": 0.0,
                    "highest": None,
                    "styles": {s: 0 for s in COLOR_STYLES},
                    "top_countries": [],
                    "top_grapes": [],
                    "cellar_count": cellar_count,
                    "cellar_bottles": cellar_bottles,
                }

            avg_rating = conn.execute(
                "SELECT ROUND(AVG(rating), 1) FROM wines WHERE in_cellar = 0 AND rating IS NOT NULL"
            ).fetchone()[0]

            highest_row = conn.execute(
                "SELECT wine_name, winery, rating, vintage FROM wines "
                "WHERE in_cellar = 0 AND rating IS NOT NULL ORDER BY rating DESC, id DESC LIMIT 1"
            ).fetchone()
            highest = dict(highest_row) if highest_row else None

            styles = {s: 0 for s in COLOR_STYLES}
            for row in conn.execute(
                "SELECT color_style, COUNT(*) as cnt FROM wines WHERE in_cellar = 0 GROUP BY color_style"
            ):
                styles[row["color_style"]] = row["cnt"]

            top_countries = [
                (r["country"], r["cnt"])
                for r in conn.execute(
                    "SELECT country, COUNT(*) as cnt FROM wines WHERE in_cellar = 0 GROUP BY country ORDER BY cnt DESC LIMIT 5"
                )
            ]

            top_grapes = [
                (r["grape_variety"], r["cnt"])
                for r in conn.execute(
                    "SELECT grape_variety, COUNT(*) as cnt FROM wines WHERE in_cellar = 0 AND grape_variety != '' "
                    "GROUP BY grape_variety ORDER BY cnt DESC LIMIT 5"
                )
            ]

            return {
                "total": tasted_total,
                "avg_rating": avg_rating or 0.0,
                "highest": highest,
                "styles": styles,
                "top_countries": top_countries,
                "top_grapes": top_grapes,
                "cellar_count": cellar_count,
                "cellar_bottles": cellar_bottles,
            }

    def sample_count(self) -> int:
        with self._get_connection() as conn:
            row = conn.execute("SELECT COUNT(*) FROM wines WHERE is_sample = 1").fetchone()
            return row[0] if row else 0

    def is_sample(self, wine_id: int) -> bool:
        with self._get_connection() as conn:
            row = conn.execute("SELECT is_sample FROM wines WHERE id = ?", (wine_id,)).fetchone()
            return bool(row and row[0])

    def list_samples(self) -> List[Wine]:
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM wines WHERE is_sample = 1 ORDER BY id").fetchall()
            return [Wine.from_row(dict(row)) for row in rows]

    def remove_samples(self) -> List[Wine]:
        samples = self.list_samples()
        if samples:
            with self._get_connection() as conn:
                conn.execute("DELETE FROM wines WHERE is_sample = 1")
        return samples

    def seed_samples(self) -> int:
        count = 0
        for sample in SAMPLE_WINES:
            existing = self.list_tasted(search=sample.wine_name)
            if not any(w.wine_name == sample.wine_name and w.winery == sample.winery for w in existing):
                self.insert(sample, is_sample=True, in_cellar=False)
                count += 1
        return count

    def export_json(self, target_file: Path | str) -> int:
        wines = self.list_all()
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
                wine.id = None
                self.insert(wine, in_cellar=wine.in_cellar)
                imported += 1
        return imported

    def export_csv(self, target_file: Path | str) -> int:
        wines = self.list_all()
        path = Path(target_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        fields = [
            "wine_name", "winery", "country", "region", "sub_region", "vintage",
            "color_style", "grape_variety", "abv", "price", "purchase_location",
            "purchase_date", "in_cellar", "bottles", "storage_location", "drink_from",
            "drink_until", "tasting_date", "rating", "tasting_notes", "aroma_notes",
            "serving_temperature", "aging_potential", "food_pairing", "bottle_size",
            "closure_type", "organic", "biodynamic"
        ]
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for w in wines:
                d = w.to_dict()
                row = {k: d.get(k) for k in fields}
                if isinstance(row.get("aroma_notes"), list):
                    row["aroma_notes"] = ", ".join(row["aroma_notes"])
                writer.writerow(row)
        return len(wines)
