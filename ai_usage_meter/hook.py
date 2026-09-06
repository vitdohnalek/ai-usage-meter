#!/usr/bin/env python3
"""Claude Code statusline command. Reads the payload from stdin, merges it
into the snapshot, prints one line. Any failure degrades to a fallback line;
nothing is written to stderr and the exit code is always 0."""
import os
import sys

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main() -> int:
    output = "Claude · ⛁ --"
    try:
        from ai_usage_meter.core.hook_runner import run
        from ai_usage_meter.core.store import SnapshotStore
        output = run(sys.stdin.buffer.read(), SnapshotStore.default())
    except BaseException:
        pass
    try:
        sys.stdout.buffer.write(output.encode("utf-8") + b"\n")
        sys.stdout.buffer.flush()
    except BaseException:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
