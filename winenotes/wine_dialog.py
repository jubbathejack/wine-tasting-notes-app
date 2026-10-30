"""
Dialog for adding or editing a wine tasting note.
"""

from __future__ import annotations
from datetime import date, datetime
from typing import Optional, Callable
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw
from winenotes.models import Wine, COLOR_STYLES, CLOSURE_TYPES
from winenotes.aroma_dialog import AromaWheelDialog
from winenotes.aroma_wheel_data import get_descriptor_css_class, format_keywords_sentence

BOTTLE_SIZES = [
    ("0.75 L (Standard)", 0.75),
    ("0.375 L (Half Bottle)", 0.375),
    ("1.5 L (Magnum)", 1.5),
    ("3.0 L (Double Magnum)", 3.0),
    ("0.5 L (Sweet / Tokaji)", 0.5),
]

class WineDialog(Adw.Dialog):
    def __init__(
        self,
        wine: Optional[Wine] = None,
        on_save: Optional[Callable[[Wine], None]] = None,
    ):
        super().__init__()
        self.wine = wine
        self.on_save = on_save
        self.is_edit = wine is not None
        self.aroma_keywords = list(wine.aroma_notes) if (self.is_edit and wine and wine.aroma_notes) else []

        title = "Edit Wine Tasting Note" if self.is_edit else "New Wine Tasting Note"
        self.set_title(title)
        self.set_content_width(620)
        self.set_content_height(720)

        # ToolbarView with HeaderBar
        self.toolbar_view = Adw.ToolbarView.new()
        header = Adw.HeaderBar.new()

        cancel_btn = Gtk.Button(label="Cancel")
        cancel_btn.connect("clicked", lambda b: self.close())
        header.pack_start(cancel_btn)

        save_btn = Gtk.Button(label="Save")
        save_btn.add_css_class("suggested-action")
        save_btn.connect("clicked", self._on_save_clicked)
        header.pack_end(save_btn)

        self.toolbar_view.add_top_bar(header)

        # Toast overlay for in-dialog notifications
        self.toast_overlay = Adw.ToastOverlay.new()

        # Preferences page with form fields
        page = Adw.PreferencesPage.new()

        # --- Group 1: Wine Profile ---
        profile_grp = Adw.PreferencesGroup.new()
        profile_grp.set_title("Wine Profile")

        self.name_row = Adw.EntryRow.new()
        self.name_row.set_title("Wine Name *")
        if self.is_edit:
            self.name_row.set_text(self.wine.wine_name)
        profile_grp.add(self.name_row)

        self.winery_row = Adw.EntryRow.new()
        self.winery_row.set_title("Winery / Producer *")
        if self.is_edit:
            self.winery_row.set_text(self.wine.winery)
        profile_grp.add(self.winery_row)

        self.grape_row = Adw.EntryRow.new()
        self.grape_row.set_title("Grape Variety (e.g. Pinot Noir, Cabernet)")
        if self.is_edit:
            self.grape_row.set_text(self.wine.grape_variety or "")
        profile_grp.add(self.grape_row)

        # Vintage spin row (1800 = NV)
        current_year = datetime.now().year
        vintage_val = self.wine.vintage if (self.is_edit and self.wine.vintage) else current_year - 1
        adj_vintage = Gtk.Adjustment.new(vintage_val, 1800, current_year + 2, 1, 5, 0)
        self.vintage_row = Adw.SpinRow.new(adj_vintage, 1, 0)
        self.vintage_row.set_title("Vintage (Set 1800 for Non-Vintage)")
        if self.is_edit and self.wine.vintage is None:
            self.vintage_row.set_value(1800)
        profile_grp.add(self.vintage_row)

        # Color and Style Combo
        self.style_row = Adw.ComboRow.new()
        self.style_row.set_title("Color and Style *")
        style_list = Gtk.StringList.new(COLOR_STYLES)
        self.style_row.set_model(style_list)
        if self.is_edit and self.wine.color_style in COLOR_STYLES:
            self.style_row.set_selected(COLOR_STYLES.index(self.wine.color_style))
        else:
            self.style_row.set_selected(0)
        profile_grp.add(self.style_row)

        page.add(profile_grp)

        # --- Group 2: Origin & Terroir ---
        origin_grp = Adw.PreferencesGroup.new()
        origin_grp.set_title("Origin and Terroir")

        self.country_row = Adw.EntryRow.new()
        self.country_row.set_title("Country * (e.g. France, Italy, Spain)")
        if self.is_edit:
            self.country_row.set_text(self.wine.country)
        origin_grp.add(self.country_row)

        self.region_row = Adw.EntryRow.new()
        self.region_row.set_title("Region (e.g. Bordeaux, Piedmont, Napa Valley)")
        if self.is_edit and self.wine.region:
            self.region_row.set_text(self.wine.region)
        origin_grp.add(self.region_row)

        self.sub_region_row = Adw.EntryRow.new()
        self.sub_region_row.set_title("Sub-region / Appellation (e.g. Pauillac, Barolo)")
        if self.is_edit and self.wine.sub_region:
            self.sub_region_row.set_text(self.wine.sub_region)
        origin_grp.add(self.sub_region_row)

        page.add(origin_grp)

        # --- Group 3: Tasting & Evaluation ---
        eval_grp = Adw.PreferencesGroup.new()
        eval_grp.set_title("Tasting and Evaluation")

        rating_val = self.wine.rating if self.is_edit else 90
        adj_rating = Gtk.Adjustment.new(rating_val, 0, 100, 1, 5, 0)
        self.rating_row = Adw.SpinRow.new(adj_rating, 1, 0)
        self.rating_row.set_title("Rating Score (0 - 100) *")
        eval_grp.add(self.rating_row)

        self.date_row = Adw.EntryRow.new()
        self.date_row.set_title("Tasting Date (YYYY-MM-DD)")
        default_date = self.wine.tasting_date if self.is_edit else date.today().isoformat()
        self.date_row.set_text(default_date)
        eval_grp.add(self.date_row)

        page.add(eval_grp)

        # Tasting notes multiline text
        notes_grp = Adw.PreferencesGroup.new()
        notes_grp.set_title("Tasting Notes and Impressions *")
        notes_grp.set_description("Describe appearance, nose/aroma, palate, tannins, acidity, and finish.")

        self.notes_buffer = Gtk.TextBuffer.new()
        if self.is_edit:
            self.notes_buffer.set_text(self.wine.tasting_notes)

        notes_tv = Gtk.TextView.new_with_buffer(self.notes_buffer)
        notes_tv.set_wrap_mode(Gtk.WrapMode.WORD)
        notes_tv.set_top_margin(10)
        notes_tv.set_bottom_margin(10)
        notes_tv.set_left_margin(12)
        notes_tv.set_right_margin(12)

        scrolled_notes = Gtk.ScrolledWindow.new()
        scrolled_notes.set_min_content_height(130)
        scrolled_notes.set_child(notes_tv)
        scrolled_notes.add_css_class("card")
        notes_grp.add(scrolled_notes)

        page.add(notes_grp)

        # --- Aroma and Flavor Wheel Profile ---
        aroma_grp = Adw.PreferencesGroup.new()
        aroma_grp.set_title("Aroma and Flavor Wheel (Keywords)")
        aroma_grp.set_description("Categorize what you tasted using the visual tasting wheel.")

        wheel_row = Adw.ActionRow.new()
        wheel_row.set_title("Tasting Wheel Descriptors")
        wheel_row.set_subtitle("Pick structured flavor keywords to accompany your notes.")

        open_wheel_btn = Gtk.Button.new_with_label("Open Tasting Wheel...")
        open_wheel_btn.add_css_class("suggested-action")
        open_wheel_btn.add_css_class("pill")
        open_wheel_btn.set_valign(Gtk.Align.CENTER)
        open_wheel_btn.connect("clicked", lambda b: self._open_aroma_wheel_dialog())
        wheel_row.add_suffix(open_wheel_btn)
        aroma_grp.add(wheel_row)

        # Chips container
        self.aroma_chips_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.aroma_chips_container.set_margin_top(8)
        self.aroma_chips_container.set_margin_bottom(8)
        self.aroma_chips_container.set_margin_start(12)
        self.aroma_chips_container.set_margin_end(12)

        self.aroma_flowbox = Gtk.FlowBox.new()
        self.aroma_flowbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.aroma_flowbox.set_column_spacing(6)
        self.aroma_flowbox.set_row_spacing(6)
        self.aroma_chips_container.append(self.aroma_flowbox)

        # Button to append keywords into tasting notes description
        self.append_notes_btn = Gtk.Button.new_with_label("Append Keywords to Notes Description")
        self.append_notes_btn.add_css_class("flat")
        self.append_notes_btn.add_css_class("caption")
        self.append_notes_btn.set_halign(Gtk.Align.START)
        self.append_notes_btn.connect("clicked", lambda b: self._append_keywords_to_notes())
        self.aroma_chips_container.append(self.append_notes_btn)

        aroma_grp.add(self.aroma_chips_container)
        page.add(aroma_grp)

        self._refresh_dialog_aroma_chips()

        # --- Group 4: Technical Specifications ---
        tech_grp = Adw.PreferencesGroup.new()
        tech_grp.set_title("Technical and Service Details")

        abv_val = self.wine.abv if (self.is_edit and self.wine.abv is not None) else 13.5
        adj_abv = Gtk.Adjustment.new(abv_val, 0.0, 30.0, 0.5, 1.0, 0)
        self.abv_row = Adw.SpinRow.new(adj_abv, 0.5, 1)
        self.abv_row.set_title("Alcohol by Volume (% ABV)")
        tech_grp.add(self.abv_row)

        temp_val = self.wine.serving_temperature if (self.is_edit and self.wine.serving_temperature is not None) else 16
        adj_temp = Gtk.Adjustment.new(temp_val, 0, 30, 1, 2, 0)
        self.temp_row = Adw.SpinRow.new(adj_temp, 1, 0)
        self.temp_row.set_title("Serving Temperature (°C)")
        tech_grp.add(self.temp_row)

        # Bottle Size
        self.size_row = Adw.ComboRow.new()
        self.size_row.set_title("Bottle Size")
        size_list = Gtk.StringList.new([label for label, _ in BOTTLE_SIZES])
        self.size_row.set_model(size_list)
        selected_size_idx = 0
        if self.is_edit and self.wine.bottle_size:
            for idx, (_, val) in enumerate(BOTTLE_SIZES):
                if abs(val - self.wine.bottle_size) < 0.01:
                    selected_size_idx = idx
                    break
        self.size_row.set_selected(selected_size_idx)
        tech_grp.add(self.size_row)

        # Closure
        self.closure_row = Adw.ComboRow.new()
        self.closure_row.set_title("Closure Type")
        closure_list = Gtk.StringList.new(CLOSURE_TYPES)
        self.closure_row.set_model(closure_list)
        if self.is_edit and self.wine.closure_type in CLOSURE_TYPES:
            self.closure_row.set_selected(CLOSURE_TYPES.index(self.wine.closure_type))
        else:
            self.closure_row.set_selected(0)
        tech_grp.add(self.closure_row)

        self.organic_row = Adw.SwitchRow.new()
        self.organic_row.set_title("Certified Organic")
        if self.is_edit:
            self.organic_row.set_active(self.wine.organic)
        tech_grp.add(self.organic_row)

        self.biodynamic_row = Adw.SwitchRow.new()
        self.biodynamic_row.set_title("Certified Biodynamic")
        if self.is_edit:
            self.biodynamic_row.set_active(self.wine.biodynamic)
        tech_grp.add(self.biodynamic_row)

        page.add(tech_grp)

        # --- Group 5: Cellar & Food Pairing ---
        cellar_grp = Adw.PreferencesGroup.new()
        cellar_grp.set_title("Cellar, Food Pairing and Purchase")

        self.price_row = Adw.EntryRow.new()
        self.price_row.set_title("Price Paid")
        if self.is_edit and self.wine.price is not None:
            self.price_row.set_text(f"{self.wine.price:.2f}")
        cellar_grp.add(self.price_row)

        self.location_row = Adw.EntryRow.new()
        self.location_row.set_title("Purchase Location / Merchant")
        if self.is_edit and self.wine.purchase_location:
            self.location_row.set_text(self.wine.purchase_location)
        cellar_grp.add(self.location_row)

        self.aging_row = Adw.EntryRow.new()
        self.aging_row.set_title("Aging Potential (e.g. 2026 - 2040)")
        if self.is_edit and self.wine.aging_potential:
            self.aging_row.set_text(self.wine.aging_potential)
        cellar_grp.add(self.aging_row)

        self.pairing_row = Adw.EntryRow.new()
        self.pairing_row.set_title("Food Pairing Suggestions")
        if self.is_edit and self.wine.food_pairing:
            self.pairing_row.set_text(self.wine.food_pairing)
        cellar_grp.add(self.pairing_row)

        page.add(cellar_grp)

        # Assemble layout
        self.toast_overlay.set_child(page)
        self.toolbar_view.set_content(self.toast_overlay)
        self.set_child(self.toolbar_view)

    def _show_toast(self, message: str):
        toast = Adw.Toast.new(message)
        toast.set_timeout(3)
        self.toast_overlay.add_toast(toast)

    def _on_save_clicked(self, _btn):
        name = self.name_row.get_text().strip()
        winery = self.winery_row.get_text().strip()
        country = self.country_row.get_text().strip()

        start_iter = self.notes_buffer.get_start_iter()
        end_iter = self.notes_buffer.get_end_iter()
        notes = self.notes_buffer.get_text(start_iter, end_iter, True).strip()

        # Basic validations
        if not name:
            self._show_toast("Please enter a Wine Name.")
            self.name_row.grab_focus()
            return

        if not winery:
            self._show_toast("Please enter the Winery / Producer.")
            self.winery_row.grab_focus()
            return

        if not country:
            self._show_toast("Please enter the Country of origin.")
            self.country_row.grab_focus()
            return

        if not notes:
            self._show_toast("Please provide your Tasting Notes.")
            return

        # Parse vintage
        vintage_raw = int(self.vintage_row.get_value())
        vintage = None if vintage_raw <= 1800 else vintage_raw

        # Parse style
        style_idx = self.style_row.get_selected()
        color_style = COLOR_STYLES[style_idx] if style_idx < len(COLOR_STYLES) else "Red"

        # Parse closure
        closure_idx = self.closure_row.get_selected()
        closure_type = CLOSURE_TYPES[closure_idx] if closure_idx < len(CLOSURE_TYPES) else "Cork"

        # Parse bottle size
        size_idx = self.size_row.get_selected()
        bottle_size = BOTTLE_SIZES[size_idx][1] if size_idx < len(BOTTLE_SIZES) else 0.75

        # Parse price
        price = None
        price_str = self.price_row.get_text().strip().replace("$", "").replace("£", "").replace("€", "")
        if price_str:
            try:
                price = float(price_str)
            except ValueError:
                self._show_toast("Invalid price value. Please enter a number.")
                self.price_row.grab_focus()
                return

        # Rating and date
        rating = int(self.rating_row.get_value())
        tasting_date = self.date_row.get_text().strip() or date.today().isoformat()

        # Construct Wine object
        wine_id = self.wine.id if self.is_edit else None

        saved_wine = Wine(
            id=wine_id,
            wine_name=name,
            winery=winery,
            country=country,
            region=self.region_row.get_text().strip() or None,
            sub_region=self.sub_region_row.get_text().strip() or None,
            vintage=vintage,
            color_style=color_style,
            grape_variety=self.grape_row.get_text().strip(),
            abv=float(self.abv_row.get_value()),
            price=price,
            tasting_date=tasting_date,
            rating=rating,
            tasting_notes=notes,
            serving_temperature=int(self.temp_row.get_value()),
            aging_potential=self.aging_row.get_text().strip() or None,
            food_pairing=self.pairing_row.get_text().strip() or None,
            purchase_location=self.location_row.get_text().strip() or None,
            bottle_size=bottle_size,
            closure_type=closure_type,
            organic=self.organic_row.get_active(),
            biodynamic=self.biodynamic_row.get_active(),
            aroma_notes=list(self.aroma_keywords),
        )

        validation_errors = saved_wine.validate()
        if validation_errors:
            self._show_toast(validation_errors[0])
            return

        if self.on_save:
            self.on_save(saved_wine)

        self.close()

    def _open_aroma_wheel_dialog(self):
        def on_apply(keywords: List[str], generated_sentence: Optional[str]):
            self.aroma_keywords = keywords
            self._refresh_dialog_aroma_chips()
            if generated_sentence:
                self._insert_into_notes(generated_sentence)

        dlg = AromaWheelDialog(
            initial_keywords=self.aroma_keywords,
            on_apply=on_apply,
            allow_append_to_notes=True,
        )
        dlg.present(self)

    def _refresh_dialog_aroma_chips(self):
        while child := self.aroma_flowbox.get_first_child():
            self.aroma_flowbox.remove(child)

        if not self.aroma_keywords:
            empty_lbl = Gtk.Label(
                label="No aroma keywords selected yet. Click 'Open Tasting Wheel' to select aromas.",
                xalign=0.0,
            )
            empty_lbl.add_css_class("dim-label")
            empty_lbl.add_css_class("caption")
            self.aroma_flowbox.append(empty_lbl)
            self.append_notes_btn.set_sensitive(False)
            return

        self.append_notes_btn.set_sensitive(True)
        for kw in sorted(self.aroma_keywords):
            chip = Gtk.Button(label=f"{kw}  ×")
            chip.add_css_class("pill")
            chip.add_css_class("aroma-chip-btn")
            chip.add_css_class(get_descriptor_css_class(kw))
            chip.set_tooltip_text(f"Remove '{kw}'")
            chip.connect("clicked", self._remove_dialog_keyword, kw)
            self.aroma_flowbox.append(chip)

    def _remove_dialog_keyword(self, _btn, keyword: str):
        if keyword in self.aroma_keywords:
            self.aroma_keywords.remove(keyword)
            self._refresh_dialog_aroma_chips()

    def _append_keywords_to_notes(self):
        if not self.aroma_keywords:
            return
        sentence = format_keywords_sentence(self.aroma_keywords)
        if sentence:
            self._insert_into_notes(sentence)

    def _insert_into_notes(self, sentence: str):
        start_iter = self.notes_buffer.get_start_iter()
        end_iter = self.notes_buffer.get_end_iter()
        current_text = self.notes_buffer.get_text(start_iter, end_iter, True).strip()

        if not current_text:
            self.notes_buffer.set_text(sentence)
        elif sentence not in current_text:
            self.notes_buffer.set_text(f"{current_text} {sentence}")
        self._show_toast("Added keywords to notes description.")
