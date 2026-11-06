"""
Statistics dialog summarizing wine collection, cellar, and tasting metrics.
"""

from __future__ import annotations
from typing import Dict, Any
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib

class StatsDialog(Adw.Dialog):
    def __init__(self, stats: Dict[str, Any]):
        super().__init__()
        self.set_title("Wine Collection Statistics")
        self.set_content_width(520)
        self.set_content_height(580)

        toolbar_view = Adw.ToolbarView.new()
        header = Adw.HeaderBar.new()

        close_btn = Gtk.Button(label="Close")
        close_btn.connect("clicked", lambda b: self.close())
        header.pack_end(close_btn)

        toolbar_view.add_top_bar(header)

        page = Adw.PreferencesPage.new()

        # Cellar Group
        cellar_grp = Adw.PreferencesGroup.new()
        cellar_grp.set_title("Cellar Inventory")

        cellar_count_row = Adw.ActionRow.new()
        cellar_count_row.set_title("Wines in Cellar")
        cellar_count_row.set_subtitle(f"{stats.get('cellar_count', 0)} different wines")
        cellar_grp.add(cellar_count_row)

        bottles_row = Adw.ActionRow.new()
        bottles_row.set_title("Total Bottles")
        bottles_row.set_subtitle(f"{stats.get('cellar_bottles', 0)} bottles stored")
        cellar_grp.add(bottles_row)

        page.add(cellar_grp)

        # Overview Group
        overview_grp = Adw.PreferencesGroup.new()
        overview_grp.set_title("Tasting Overview")

        total_row = Adw.ActionRow.new()
        total_row.set_title("Wines Tasted")
        total_row.set_subtitle(f"{stats['total']} tasting notes recorded")
        overview_grp.add(total_row)

        avg_row = Adw.ActionRow.new()
        avg_row.set_title("Average Tasting Rating")
        avg_row.set_subtitle(f"{stats['avg_rating']} / 100")
        overview_grp.add(avg_row)

        if stats.get("highest"):
            hi = stats["highest"]
            hi_row = Adw.ActionRow.new()
            hi_row.set_title("Highest Rated Wine")
            vintage_str = f" ({hi['vintage']})" if hi.get("vintage") else ""
            desc = f"{hi['wine_name']}{vintage_str} · {hi['winery']} ({hi['rating']} pts)"
            hi_row.set_subtitle(GLib.markup_escape_text(desc))
            overview_grp.add(hi_row)

        page.add(overview_grp)

        # Style Breakdown Group
        styles_grp = Adw.PreferencesGroup.new()
        styles_grp.set_title("Styles Breakdown (Tasted)")

        for style, count in stats.get("styles", {}).items():
            s_row = Adw.ActionRow.new()
            s_row.set_title(GLib.markup_escape_text(style))
            pct = (count / stats["total"] * 100) if stats["total"] > 0 else 0
            s_row.set_subtitle(f"{count} wines ({pct:.0f}%)")
            styles_grp.add(s_row)

        page.add(styles_grp)

        # Top Countries Group
        if stats.get("top_countries"):
            country_grp = Adw.PreferencesGroup.new()
            country_grp.set_title("Top Countries of Origin")
            for country, count in stats["top_countries"]:
                c_row = Adw.ActionRow.new()
                c_row.set_title(GLib.markup_escape_text(country))
                c_row.set_subtitle(f"{count} tasting{'s' if count != 1 else ''}")
                country_grp.add(c_row)
            page.add(country_grp)

        toolbar_view.set_content(page)
        self.set_child(toolbar_view)
