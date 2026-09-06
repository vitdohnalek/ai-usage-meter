# ai-usage-meter, Linux. Standard library Python for the hook, PyGObject +
# AppIndicator3 (system packages) for the tray. No pip, no venv: the tray
# needs the system-owned GI typelibs, so everything runs on /usr/bin/python3.
PYTHON    ?= python3
FILTER    ?=

PKG_DEST   = $(HOME)/.local/share/ai-usage-meter
BIN_DIR    = $(HOME)/.local/bin
HOOK_DEST  = $(BIN_DIR)/ai-usage-meter-hook
TRAY_DEST  = $(BIN_DIR)/ai-usage-meter-tray
AUTOSTART  = $(HOME)/.config/autostart/ai-usage-meter.desktop
# Matches only the running shim (python3 <shim>), never the make that spawns it.
TRAY_PATTERN = ^[^ ]*python3 $(TRAY_DEST)$$
SNAPSHOT   = $${XDG_STATE_HOME:-$(HOME)/.local/state}/ai-usage-meter

.PHONY: test install install-hook install-tray uninstall run snippet check-tray-deps

test:
	$(PYTHON) -m unittest discover -s tests -t . $(if $(FILTER),-k $(FILTER),)

check-tray-deps:
	@$(PYTHON) -c "import gi; gi.require_version('Gtk','3.0'); gi.require_version('AppIndicator3','0.1'); from gi.repository import Gtk, AppIndicator3" 2>/dev/null \
	  || { echo "Missing PyGObject/AppIndicator3. On Ubuntu: sudo apt install python3-gi gir1.2-gtk-3.0 gir1.2-appindicator3-0.1 gnome-shell-extension-appindicator"; exit 1; }

# Copy the package to a versioned-free fixed home, atomically (.new + mv),
# so a running tray never imports half a tree.
install-package:
	rm -rf "$(PKG_DEST).new"
	mkdir -p "$(PKG_DEST).new" "$(BIN_DIR)"
	cp -R ai_usage_meter "$(PKG_DEST).new/ai_usage_meter"
	find "$(PKG_DEST).new" -name __pycache__ -type d -prune -exec rm -rf {} +
	rm -rf "$(PKG_DEST)"
	mv "$(PKG_DEST).new" "$(PKG_DEST)"

install-hook: install-package
	printf '#!/usr/bin/env python3\nimport sys\nsys.path.insert(0, "%s")\nfrom ai_usage_meter.hook import main\nsys.exit(main())\n' "$(PKG_DEST)" > "$(HOOK_DEST).new"
	chmod 755 "$(HOOK_DEST).new"
	mv -f "$(HOOK_DEST).new" "$(HOOK_DEST)"
	@$(MAKE) --no-print-directory snippet

install-tray: check-tray-deps install-package
	printf '#!/usr/bin/env python3\nimport sys\nsys.path.insert(0, "%s")\nfrom ai_usage_meter.tray.app import main\nsys.exit(main())\n' "$(PKG_DEST)" > "$(TRAY_DEST).new"
	chmod 755 "$(TRAY_DEST).new"
	mv -f "$(TRAY_DEST).new" "$(TRAY_DEST)"
	mkdir -p "$(dir $(AUTOSTART))"
	sed 's|@TRAY@|$(TRAY_DEST)|' packaging/ai-usage-meter.desktop.in > "$(AUTOSTART)"
	-pkill -f "$(TRAY_PATTERN)" 2>/dev/null
	@for i in 1 2 3 4 5 6; do pgrep -f "$(TRAY_PATTERN)" >/dev/null 2>&1 || break; sleep 0.5; done
	setsid -f "$(TRAY_DEST)" >/dev/null 2>&1
	@echo "Tray launched; it also starts at login via $(AUTOSTART)."

install: install-hook install-tray

snippet:
	@echo ""
	@echo "Add this to ~/.claude/settings.json (the installer never edits it):"
	@echo ""
	@echo '  "statusLine": {'
	@echo '    "type": "command",'
	@echo '    "command": "$(HOOK_DEST)"'
	@echo '  }'
	@echo ""

uninstall:
	-pkill -f "$(TRAY_PATTERN)" 2>/dev/null
	rm -f "$(HOOK_DEST)" "$(TRAY_DEST)" "$(AUTOSTART)"
	rm -rf "$(PKG_DEST)" "$(PKG_DEST).new"
	@echo "Removed the package, both shims, the autostart entry and the tray. Remove the statusLine entry from ~/.claude/settings.json by hand."
	@echo "Snapshot left in place: $(SNAPSHOT)"

run:
	$(PYTHON) -m ai_usage_meter.tray.app
