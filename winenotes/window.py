"""
Main application window featuring an adaptive split-view interface.
"""

from __future__ import annotations
from typing import Optional, List
from pathlib import Path
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gio, GLib

from winenotes.models import Wine, COLOR_STYLES
from winenotes.db import Database
from winenotes.wine_row import WineRow
from winenotes.wine_detail import WineDetailView
from winenotes.wine_dialog import WineDialog
from winenotes.stats_dialog import StatsDialog
from winenotes.aroma_dialog import AromaWheelDialog
from winenotes.sample_data import SAMPLE_WINES

CHANGELOG_URL = (
    "https://github.com/jubbathejack/wine-tasting-notes-app/blob/develop/CHANGELOG.md"
)

STYLE_FILTERS = ["All Styles"] + COLOR_STYLES

SORT_OPTIONS = [
    ("Date: Newest", "date_desc"),
    ("Date: Oldest", "date_asc"),
    ("Rating: Highest", "rating_desc"),
    ("Rating: Lowest", "rating_asc"),
    ("Vintage: Newest", "vintage_desc"),
    ("Name: A-Z", "name_asc"),
    ("Drink Window", "drink_from_asc"),
    ("Date Added", "date_added_desc"),
]

class MainWindow(Adw.ApplicationWindow):
    def __init__(self, app: Adw.Application, db: Database):
        super().__init__(application=app)
        self.db = db
        self._view_mode = "collection"  # "collection" or "cellar"
        self.selected_wine: Optional[Wine] = None
        self._last_deleted_wine: Optional[Wine] = None

        self.set_title("Wine Tasting Notes")
        self.set_default_size(1120, 780)
        self.set_size_request(380, 480)

        # Main Toast Overlay
        self.toast_overlay = Adw.ToastOverlay.new()
        self.set_content(self.toast_overlay)

        # Navigation Split View
        self.split_view = Adw.NavigationSplitView.new()
        self.split_view.set_min_sidebar_width(340)
        self.split_view.set_max_sidebar_width(460)
        self.toast_overlay.set_child(self.split_view)

        # Setup sidebar and content
        self._build_sidebar()
        self._build_content()
        self._setup_window_actions()

        # Seed sample data if database is brand new
        if self.db.count() == 0:
            self.db.seed_samples()

        self._update_sample_actions()

        # Initial list load
        self.reload_wines()

    def _build_sidebar(self):
        sidebar_page = Adw.NavigationPage.new(Gtk.Box(), "Wines")
        sidebar_page.set_tag("sidebar")

        toolbar_view = Adw.ToolbarView.new()

        # HeaderBar
        header = Adw.HeaderBar.new()
        header.set_show_title(True)

        # Add Wine button (+)
        self.add_btn = Gtk.Button.new_from_icon_name("list-add-symbolic")
        self.add_btn.set_tooltip_text("Record New Wine Tasting (Ctrl+N)")
        self.add_btn.connect("clicked", lambda b: self.open_add_dialog())
        header.pack_start(self.add_btn)

        # Primary Menu Button
        menu_btn = Gtk.MenuButton.new()
        menu_btn.set_icon_name("open-menu-symbolic")
        menu_btn.set_tooltip_text("Main Menu")

        menu = Gio.Menu.new()
        menu.append("Wine Aroma Wheel Reference", "win.show-aroma-wheel")
        menu.append("Collection Statistics", "win.show-stats")
        menu.append("Add Sample Wines", "win.seed-samples")
        menu.append("Remove Sample Wines", "win.remove-samples")

        data_section = Gio.Menu.new()
        data_section.append("Export to JSON...", "win.export-json")
        data_section.append("Export to CSV...", "win.export-csv")
        data_section.append("Import from JSON...", "win.import-json")
        menu.append_section(None, data_section)

        about_section = Gio.Menu.new()
        about_section.append("Changelog", "win.show-changelog")
        about_section.append("About Wine Notes", "app.about")
        menu.append_section(None, about_section)

        menu_btn.set_menu_model(menu)
        header.pack_end(menu_btn)

        toolbar_view.add_top_bar(header)

        # Sidebar content box
        sidebar_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        sidebar_vbox.set_margin_top(8)
        sidebar_vbox.set_margin_bottom(8)
        sidebar_vbox.set_margin_start(10)
        sidebar_vbox.set_margin_end(10)

        # View Switcher (Collection vs Cellar)
        view_switcher_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        view_switcher_box.add_css_class("linked")
        view_switcher_box.set_halign(Gtk.Align.FILL)
        view_switcher_box.set_hexpand(True)

        self.collection_btn = Gtk.ToggleButton(label="🍷  Collection")
        self.collection_btn.set_hexpand(True)
        self.collection_btn.set_active(True)
        self.collection_btn.connect("toggled", self._on_view_switched)

        self.cellar_btn = Gtk.ToggleButton(label="🏠  Cellar")
        self.cellar_btn.set_hexpand(True)
        self.cellar_btn.set_group(self.collection_btn)
        self.cellar_btn.connect("toggled", self._on_view_switched)

        view_switcher_box.append(self.collection_btn)
        view_switcher_box.append(self.cellar_btn)
        sidebar_vbox.append(view_switcher_box)

        # Search Entry
        self.search_entry = Gtk.SearchEntry.new()
        self.search_entry.set_placeholder_text("Search wines, grapes, regions...")
        self.search_entry.connect("search-changed", lambda e: self.reload_wines())
        sidebar_vbox.append(self.search_entry)

        # Filter & Sort Bar
        filter_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        # Style filter dropdown
        self.style_dropdown = Gtk.DropDown.new_from_strings(STYLE_FILTERS)
        self.style_dropdown.set_hexpand(True)
        self.style_dropdown.connect("notify::selected", lambda dd, ps: self.reload_wines())
        filter_box.append(self.style_dropdown)

        # Sort dropdown
        sort_labels = [label for label, _ in SORT_OPTIONS]
        self.sort_dropdown = Gtk.DropDown.new_from_strings(sort_labels)
        self.sort_dropdown.set_hexpand(True)
        self.sort_dropdown.connect("notify::selected", lambda dd, ps: self.reload_wines())
        filter_box.append(self.sort_dropdown)

        sidebar_vbox.append(filter_box)

        # Stack for List vs Empty State
        self.list_stack = Gtk.Stack.new()
        self.list_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.list_stack.set_vexpand(True)

        # 1. Scrolled ListBox
        scrolled = Gtk.ScrolledWindow.new()
        scrolled.set_vexpand(True)
        self.list_box = Gtk.ListBox.new()
        self.list_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.list_box.add_css_class("boxed-list")
        self.list_box.connect("row-selected", self._on_row_selected)
        scrolled.set_child(self.list_box)
        self.list_stack.add_named(scrolled, "list")

        # 2. Empty Status Page (Collection)
        self.empty_page = Adw.StatusPage.new()
        self.empty_page.set_icon_name("starred-symbolic")
        self.empty_page.set_title("No Wines Found")
        self.empty_page.set_description("Record your first tasting note or clear your search query.")
        empty_add_btn = Gtk.Button(label="Add Wine Tasting")
        empty_add_btn.add_css_class("suggested-action")
        empty_add_btn.add_css_class("pill")
        empty_add_btn.set_halign(Gtk.Align.CENTER)
        empty_add_btn.connect("clicked", lambda b: self.open_add_dialog())
        self.empty_page.set_child(empty_add_btn)
        self.list_stack.add_named(self.empty_page, "empty")

        # 3. Empty Status Page (Cellar)
        self.empty_cellar_page = Adw.StatusPage.new()
        self.empty_cellar_page.set_icon_name("user-home-symbolic")
        self.empty_cellar_page.set_title("Your Cellar is Empty")
        self.empty_cellar_page.set_description("Track bottles you own and want to age before tasting.")
        empty_cellar_btn = Gtk.Button(label="Add Wine to Cellar")
        empty_cellar_btn.add_css_class("suggested-action")
        empty_cellar_btn.add_css_class("pill")
        empty_cellar_btn.set_halign(Gtk.Align.CENTER)
        empty_cellar_btn.connect("clicked", lambda b: self.open_add_cellar_dialog())
        self.empty_cellar_page.set_child(empty_cellar_btn)
        self.list_stack.add_named(self.empty_cellar_page, "empty_cellar")

        sidebar_vbox.append(self.list_stack)
        toolbar_view.set_content(sidebar_vbox)
        sidebar_page.set_child(toolbar_view)
        self.split_view.set_sidebar(sidebar_page)

    def _build_content(self):
        content_page = Adw.NavigationPage.new(Gtk.Box(), "Wine Details")
        content_page.set_tag("content")

        toolbar_view = Adw.ToolbarView.new()

        # HeaderBar for Content
        content_header = Adw.HeaderBar.new()

        # Mark as Tasted button (Cellar mode only)
        self.taste_btn = Gtk.Button.new_from_icon_name("emblem-ok-symbolic")
        self.taste_btn.set_tooltip_text("Mark as Tasted (Open a bottle from your cellar)")
        self.taste_btn.set_sensitive(False)
        self.taste_btn.set_visible(False)
        self.taste_btn.connect("clicked", lambda b: self.open_mark_as_tasted_dialog())
        content_header.pack_end(self.taste_btn)

        # Edit button
        self.edit_btn = Gtk.Button.new_from_icon_name("document-edit-symbolic")
        self.edit_btn.set_tooltip_text("Edit (Ctrl+E)")
        self.edit_btn.set_sensitive(False)
        self.edit_btn.connect("clicked", lambda b: self.open_edit_dialog())
        content_header.pack_end(self.edit_btn)

        # Delete button
        self.delete_btn = Gtk.Button.new_from_icon_name("user-trash-symbolic")
        self.delete_btn.set_tooltip_text("Delete")
        self.delete_btn.set_sensitive(False)
        self.delete_btn.connect("clicked", lambda b: self.confirm_delete_selected())
        content_header.pack_end(self.delete_btn)

        toolbar_view.add_top_bar(content_header)

        # Content Stack: Placeholder vs Detail View
        self.content_stack = Gtk.Stack.new()
        self.content_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)

        # Placeholder StatusPage
        self.placeholder = Adw.StatusPage.new()
        self.placeholder.set_icon_name("starred-symbolic")
        self.placeholder.set_title("No Wine Selected")
        self.placeholder.set_description("Select a wine from the list to view its details.")
        self.content_stack.add_named(self.placeholder, "placeholder")

        # Detail View
        self.detail_view = WineDetailView()
        self.content_stack.add_named(self.detail_view, "detail")

        toolbar_view.set_content(self.content_stack)
        content_page.set_child(toolbar_view)
        self.split_view.set_content(content_page)

    def _setup_window_actions(self):
        # Action: Show Aroma Wheel Reference
        wheel_action = Gio.SimpleAction.new("show-aroma-wheel", None)
        wheel_action.connect("activate", lambda a, p: self.show_aroma_wheel_dialog())
        self.add_action(wheel_action)

        # Action: Open Changelog
        changelog_action = Gio.SimpleAction.new("show-changelog", None)
        changelog_action.connect("activate", lambda a, p: self.show_changelog())
        self.add_action(changelog_action)

        # Action: Show Stats
        stats_action = Gio.SimpleAction.new("show-stats", None)
        stats_action.connect("activate", lambda a, p: self.show_stats_dialog())
        self.add_action(stats_action)

        # Action: Add Samples
        self._add_samples_action = Gio.SimpleAction.new("seed-samples", None)
        self._add_samples_action.connect(
            "activate", lambda a, p: self.seed_samples()
        )
        self.add_action(self._add_samples_action)

        # Action: Remove Samples
        self._remove_samples_action = Gio.SimpleAction.new("remove-samples", None)
        self._remove_samples_action.connect(
            "activate", lambda a, p: self.remove_samples()
        )
        self.add_action(self._remove_samples_action)

        # Action: Export JSON
        export_json_action = Gio.SimpleAction.new("export-json", None)
        export_json_action.connect("activate", lambda a, p: self.export_json_flow())
        self.add_action(export_json_action)

        # Action: Export CSV
        export_csv_action = Gio.SimpleAction.new("export-csv", None)
        export_csv_action.connect("activate", lambda a, p: self.export_csv_flow())
        self.add_action(export_csv_action)

        # Action: Import JSON
        import_json_action = Gio.SimpleAction.new("import-json", None)
        import_json_action.connect("activate", lambda a, p: self.import_json_flow())
        self.add_action(import_json_action)

    def _on_view_switched(self, btn):
        if not btn.get_active():
            return
        if btn == self.collection_btn:
            self._view_mode = "collection"
            self.add_btn.set_tooltip_text("Record New Wine Tasting (Ctrl+N)")
        else:
            self._view_mode = "cellar"
            self.add_btn.set_tooltip_text("Add Wine to Cellar (Ctrl+N)")

        self.selected_wine = None
        self.content_stack.set_visible_child_name("placeholder")
        self.edit_btn.set_sensitive(False)
        self.delete_btn.set_sensitive(False)
        self.taste_btn.set_visible(self._view_mode == "cellar")
        self.taste_btn.set_sensitive(False)
        self.reload_wines()

    def show_toast(self, message: str, undo_callback=None):
        toast = Adw.Toast.new(message)
        toast.set_timeout(4)
        if undo_callback:
            toast.set_button_label("Undo")
            toast.connect("button-clicked", lambda t: undo_callback())
        self.toast_overlay.add_toast(toast)

    def reload_wines(self, select_id: Optional[int] = None):
        search_query = self.search_entry.get_text().strip()

        style_idx = self.style_dropdown.get_selected()
        style_filter = STYLE_FILTERS[style_idx] if style_idx < len(STYLE_FILTERS) else None
        if style_filter == "All Styles":
            style_filter = None

        sort_idx = self.sort_dropdown.get_selected()
        sort_by = SORT_OPTIONS[sort_idx][1] if sort_idx < len(SORT_OPTIONS) else "date_desc"

        if self._view_mode == "cellar":
            wines = self.db.list_cellar(search=search_query, style_filter=style_filter, sort_by=sort_by)
            empty_child = "empty_cellar"
        else:
            wines = self.db.list_tasted(search=search_query, style_filter=style_filter, sort_by=sort_by)
            empty_child = "empty"

        # Clear list
        while row := self.list_box.get_first_child():
            self.list_box.remove(row)

        target_row = None
        if wines:
            self.list_stack.set_visible_child_name("list")
            for wine in wines:
                row = WineRow(wine)
                self.list_box.append(row)
                if select_id is not None and wine.id == select_id:
                    target_row = row
                elif self.selected_wine and wine.id == self.selected_wine.id and target_row is None:
                    target_row = row

            if target_row:
                self.list_box.select_row(target_row)
            elif not self.selected_wine:
                first_row = self.list_box.get_row_at_index(0)
                if first_row:
                    self.list_box.select_row(first_row)
        else:
            self.list_stack.set_visible_child_name(empty_child)
            self.content_stack.set_visible_child_name("placeholder")
            self.selected_wine = None
            self.edit_btn.set_sensitive(False)
            self.delete_btn.set_sensitive(False)
            self.taste_btn.set_sensitive(False)

    def _on_row_selected(self, _box, row):
        if row is None or not isinstance(row, WineRow):
            self.selected_wine = None
            self.content_stack.set_visible_child_name("placeholder")
            self.edit_btn.set_sensitive(False)
            self.delete_btn.set_sensitive(False)
            self.taste_btn.set_sensitive(False)
            return

        self.selected_wine = row.wine
        self.detail_view.display_wine(row.wine)
        self.content_stack.set_visible_child_name("detail")
        self.edit_btn.set_sensitive(True)
        self.delete_btn.set_sensitive(True)

        if self._view_mode == "cellar":
            self.taste_btn.set_visible(True)
            self.taste_btn.set_sensitive(True)
        else:
            self.taste_btn.set_visible(False)
            self.taste_btn.set_sensitive(False)

        # For adaptive layout (collapsed on small screen)
        self.split_view.set_show_content(True)

    def open_add_dialog(self):
        if self._view_mode == "cellar":
            self.open_add_cellar_dialog()
        else:
            self._open_add_tasting_dialog()

    def _open_add_tasting_dialog(self):
        def on_saved(new_wine: Wine):
            wine_id = self.db.insert(new_wine, in_cellar=False)
            self.show_toast(f"Recorded '{new_wine.wine_name}'")
            self.reload_wines(select_id=wine_id)

        dialog = WineDialog(wine=None, on_save=on_saved, cellar_mode=False, db=self.db)
        dialog.present(self)

    def open_add_cellar_dialog(self):
        def on_saved(new_wine: Wine):
            wine_id = self.db.insert(new_wine, in_cellar=True)
            self.show_toast(f"Added '{new_wine.wine_name}' to cellar")
            self.reload_wines(select_id=wine_id)

        dialog = WineDialog(wine=None, on_save=on_saved, cellar_mode=True, db=self.db)
        dialog.present(self)

    def open_edit_dialog(self):
        if not self.selected_wine:
            return

        is_cellar = self.selected_wine.in_cellar

        def on_saved(updated_wine: Wine):
            self.db.update(updated_wine)
            self.show_toast(f"Updated '{updated_wine.wine_name}'")
            self.reload_wines(select_id=updated_wine.id)

        dialog = WineDialog(wine=self.selected_wine, on_save=on_saved, cellar_mode=is_cellar, db=self.db)
        dialog.present(self)

    def open_mark_as_tasted_dialog(self):
        if not self.selected_wine or not self.selected_wine.in_cellar:
            return

        cellar_wine = self.selected_wine

        # Create a pre-filled Wine copy for tasting note
        tasting_wine = Wine(
            wine_name=cellar_wine.wine_name,
            winery=cellar_wine.winery,
            country=cellar_wine.country,
            region=cellar_wine.region,
            sub_region=cellar_wine.sub_region,
            vintage=cellar_wine.vintage,
            color_style=cellar_wine.color_style,
            grape_variety=cellar_wine.grape_variety,
            abv=cellar_wine.abv,
            price=cellar_wine.price,
            purchase_location=cellar_wine.purchase_location,
            purchase_date=cellar_wine.purchase_date,
            bottle_size=cellar_wine.bottle_size,
            closure_type=cellar_wine.closure_type,
            organic=cellar_wine.organic,
            biodynamic=cellar_wine.biodynamic,
            aging_potential=cellar_wine.aging_potential,
            food_pairing=cellar_wine.food_pairing,
            in_cellar=False,
            bottles=1,
        )

        def on_saved(new_tasted_wine: Wine):
            # Insert the new tasted wine
            new_id = self.db.insert(new_tasted_wine, in_cellar=False)

            # Decrement cellar entry count (or delete if 0)
            remaining = self.db.decrement_or_delete_cellar(cellar_wine.id)
            if remaining > 0:
                noun = "bottle" if remaining == 1 else "bottles"
                self.show_toast(f"Added to Collection · {remaining} {noun} remaining in cellar")
            else:
                self.show_toast("Added to Collection")

            # Switch to collection view to see the new tasting note
            self.collection_btn.set_active(True)
            self.reload_wines(select_id=new_id)

        dialog = WineDialog(wine=tasting_wine, on_save=on_saved, cellar_mode=False, db=self.db)
        dialog.present(self)

    def confirm_delete_selected(self):
        if not self.selected_wine:
            return

        wine = self.selected_wine
        entity_name = "Cellar Entry" if wine.in_cellar else "Tasting Note"
        alert = Adw.AlertDialog.new(
            f"Delete {entity_name}?",
            f"Are you sure you want to delete '{wine.wine_name}'? This action can be undone.",
        )
        alert.add_response("cancel", "Cancel")
        alert.add_response("delete", "Delete")
        alert.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)

        def on_alert_response(_dialog, response):
            if response == "delete":
                self._delete_wine(wine)

        alert.connect("response", on_alert_response)
        alert.present(self)

    def _delete_wine(self, wine: Wine):
        was_sample = self.db.is_sample(wine.id)
        self._last_deleted_wine = wine
        self.db.delete(wine.id)

        def undo():
            if self._last_deleted_wine:
                new_id = self.db.insert(
                    self._last_deleted_wine,
                    is_sample=was_sample,
                    in_cellar=self._last_deleted_wine.in_cellar,
                )
                self.show_toast(f"Restored '{self._last_deleted_wine.wine_name}'")
                self._update_sample_actions()
                self.reload_wines(select_id=new_id)

        self.show_toast(f"Deleted '{wine.wine_name}'", undo_callback=undo)
        self.selected_wine = None
        self._update_sample_actions()
        self.reload_wines()

    def show_aroma_wheel_dialog(self):
        dialog = AromaWheelDialog(initial_keywords=[], allow_append_to_notes=False)
        dialog.present(self)

    def show_changelog(self):
        launcher = Gtk.UriLauncher.new(CHANGELOG_URL)
        launcher.launch(self, None, self._on_changelog_launched)

    def _on_changelog_launched(self, launcher, result):
        try:
            launcher.launch_finish(result)
        except GLib.Error:
            self.show_toast("Could not open the changelog")

    def show_stats_dialog(self):
        stats = self.db.get_stats()
        dialog = StatsDialog(stats)
        dialog.present(self)

    def _update_sample_actions(self):
        sample_count = self.db.sample_count()
        self._add_samples_action.set_enabled(sample_count < len(SAMPLE_WINES))
        self._remove_samples_action.set_enabled(sample_count > 0)

    def seed_samples(self):
        count = self.db.seed_samples()
        if count > 0:
            self.show_toast(f"Added {count} sample wine tasting notes!")
        else:
            self.show_toast("Sample wines already exist in your collection.")
        self._update_sample_actions()
        self.reload_wines()

    def remove_samples(self):
        count = self.db.sample_count()
        if count == 0:
            self.show_toast("No sample wines to remove.")
            return

        noun = "note" if count == 1 else "notes"
        alert = Adw.AlertDialog.new(
            "Remove Sample Wines?",
            f"Remove {count} sample wine tasting {noun} from your collection? This action can be undone.",
        )
        alert.add_response("cancel", "Cancel")
        alert.add_response("remove", "Remove")
        alert.set_response_appearance("remove", Adw.ResponseAppearance.DESTRUCTIVE)

        def on_alert_response(_dialog, response):
            if response == "remove":
                self._remove_samples()

        alert.connect("response", on_alert_response)
        alert.present(self)

    def _remove_samples(self):
        samples = self.db.remove_samples()
        if not samples:
            return

        noun = "wine" if len(samples) == 1 else "wines"

        def undo():
            for wine in samples:
                self.db.insert(wine, is_sample=True, in_cellar=False)
            self.show_toast(f"Restored {len(samples)} sample {noun}")
            self._update_sample_actions()
            self.reload_wines()

        self.show_toast(
            f"Removed {len(samples)} sample {noun}", undo_callback=undo
        )
        self.selected_wine = None
        self._update_sample_actions()
        self.reload_wines()

    def export_json_flow(self):
        file_dialog = Gtk.FileDialog.new()
        file_dialog.set_title("Export Wine Notes to JSON")
        file_dialog.set_initial_name("wine_tasting_notes.json")

        def on_save_response(dialog, result):
            try:
                gfile = dialog.save_finish(result)
                if gfile:
                    count = self.db.export_json(gfile.get_path())
                    self.show_toast(f"Exported {count} wines to {gfile.get_basename()}")
            except GLib.Error:
                pass

        file_dialog.save(self, None, on_save_response)

    def export_csv_flow(self):
        file_dialog = Gtk.FileDialog.new()
        file_dialog.set_title("Export Wine Notes to CSV")
        file_dialog.set_initial_name("wine_tasting_notes.csv")

        def on_save_response(dialog, result):
            try:
                gfile = dialog.save_finish(result)
                if gfile:
                    count = self.db.export_csv(gfile.get_path())
                    self.show_toast(f"Exported {count} wines to {gfile.get_basename()}")
            except GLib.Error:
                pass

        file_dialog.save(self, None, on_save_response)

    def import_json_flow(self):
        file_dialog = Gtk.FileDialog.new()
        file_dialog.set_title("Import Wine Notes from JSON")

        def on_open_response(dialog, result):
            try:
                gfile = dialog.open_finish(result)
                if gfile:
                    count = self.db.import_json(gfile.get_path())
                    self.show_toast(f"Successfully imported {count} wines!")
                    self.reload_wines()
            except Exception as e:
                self.show_toast(f"Import failed: {e}")

        file_dialog.open(self, None, on_open_response)
