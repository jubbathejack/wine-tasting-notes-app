"""
Wine Detail view showing complete tasting notes and wine specifications.
"""

from __future__ import annotations
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Pango, GLib
from winenotes.models import Wine
from winenotes.aroma_dialog import AromaWheelDialog
from winenotes.aroma_wheel_data import get_descriptor_css_class

class WineDetailView(Gtk.ScrolledWindow):
    def __init__(self):
        super().__init__()
        self.set_vexpand(True)
        self.set_hexpand(True)

        self.clamp = Adw.Clamp.new()
        self.clamp.set_maximum_size(860)
        self.clamp.set_tightening_threshold(600)

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        self.main_box.set_margin_top(24)
        self.main_box.set_margin_bottom(36)
        self.main_box.set_margin_start(20)
        self.main_box.set_margin_end(20)

        self.clamp.set_child(self.main_box)
        self.set_child(self.clamp)

    def display_wine(self, wine: Wine):
        # Clear existing children
        while child := self.main_box.get_first_child():
            self.main_box.remove(child)

        # 1. Header Card (Hero)
        header_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        header_card.add_css_class("card")
        header_card.set_margin_bottom(6)
        header_card.set_margin_top(4)

        header_inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        header_inner.set_margin_top(20)
        header_inner.set_margin_bottom(20)
        header_inner.set_margin_start(20)
        header_inner.set_margin_end(20)

        # Title & Badges row
        top_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)

        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        title_box.set_hexpand(True)

        name_label = Gtk.Label(label=wine.wine_name, xalign=0.0)
        name_label.add_css_class("title-1")
        name_label.set_wrap(True)
        name_label.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
        title_box.append(name_label)

        sub_label = Gtk.Label(
            label=f"{wine.winery} · {wine.vintage_display}",
            xalign=0.0,
        )
        sub_label.add_css_class("title-3")
        sub_label.add_css_class("dim-label")
        title_box.append(sub_label)

        top_row.append(title_box)

        # Big Rating Score
        score_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        score_box.set_valign(Gtk.Align.CENTER)
        score_box.set_halign(Gtk.Align.END)

        score_num = Gtk.Label(label=f"{wine.rating}")
        score_num.add_css_class("rating-pill")
        if wine.rating >= 95:
            score_num.add_css_class("rating-pill-high")
        elif wine.rating >= 90:
            score_num.add_css_class("rating-pill-mid")
        else:
            score_num.add_css_class("rating-pill-low")
        score_box.append(score_num)

        stars_label = Gtk.Label(label=wine.rating_stars)
        stars_label.add_css_class("caption")
        stars_label.add_css_class("dim-label")
        score_box.append(stars_label)

        top_row.append(score_box)
        header_inner.append(top_row)

        # Badges & Tag strip
        tag_strip = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        tag_strip.set_margin_top(4)

        style_badge = Gtk.Label(label=wine.color_style)
        style_badge.add_css_class("style-badge")
        style_badge.add_css_class(wine.style_badge_class)
        tag_strip.append(style_badge)

        level_badge = Gtk.Label(label=wine.rating_level)
        level_badge.add_css_class("caption")
        level_badge.add_css_class("dim-label")
        tag_strip.append(level_badge)

        if wine.organic:
            org_pill = Gtk.Label(label="🌱 Organic")
            org_pill.add_css_class("eco-pill")
            tag_strip.append(org_pill)

        if wine.biodynamic:
            bio_pill = Gtk.Label(label="✨ Biodynamic")
            bio_pill.add_css_class("eco-pill")
            tag_strip.append(bio_pill)

        header_inner.append(tag_strip)
        header_card.append(header_inner)
        self.main_box.append(header_card)

        # 2. Tasting Notes Callout
        notes_group = Adw.PreferencesGroup.new()
        notes_group.set_title("Tasting Notes and Impressions")
        notes_group.set_description(f"Tasted on {wine.tasting_date}")

        notes_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        notes_box.add_css_class("tasting-note-box")

        notes_label = Gtk.Label(label=wine.tasting_notes, xalign=0.0)
        notes_label.set_wrap(True)
        notes_label.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
        notes_label.set_selectable(True)
        notes_box.append(notes_label)

        notes_group.add(notes_box)
        self.main_box.append(notes_group)

        # 3. Aroma and Flavor Wheel Keywords
        aroma_group = Adw.PreferencesGroup.new()
        aroma_group.set_title("Aroma and Flavor Profile")
        count_desc = (
            f"{len(wine.aroma_notes)} flavor keywords categorized from tasting wheel"
            if wine.aroma_notes
            else "Categorize tasting flavors using the visual aroma wheel"
        )
        aroma_group.set_description(count_desc)

        aroma_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        aroma_card.add_css_class("card")
        aroma_card.set_margin_top(4)

        card_inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        card_inner.set_margin_top(14)
        card_inner.set_margin_bottom(14)
        card_inner.set_margin_start(16)
        card_inner.set_margin_end(16)

        header_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        header_title = Gtk.Label(label="Tasting Wheel Keywords", xalign=0.0)
        header_title.add_css_class("heading")
        header_title.set_hexpand(True)
        header_row.append(header_title)

        explore_wheel_btn = Gtk.Button.new_with_label("View on Tasting Wheel...")
        explore_wheel_btn.add_css_class("pill")
        explore_wheel_btn.set_valign(Gtk.Align.CENTER)
        explore_wheel_btn.connect("clicked", lambda b, w=wine: self._open_wheel_viewer(w))
        header_row.append(explore_wheel_btn)
        card_inner.append(header_row)

        if wine.aroma_notes:
            chips_flow = Gtk.FlowBox.new()
            chips_flow.set_selection_mode(Gtk.SelectionMode.NONE)
            chips_flow.set_column_spacing(8)
            chips_flow.set_row_spacing(8)

            for kw in wine.aroma_notes:
                badge = Gtk.Label(label=kw)
                badge.add_css_class("aroma-badge")
                badge.add_css_class(get_descriptor_css_class(kw))
                chips_flow.append(badge)
            card_inner.append(chips_flow)
        else:
            no_aroma_lbl = Gtk.Label(
                label="No aroma keywords tagged yet. Edit this note to select keywords from the tasting wheel.",
                xalign=0.0,
            )
            no_aroma_lbl.add_css_class("dim-label")
            no_aroma_lbl.add_css_class("caption")
            card_inner.append(no_aroma_lbl)

        aroma_card.append(card_inner)
        aroma_group.add(aroma_card)
        self.main_box.append(aroma_group)

        # 4. Wine Profile Group
        profile_group = Adw.PreferencesGroup.new()
        profile_group.set_title("Wine Profile and Terroir")

        self._add_row(profile_group, "Winery / Producer", wine.winery)
        if wine.grape_variety:
            self._add_row(profile_group, "Grape Variety", wine.grape_variety)
        if wine.vintage:
            self._add_row(profile_group, "Vintage", str(wine.vintage))
        self._add_row(profile_group, "Country", wine.country)
        if wine.region:
            self._add_row(profile_group, "Region", wine.region)
        if wine.sub_region:
            self._add_row(profile_group, "Sub-region / Appellation", wine.sub_region)

        self.main_box.append(profile_group)

        # 4. Specifications & Service Group
        specs_group = Adw.PreferencesGroup.new()
        specs_group.set_title("Specifications and Service")

        self._add_row(specs_group, "Color and Style", wine.color_style)

        if wine.abv is not None:
            self._add_row(specs_group, "Alcohol by Volume (ABV)", f"{wine.abv:.1f}%")

        if wine.serving_temperature is not None:
            self._add_row(specs_group, "Serving Temperature", f"{wine.serving_temperature} °C ({int(wine.serving_temperature * 9 / 5 + 32)} °F)")

        if wine.bottle_size is not None:
            size_str = f"{wine.bottle_size} L"
            if wine.bottle_size == 0.75:
                size_str += " (Standard 750ml)"
            elif wine.bottle_size == 1.5:
                size_str += " (Magnum)"
            self._add_row(specs_group, "Bottle Size", size_str)

        if wine.closure_type:
            self._add_row(specs_group, "Closure Type", wine.closure_type)

        farming = []
        if wine.organic:
            farming.append("Certified Organic")
        if wine.biodynamic:
            farming.append("Certified Biodynamic")
        if farming:
            self._add_row(specs_group, "Farming Practices", " · ".join(farming))

        self.main_box.append(specs_group)

        # 5. Cellar, Purchase & Food Pairing
        cellar_group = Adw.PreferencesGroup.new()
        cellar_group.set_title("Cellar, Food Pairing and Purchase")

        if wine.food_pairing:
            self._add_row(cellar_group, "Food Pairing Recommendations", wine.food_pairing)

        if wine.aging_potential:
            self._add_row(cellar_group, "Aging Potential and Drinking Window", wine.aging_potential)

        if wine.purchase_location:
            self._add_row(cellar_group, "Purchased From", wine.purchase_location)

        if wine.price is not None:
            self._add_row(cellar_group, "Price Paid", f"£{wine.price:.2f}" if wine.price > 0 else "N/A")

        self._add_row(cellar_group, "Tasted On", wine.tasting_date)

        self.main_box.append(cellar_group)

    def _add_row(self, group: Adw.PreferencesGroup, title: str, subtitle: str):
        row = Adw.ActionRow.new()
        row.set_title(GLib.markup_escape_text(title))
        row.set_subtitle(GLib.markup_escape_text(subtitle or "—"))
        row.set_subtitle_lines(0)
        group.add(row)

    def _open_wheel_viewer(self, wine: Wine):
        dlg = AromaWheelDialog(
            initial_keywords=wine.aroma_notes,
            allow_append_to_notes=False,
        )
        root = self.get_root()
        if root:
            dlg.present(root)
        else:
            dlg.present()

