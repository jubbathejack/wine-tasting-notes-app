"""
Custom ListBoxRow widget representing a wine in the list.
"""

from __future__ import annotations
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Pango
from winenotes.models import Wine

class WineRow(Gtk.ListBoxRow):
    def __init__(self, wine: Wine):
        super().__init__()
        self.wine = wine
        self.add_css_class("wine-row-card")

        # Main horizontal container
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        hbox.set_margin_top(8)
        hbox.set_margin_bottom(8)
        hbox.set_margin_start(8)
        hbox.set_margin_end(8)

        # Left column: Name, Winery & Vintage, Country
        vbox_left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        vbox_left.set_hexpand(True)

        title_label = Gtk.Label(label=wine.wine_name, xalign=0.0)
        title_label.add_css_class("wine-title")
        title_label.set_ellipsize(Pango.EllipsizeMode.END)
        vbox_left.append(title_label)

        sub_text = f"{wine.winery} · {wine.vintage_display}"
        sub_label = Gtk.Label(label=sub_text, xalign=0.0)
        sub_label.add_css_class("wine-subtitle")
        sub_label.set_ellipsize(Pango.EllipsizeMode.END)
        vbox_left.append(sub_label)

        origin_text = wine.location_summary
        origin_label = Gtk.Label(label=origin_text, xalign=0.0)
        origin_label.add_css_class("caption")
        origin_label.add_css_class("dim-label")
        origin_label.set_ellipsize(Pango.EllipsizeMode.END)
        vbox_left.append(origin_label)

        if wine.aroma_notes:
            aroma_preview = " • ".join(wine.aroma_notes[:3])
            if len(wine.aroma_notes) > 3:
                aroma_preview += f" (+{len(wine.aroma_notes) - 3})"
            aroma_label = Gtk.Label(label=f"Aromas: {aroma_preview}", xalign=0.0)
            aroma_label.add_css_class("caption")
            aroma_label.add_css_class("dim-label")
            aroma_label.set_ellipsize(Pango.EllipsizeMode.END)
            vbox_left.append(aroma_label)

        hbox.append(vbox_left)

        # Right column: Style badge & Rating
        vbox_right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox_right.set_valign(Gtk.Align.CENTER)
        vbox_right.set_halign(Gtk.Align.END)

        # Style badge
        style_badge = Gtk.Label(label=wine.color_style)
        style_badge.add_css_class("style-badge")
        style_badge.add_css_class(wine.style_badge_class)
        vbox_right.append(style_badge)

        # Rating badge
        rating_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=3)
        rating_box.set_halign(Gtk.Align.END)

        rating_label = Gtk.Label(label=f"{wine.rating}")
        rating_label.add_css_class("rating-pill")
        if wine.rating >= 95:
            rating_label.add_css_class("rating-pill-high")
        elif wine.rating >= 90:
            rating_label.add_css_class("rating-pill-mid")
        else:
            rating_label.add_css_class("rating-pill-low")
        rating_box.append(rating_label)

        vbox_right.append(rating_box)
        hbox.append(vbox_right)

        self.set_child(hbox)
