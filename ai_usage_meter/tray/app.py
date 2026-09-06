#!/usr/bin/env python3
"""The tray app: one AppIndicator, re-read the snapshot every 30 seconds.
Single-instance through the GtkApplication id."""
import os
import sys
from datetime import datetime, timezone

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import gi  # noqa: E402

gi.require_version("Gtk", "3.0")
gi.require_version("AppIndicator3", "0.1")
from gi.repository import AppIndicator3, GLib, Gtk  # noqa: E402

from ai_usage_meter.core import display as display_rules  # noqa: E402
from ai_usage_meter.core.store import SnapshotStore  # noqa: E402
from ai_usage_meter.tray import label  # noqa: E402

APPLICATION_ID = "io.github.vitdohnalek.AiUsageMeter"
INDICATOR_ID = "ai-usage-meter"
REFRESH_SECONDS = 30
LABEL_GUIDE = "100%! · 100%!"


class MeterTray(Gtk.Application):
    def __init__(self, store=None):
        super().__init__(application_id=APPLICATION_ID)
        self.store = store or SnapshotStore.default()
        self.indicator = None
        self.rows = []

    def do_activate(self):
        if self.indicator is not None:
            return
        self.hold()
        self.indicator = AppIndicator3.Indicator.new(
            INDICATOR_ID, label.NORMAL_ICON, AppIndicator3.IndicatorCategory.APPLICATION_STATUS)
        self.indicator.set_icon_theme_path(str(label.ICON_DIR))
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self.indicator.set_menu(self._build_menu())
        self.refresh()
        GLib.timeout_add_seconds(REFRESH_SECONDS, self.refresh)

    def _build_menu(self):
        menu = Gtk.Menu()
        for _ in range(2):
            row = Gtk.MenuItem(label="")
            bar = Gtk.MenuItem(label="")
            row.set_sensitive(False)
            bar.set_sensitive(False)
            self.rows.append((row, bar))
            menu.append(row)
            menu.append(bar)
        menu.append(Gtk.SeparatorMenuItem())
        self.age_item = Gtk.MenuItem(label="")
        self.age_item.set_sensitive(False)
        menu.append(self.age_item)
        menu.append(Gtk.SeparatorMenuItem())
        quit_item = Gtk.MenuItem(label="Quit AI Usage Meter")
        quit_item.connect("activate", lambda _: self.quit())
        menu.append(quit_item)
        menu.show_all()
        return menu

    def refresh(self):
        state = display_rules.make(self.store.read(), datetime.now(timezone.utc))
        self.indicator.set_icon_full(label.icon_name(state), "AI usage")
        self.indicator.set_label(label.label_text(state), LABEL_GUIDE)
        for (row, bar), (row_text, bar_text) in zip(self.rows, label.menu_rows(state)):
            row.set_label(row_text)
            bar.set_label(bar_text)
        self.age_item.set_label(state.age_text)
        return True


def main() -> int:
    return MeterTray().run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
