#!/usr/bin/env python3
"""Claude Code statusline command. Reads the payload from stdin, merges it
into the snapshot, prints one line. Any failure degrades to a fallback line;
nothing is written to stderr and the exit code is always 0. When no usage
probe has run lately it starts one detached and does not wait for it."""
import os
import sys

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

NO_PROBE_ENV = "AI_USAGE_METER_NO_PROBE"
PROBE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "probe.py")


def spawn_probe() -> None:
    """Start ``probe.py`` in its own session with no stdio, so it outlives
    this process and Claude Code never waits on its pipes."""
    import subprocess
    import warnings
    # Dropping a Popen whose child still runs raises a ResourceWarning,
    # which dev mode would print to stderr.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ResourceWarning)
        subprocess.Popen([sys.executable, PROBE], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, start_new_session=True, close_fds=True)


def main() -> int:
    output = "Claude · ⛁ --"
    try:
        from ai_usage_meter.core.hook_runner import run
        from ai_usage_meter.core.store import SnapshotStore
        output = run(sys.stdin.buffer.read(), SnapshotStore.default(), color="NO_COLOR" not in os.environ,
                     request_probe=None if os.environ.get(NO_PROBE_ENV) else spawn_probe)
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
