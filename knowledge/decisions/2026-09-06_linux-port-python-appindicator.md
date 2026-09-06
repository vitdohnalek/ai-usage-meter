# Decision: Linux port in Python + PyGObject with an AppIndicator tray

## What was decided
The fork is Linux-only. The Swift tree is removed and replaced by a Python
package: `core/` (stdlib, one-to-one with MeterCore, tested with unittest),
`hook.py`, and a `tray/` shell built on GTK 3 + AppIndicator3
(StatusNotifierItem over DBus, served by GNOME's appindicator extension).
The tray polls the snapshot every 30 s, as the Mac app did.

## Why
The host is Ubuntu 24.04 / GNOME 46 on Wayland with no Swift toolchain.
Wayland has no X11 tray, so StatusNotifierItem is the only tray protocol.
Python 3.12, PyGObject and the AppIndicator3 typelib were already
installed, so the "zero third-party runtime, already on the machine"
rationale of the Mac decision points at Python here. The core logic is
~250 lines of platform-free rules pinned by ~70 tests, so the port is a
rehost of behaviour, not a redesign.

## Evidence
- Host probe 2026-09-06: GNOME 46, `ubuntu-appindicators` enabled,
  `gir1.2-appindicator3-0.1` importable with label support, no `swift`.
- Architect recon 2026-09-06: 69 of 72 upstream tests are contract
  behaviour independent of language. [ADR-upstream: host-native-swift-menubarextra]
- Design spec: `docs/superpowers/specs/2026-09-06-linux-port-design.md`.

## Alternatives considered
- GNOME Shell extension (gjs): no runtime at all, but not headless-testable
  and coupled to GNOME major versions; useless on WSL or other desktops.
- Node: needs a native tray library or Electron; slower hook start.
- Swift on Linux: no toolchain installed; SwiftUI does not exist on Linux,
  so the tray had to be rewritten anyway.
- GFileMonitor or hook-push over DBus instead of polling: the file must
  stay the sole source of truth for a future cross-boundary WSL reader, and
  the push adds a failure surface to the never-block hook. Polling stays.
- pyproject + pip / venv / zipapp: the tray needs the system-owned GI
  typelibs, which pip cannot install; Ubuntu's externally-managed marker
  makes pip machine-dependent. The Makefile copies files instead.

Supersedes: [host-native-swift-menubarextra](upstream/2026-09-05_host-native-swift-menubarextra.md),
the implementation half of [hook-is-a-swift-target](upstream/2026-09-05_hook-is-a-swift-target.md)
(the contract half stands), and [glyph-embedded-svg-string](upstream/2026-09-05_glyph-embedded-svg-string.md)
(icons are now SVG files in `ai_usage_meter/assets`).

**Last updated**: 2026-09-06
