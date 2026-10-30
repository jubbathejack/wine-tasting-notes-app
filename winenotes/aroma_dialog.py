"""
Dialog for exploring the Wine Aroma Wheel and selecting flavor keywords.
Integrates the interactive Cairo wheel with search, category filtering,
and instant keyword chip management.
"""

from __future__ import annotations
from typing import Set, List, Optional, Callable
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gio, GLib

from winenotes.tasting_wheel_widget import TastingWheelWidget
from winenotes.aroma_wheel_data import (
    SUBCATEGORIES,
    DESCRIPTOR_MAP,
    format_keywords_sentence,
    get_descriptor_css_class,
)


class AromaWheelDialog(Adw.Dialog):
    """
    Modal dialog providing an interactive wine aroma wheel
    and structured keyword selector.
    """

    def __init__(
        self,
        initial_keywords: Optional[List[str]] = None,
        on_apply: Optional[Callable[[List[str], Optional[str]], None]] = None,
        allow_append_to_notes: bool = True,
    ):
        super().__init__()
        self.on_apply = on_apply
        self.allow_append_to_notes = allow_append_to_notes
        self.selected_keywords: Set[str] = set(initial_keywords or [])

        self.set_title("Wine Aroma & Flavor Wheel")
        self.set_content_width(980)
        self.set_content_height(740)

        # ToolbarView layout
        self.toolbar_view = Adw.ToolbarView.new()
        header = Adw.HeaderBar.new()

        cancel_btn = Gtk.Button(label="Cancel")
        cancel_btn.connect("clicked", lambda b: self.close())
        header.pack_start(cancel_btn)

        apply_btn = Gtk.Button(label="Apply Keywords")
        apply_btn.add_css_class("suggested-action")
        apply_btn.connect("clicked", self._on_apply_clicked)
        header.pack_end(apply_btn)

        self.toolbar_view.add_top_bar(header)

        # Main horizontal split layout
        main_paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        main_paned.set_position(560)
        main_paned.set_shrink_start_child(False)
        main_paned.set_shrink_end_child(False)

        # --- Left Pane: The Interactive Wheel ---
        left_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        left_box.set_margin_start(16)
        left_box.set_margin_end(12)
        left_box.set_margin_top(12)
        left_box.set_margin_bottom(12)

        # Wheel header guidance
        guide_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        guide_label = Gtk.Label(
            label="Click any flavor segment to select/deselect. Hover to inspect details.",
            xalign=0.0,
        )
        guide_label.add_css_class("dim-label")
        guide_label.add_css_class("caption")
        guide_box.append(guide_label)
        left_box.append(guide_box)

        # Wheel widget
        self.wheel_widget = TastingWheelWidget(
            selected_descriptors=self.selected_keywords,
            on_toggle=self._on_wheel_toggled,
        )
        left_box.append(self.wheel_widget)

        main_paned.set_start_child(left_box)

        # --- Right Pane: Keywords Management & Search ---
        right_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        right_box.set_margin_start(12)
        right_box.set_margin_end(16)
        right_box.set_margin_top(12)
        right_box.set_margin_bottom(12)
        right_box.set_size_request(340, -1)

        # 1. Search bar
        self.search_entry = Gtk.SearchEntry.new()
        self.search_entry.set_placeholder_text("Search aromas (e.g. cherry, oak, mint)...")
        self.search_entry.connect("search-changed", self._on_search_changed)
        right_box.append(self.search_entry)

        # 2. Selected Keywords Tray
        tray_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        tray_card.add_css_class("card")
        tray_card.set_margin_top(2)
        tray_card.set_margin_bottom(2)

        tray_inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        tray_inner.set_margin_start(12)
        tray_inner.set_margin_end(12)
        tray_inner.set_margin_top(10)
        tray_inner.set_margin_bottom(10)

        tray_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.tray_title_label = Gtk.Label(label="Selected Keywords (0)", xalign=0.0)
        self.tray_title_label.add_css_class("heading")
        self.tray_title_label.set_hexpand(True)
        tray_header.append(self.tray_title_label)

        clear_btn = Gtk.Button(label="Clear All")
        clear_btn.add_css_class("flat")
        clear_btn.add_css_class("caption")
        clear_btn.connect("clicked", lambda b: self._clear_all_keywords())
        tray_header.append(clear_btn)
        tray_inner.append(tray_header)

        # FlowBox of selected chips
        self.selected_chips_scrolled = Gtk.ScrolledWindow.new()
        self.selected_chips_scrolled.set_min_content_height(100)
        self.selected_chips_scrolled.set_max_content_height(160)

        self.chips_flowbox = Gtk.FlowBox.new()
        self.chips_flowbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.chips_flowbox.set_column_spacing(6)
        self.chips_flowbox.set_row_spacing(6)
        self.selected_chips_scrolled.set_child(self.chips_flowbox)
        tray_inner.append(self.selected_chips_scrolled)

        tray_card.append(tray_inner)
        right_box.append(tray_card)

        # 3. Category Browser (Quick Filter / Accordion)
        browser_label = Gtk.Label(label="Browse Categories", xalign=0.0)
        browser_label.add_css_class("heading")
        right_box.append(browser_label)

        scrolled_browser = Gtk.ScrolledWindow.new()
        scrolled_browser.set_vexpand(True)

        self.categories_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        scrolled_browser.set_child(self.categories_box)
        right_box.append(scrolled_browser)

        # 4. Append to Notes Option
        if self.allow_append_to_notes:
            note_action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            note_action_box.set_margin_top(4)

            self.append_check = Gtk.CheckButton.new_with_label(
                "Also append description into tasting notes"
            )
            self.append_check.set_active(True)
            note_action_box.append(self.append_check)
            right_box.append(note_action_box)

        main_paned.set_end_child(right_box)
        self.toolbar_view.set_content(main_paned)
        self.set_child(self.toolbar_view)

        # Build category chips
        self._build_category_browser()
        self._update_selected_chips()

    def _build_category_browser(self):
        """Populate the expandable/scrollable categories with clickable descriptor chips."""
        while child := self.categories_box.get_first_child():
            self.categories_box.remove(child)

        query = self.search_entry.get_text().strip().lower()

        for subcat in SUBCATEGORIES:
            # Filter descriptors by search query
            matching_descs = [
                d for d in subcat.descriptors
                if not query or query in d.lower() or query in subcat.name.lower() or query in subcat.tier1.lower()
            ]

            if not matching_descs:
                continue

            expander = Adw.ExpanderRow.new()
            expander.set_title(GLib.markup_escape_text(f"{subcat.name} ({subcat.tier1})"))
            expander.set_subtitle(GLib.markup_escape_text(f"{len(matching_descs)} descriptors"))
            if query:
                expander.set_expanded(True)
            else:
                expander.set_expanded(False)

            flow = Gtk.FlowBox.new()
            flow.set_selection_mode(Gtk.SelectionMode.NONE)
            flow.set_column_spacing(6)
            flow.set_row_spacing(6)
            flow.set_margin_top(8)
            flow.set_margin_bottom(8)
            flow.set_margin_start(10)
            flow.set_margin_end(10)

            for desc in matching_descs:
                btn = Gtk.ToggleButton(label=desc)
                btn.set_active(desc in self.selected_keywords)
                btn.add_css_class("pill")
                btn.connect("toggled", self._on_category_btn_toggled, desc)
                flow.append(btn)

            row_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            row_box.append(flow)
            expander.add_row(row_box)
            self.categories_box.append(expander)

    def _on_wheel_toggled(self, descriptor: str, is_selected: bool):
        """Callback from wheel click."""
        if is_selected:
            self.selected_keywords.add(descriptor)
        else:
            self.selected_keywords.discard(descriptor)
        self._update_selected_chips()
        self._build_category_browser()

    def _on_category_btn_toggled(self, btn: Gtk.ToggleButton, descriptor: str):
        """Callback from category browser toggle button."""
        if btn.get_active():
            self.selected_keywords.add(descriptor)
        else:
            self.selected_keywords.discard(descriptor)
        self.wheel_widget.set_selected_descriptors(self.selected_keywords)
        self._update_selected_chips()

    def _update_selected_chips(self):
        """Refresh the selected keywords chip tray."""
        while child := self.chips_flowbox.get_first_child():
            self.chips_flowbox.remove(child)

        count = len(self.selected_keywords)
        self.tray_title_label.set_text(f"Selected Keywords ({count})")

        if count == 0:
            empty_lbl = Gtk.Label(
                label="No aromas selected yet. Click the wheel or browse below.",
                xalign=0.0,
            )
            empty_lbl.add_css_class("dim-label")
            empty_lbl.add_css_class("caption")
            self.chips_flowbox.append(empty_lbl)
            return

        sorted_keywords = sorted(self.selected_keywords)
        for keyword in sorted_keywords:
            chip_btn = Gtk.Button(label=f"{keyword}  ×")
            chip_btn.add_css_class("pill")
            chip_btn.add_css_class("aroma-chip-btn")
            chip_btn.add_css_class(get_descriptor_css_class(keyword))
            chip_btn.set_tooltip_text(f"Remove '{keyword}'")
            chip_btn.connect("clicked", self._on_remove_chip, keyword)
            self.chips_flowbox.append(chip_btn)

    def _on_remove_chip(self, _btn, keyword: str):
        self.selected_keywords.discard(keyword)
        self.wheel_widget.set_selected_descriptors(self.selected_keywords)
        self._update_selected_chips()
        self._build_category_browser()

    def _clear_all_keywords(self):
        self.selected_keywords.clear()
        self.wheel_widget.set_selected_descriptors(self.selected_keywords)
        self._update_selected_chips()
        self._build_category_browser()

    def _on_search_changed(self, _entry):
        query = self.search_entry.get_text().strip().lower()
        if not query:
            self.wheel_widget.set_highlighted_descriptors(set())
        else:
            matched = {
                desc for desc, info in DESCRIPTOR_MAP.items()
                if query in desc.lower() or query in info.tier2.lower() or query in info.tier1.lower()
            }
            self.wheel_widget.set_highlighted_descriptors(matched)
        self._build_category_browser()

    def _on_apply_clicked(self, _btn):
        keywords_list = sorted(self.selected_keywords)
        sentence = None
        if self.allow_append_to_notes and hasattr(self, "append_check") and self.append_check.get_active():
            sentence = format_keywords_sentence(keywords_list)

        if self.on_apply:
            self.on_apply(keywords_list, sentence)

        self.close()
