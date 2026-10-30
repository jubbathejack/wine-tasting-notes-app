"""
Changelog dialog for viewing application release history.
"""

from __future__ import annotations
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Pango, GLib

from winenotes import __version__

RELEASES = [
    {
        "version": "1.1.0",
        "date": "2026-10-30",
        "title": "Interactive Wine Aroma & Flavor Wheel",
        "sections": [
            (
                "Added",
                [
                    "Interactive Cairo-rendered Wine Tasting Aroma & Flavor Wheel with 3 hierarchical tiers and 112 descriptors.",
                    "Live wheel hover inspection with dynamic center-hub path display.",
                    "Structured flavor keywords (aroma_notes) stored and displayed as category-colored badges.",
                    "Aroma Wheel exploration dialog with instant keyword search and category accordion browser.",
                    "Helper tool to automatically compose natural language sentences into notes from keywords.",
                    "Top aroma keywords preview in wine collection list rows.",
                    "Global search support for aroma keywords across the collection.",
                    "JSON and CSV export/import support for aroma keywords.",
                    "Standalone Wine Aroma Wheel Reference accessible from the main menu.",
                ],
            ),
            (
                "Changed",
                [
                    "Automatic SQLite schema migration for aroma_notes column.",
                    "Updated sample wines with rich tasting wheel keywords.",
                    "Enhanced About Dialog with native release notes support.",
                ],
            ),
        ],
    },
    {
        "version": "1.0.0",
        "date": "2026-10-29",
        "title": "Initial GNOME Desktop Release",
        "sections": [
            (
                "Added",
                [
                    "Adaptive desktop and mobile split-view layout with Adw.NavigationSplitView.",
                    "Complete wine tasting notes and cellar tracking specifications.",
                    "Zero-dependency SQLite WAL database with search and filtering.",
                    "Collection analytics and statistics dialog.",
                    "Full JSON and CSV backup import/export.",
                    "Sample wine library seeding.",
                ],
            ),
        ],
    },
]


class ChangelogDialog(Adw.Dialog):
    """
    Dialog displaying the application changelog and release history.
    """

    def __init__(self):
        super().__init__()
        self.set_title("What's New in Wine Notes")
        self.set_content_width(640)
        self.set_content_height(600)

        toolbar_view = Adw.ToolbarView.new()
        header = Adw.HeaderBar.new()

        close_btn = Gtk.Button(label="Close")
        close_btn.connect("clicked", lambda b: self.close())
        header.pack_end(close_btn)
        toolbar_view.add_top_bar(header)

        scrolled = Gtk.ScrolledWindow.new()
        scrolled.set_vexpand(True)

        clamp = Adw.Clamp.new()
        clamp.set_maximum_size(600)

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        main_box.set_margin_top(16)
        main_box.set_margin_bottom(24)
        main_box.set_margin_start(16)
        main_box.set_margin_end(16)

        for rel in RELEASES:
            card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            card.add_css_class("card")

            inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
            inner.set_margin_top(16)
            inner.set_margin_bottom(16)
            inner.set_margin_start(16)
            inner.set_margin_end(16)

            # Header row: Version pill + Date
            ver_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            ver_badge = Gtk.Label(label=f"v{rel['version']}")
            ver_badge.add_css_class("pill")
            ver_badge.add_css_class("heading")
            ver_row.append(ver_badge)

            date_lbl = Gtk.Label(label=rel["date"])
            date_lbl.add_css_class("dim-label")
            date_lbl.add_css_class("caption")
            ver_row.append(date_lbl)
            inner.append(ver_row)

            # Release title
            title_lbl = Gtk.Label(label=rel["title"], xalign=0.0)
            title_lbl.add_css_class("title-3")
            inner.append(title_lbl)

            # Sections (Added, Changed, etc.)
            for sec_name, items in rel["sections"]:
                sec_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

                sec_badge = Gtk.Label(label=sec_name.upper(), xalign=0.0)
                sec_badge.add_css_class("caption")
                sec_badge.add_css_class("dim-label")
                sec_box.append(sec_badge)

                for item in items:
                    item_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
                    bullet = Gtk.Label(label="•", xalign=0.0)
                    bullet.add_css_class("dim-label")
                    item_row.append(bullet)

                    text_lbl = Gtk.Label(label=item, xalign=0.0)
                    text_lbl.set_wrap(True)
                    text_lbl.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
                    text_lbl.set_hexpand(True)
                    item_row.append(text_lbl)

                    sec_box.append(item_row)

                inner.append(sec_box)

            card.append(inner)
            main_box.append(card)

        clamp.set_child(main_box)
        scrolled.set_child(clamp)
        toolbar_view.set_content(scrolled)
        self.set_child(toolbar_view)
