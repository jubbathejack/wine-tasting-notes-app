"""
Adw.Application implementation for Wine Notes.
"""

from __future__ import annotations
import sys
from pathlib import Path
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gio, Gdk

from winenotes import __version__, __app_id__
from winenotes.db import Database
from winenotes.window import MainWindow

class WineNotesApplication(Adw.Application):
    def __init__(self, db_path: str | Path | None = None):
        super().__init__(
            application_id=__app_id__,
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )
        self.db_path = db_path
        self.window: MainWindow | None = None

    def do_startup(self):
        Adw.Application.do_startup(self)
        self._load_css()
        self._setup_app_actions()

    def do_activate(self):
        Adw.Application.do_activate(self)
        if not self.window:
            db = Database(self.db_path)
            self.window = MainWindow(self, db)
        self.window.present()

    def _load_css(self):
        css_file = Path(__file__).parent / "style.css"
        if css_file.exists():
            provider = Gtk.CssProvider.new()
            provider.load_from_path(str(css_file))
            display = Gdk.Display.get_default()
            if display:
                Gtk.StyleContext.add_provider_for_display(
                    display,
                    provider,
                    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
                )

    def _setup_app_actions(self):
        # Quit action
        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", lambda a, p: self.quit())
        self.add_action(quit_action)
        self.set_accels_for_action("app.quit", ["<primary>q"])

        # About action
        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", lambda a, p: self._show_about_dialog())
        self.add_action(about_action)

    def _show_about_dialog(self):
        dialog = Adw.AboutDialog.new()
        dialog.set_application_name("Wine Tasting Notes")
        dialog.set_application_icon(__app_id__)
        dialog.set_version(__version__)
        dialog.set_developer_name("Jack Parker")
        dialog.set_developers(["Jack Parker"])
        dialog.set_comments(
            "An elegant GNOME desktop application for recording, rating, and managing personal wine tasting notes."
        )
        dialog.set_website("https://github.com/jubbathejack/wine-tasting-notes-app")
        dialog.set_issue_url(
            "https://github.com/jubbathejack/wine-tasting-notes-app/issues"
        )
        dialog.set_license_type(Gtk.License.MIT_X11)
        dialog.set_copyright("© 2026 Jack Parker")
        if self.window:
            dialog.present(self.window)
        else:
            dialog.present()

def main():
    app = WineNotesApplication()
    return app.run(sys.argv)

if __name__ == "__main__":
    sys.exit(main())
