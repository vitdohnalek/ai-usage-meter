#!/usr/bin/env python3
"""One usage probe, then exit: asks Claude Code for the per-model weekly
window and merges it into the snapshot. The hook starts this detached where
no tray does the asking. Silent, and the exit code is always 0."""
import os
import sys

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main() -> int:
    try:
        from ai_usage_meter.core import usage_probe
        from ai_usage_meter.core.store import SnapshotStore
        usage_probe.refresh(SnapshotStore.default())
    except BaseException:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
