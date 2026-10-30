"""
Comprehensive test suite for Wine Tasting Notes app.
"""

import tempfile
import unittest
from pathlib import Path
from winenotes.models import Wine, COLOR_STYLES
from winenotes.db import Database
from winenotes.sample_data import SAMPLE_WINES

class TestWineModels(unittest.TestCase):
    def test_wine_creation_and_defaults(self):
        wine = Wine(
            wine_name="Château Margaux",
            winery="Château Margaux",
            country="France",
            tasting_notes="Silky, floral, ethereal.",
            rating=99,
            vintage=2010,
        )
        self.assertEqual(wine.wine_name, "Château Margaux")
        self.assertEqual(wine.vintage_display, "2010")
        self.assertEqual(wine.rating_stars, "★★★★★")
        self.assertEqual(wine.rating_level, "Classic / Extraordinary")
        self.assertEqual(wine.style_badge_class, "style-badge-red")
        self.assertEqual(wine.validate(), [])

    def test_wine_validation_failures(self):
        wine = Wine(
            wine_name="",
            winery="",
            country="",
            tasting_notes="",
            rating=120,
            vintage=1700,
        )
        errors = wine.validate()
        self.assertTrue(any("Wine name is required" in e for e in errors))
        self.assertTrue(any("Winery" in e for e in errors))
        self.assertTrue(any("Country" in e for e in errors))
        self.assertTrue(any("Rating must be between 0 and 100" in e for e in errors))
        self.assertTrue(any("Vintage must be between" in e for e in errors))

    def test_from_row_and_to_dict(self):
        sample = SAMPLE_WINES[0]
        data = sample.to_dict()
        reconstructed = Wine.from_row(data)
        self.assertEqual(reconstructed.wine_name, sample.wine_name)
        self.assertEqual(reconstructed.winery, sample.winery)
        self.assertEqual(reconstructed.rating, sample.rating)
        self.assertEqual(reconstructed.organic, sample.organic)
        self.assertEqual(reconstructed.biodynamic, sample.biodynamic)

class TestDatabaseOperations(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmpdir.name) / "test_wines.db"
        self.db = Database(self.db_path)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_empty_database_and_stats(self):
        self.assertEqual(self.db.count(), 0)
        stats = self.db.get_stats()
        self.assertEqual(stats["total"], 0)
        self.assertEqual(stats["avg_rating"], 0.0)

    def test_seed_samples(self):
        count = self.db.seed_samples()
        self.assertEqual(count, len(SAMPLE_WINES))
        self.assertEqual(self.db.count(), len(SAMPLE_WINES))

        # Idempotence: seeding again should not duplicate
        reseed_count = self.db.seed_samples()
        self.assertEqual(reseed_count, 0)
        self.assertEqual(self.db.count(), len(SAMPLE_WINES))

    def test_insert_update_delete(self):
        wine = Wine(
            wine_name="Test Shiraz",
            winery="Barossa Valley Estate",
            country="Australia",
            tasting_notes="Blackberry, eucalyptus, dark chocolate.",
            rating=91,
            color_style="Red",
            vintage=2020,
        )
        wine_id = self.db.insert(wine)
        self.assertIsNotNone(wine_id)

        # Retrieve
        fetched = self.db.get_by_id(wine_id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.wine_name, "Test Shiraz")
        self.assertEqual(fetched.rating, 91)

        # Update
        fetched.rating = 95
        fetched.wine_name = "Test Shiraz Reserve"
        self.assertTrue(self.db.update(fetched))

        updated = self.db.get_by_id(wine_id)
        self.assertEqual(updated.wine_name, "Test Shiraz Reserve")
        self.assertEqual(updated.rating, 95)

        # Delete
        self.assertTrue(self.db.delete(wine_id))
        self.assertIsNone(self.db.get_by_id(wine_id))

    def test_search_and_filters(self):
        self.db.seed_samples()

        # Search by grape
        results = self.db.list_wines(search="Pinot Noir")
        self.assertTrue(len(results) >= 1)
        self.assertTrue(any("Pinot Noir" in w.grape_variety for w in results))

        # Search by region
        results = self.db.list_wines(search="Bordeaux")
        self.assertTrue(len(results) >= 1)

        # Filter by style
        reds = self.db.list_wines(style_filter="Red")
        self.assertTrue(all(w.color_style == "Red" for w in reds))

        whites = self.db.list_wines(style_filter="White")
        self.assertTrue(all(w.color_style == "White" for w in whites))

    def test_export_import_json(self):
        self.db.seed_samples()
        json_file = Path(self.tmpdir.name) / "export.json"

        # Export
        count = self.db.export_json(json_file)
        self.assertEqual(count, len(SAMPLE_WINES))
        self.assertTrue(json_file.exists())

        # Create new fresh DB and import
        db2_file = Path(self.tmpdir.name) / "imported.db"
        db2 = Database(db2_file)
        self.assertEqual(db2.count(), 0)

        imported_count = db2.import_json(json_file)
        self.assertEqual(imported_count, count)
        self.assertEqual(db2.count(), count)

    def test_export_csv(self):
        self.db.seed_samples()
        csv_file = Path(self.tmpdir.name) / "export.csv"
        count = self.db.export_csv(csv_file)
        self.assertEqual(count, len(SAMPLE_WINES))
        self.assertTrue(csv_file.exists())

    def test_aroma_notes_db_and_search(self):
        wine = Wine(
            wine_name="Aroma Test Syrah",
            winery="Rhône Cellars",
            country="France",
            tasting_notes="Spicy and floral.",
            aroma_notes=["Black Pepper", "Violet", "Blackberry"],
        )
        wine_id = self.db.insert(wine)
        fetched = self.db.get_by_id(wine_id)
        self.assertEqual(fetched.aroma_notes, ["Black Pepper", "Violet", "Blackberry"])

        # Search by aroma keyword
        matches = self.db.list_wines(search="Black Pepper")
        self.assertTrue(any(w.id == wine_id for w in matches))

        # Update aromas
        fetched.aroma_notes = ["Black Pepper", "Vanilla"]
        self.db.update(fetched)
        updated = self.db.get_by_id(wine_id)
        self.assertEqual(updated.aroma_notes, ["Black Pepper", "Vanilla"])


class TestAromaWheelData(unittest.TestCase):
    def test_aroma_wheel_taxonomy(self):
        from winenotes.aroma_wheel_data import (
            SUBCATEGORIES,
            DESCRIPTOR_MAP,
            get_descriptor_info,
            get_descriptor_css_class,
            format_keywords_sentence,
        )
        self.assertTrue(len(SUBCATEGORIES) >= 19)
        self.assertTrue(len(DESCRIPTOR_MAP) >= 100)
        self.assertIn("Sour Cherry", DESCRIPTOR_MAP)
        self.assertIn("Vanilla", DESCRIPTOR_MAP)
        self.assertIn("Lime", DESCRIPTOR_MAP)

        info = get_descriptor_info("Sour Cherry")
        self.assertIsNotNone(info)
        self.assertEqual(info.tier2, "Red Fruit")
        self.assertEqual(get_descriptor_css_class("Sour Cherry"), "aroma-cat-red-fruit")

        # Sentence formatting
        sentence = format_keywords_sentence(["Blackberry", "Violet", "Vanilla"])
        self.assertIn("blackberry", sentence)
        self.assertIn("violet", sentence)
        self.assertIn("vanilla", sentence)


class TestAromaWheelWidgets(unittest.TestCase):
    def test_widget_and_dialog_init(self):
        import gi
        gi.require_version("Gtk", "4.0")
        gi.require_version("Adw", "1")
        from gi.repository import Adw
        Adw.init()

        from winenotes.tasting_wheel_widget import TastingWheelWidget
        from winenotes.aroma_dialog import AromaWheelDialog

        widget = TastingWheelWidget(selected_descriptors={"Lime", "Vanilla"})
        self.assertEqual(widget.selected_descriptors, {"Lime", "Vanilla"})
        widget.toggle_descriptor("Lime")
        self.assertNotIn("Lime", widget.selected_descriptors)

        dialog = AromaWheelDialog(initial_keywords=["Cherry", "Oak Aging"])
        self.assertIn("Cherry", dialog.selected_keywords)

    def test_changelog_dialog_and_file(self):
        from pathlib import Path
        from winenotes.changelog_dialog import ChangelogDialog, RELEASES

        changelog_file = Path(__file__).parent.parent / "CHANGELOG.md"
        self.assertTrue(changelog_file.exists())
        content = changelog_file.read_text(encoding="utf-8")
        self.assertIn("1.1.0", content)
        self.assertIn("1.0.0", content)

        self.assertTrue(len(RELEASES) >= 2)
        dlg = ChangelogDialog()
        self.assertIsNotNone(dlg)


if __name__ == "__main__":
    unittest.main()


