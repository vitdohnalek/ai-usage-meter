"""The per-model weekly window (the "Fable" row of ``/usage``) is not in the
statusline payload; Claude Code exposes it only through its SDK control
channel. So ask a throwaway ``claude -p`` process for ``get_usage``: Claude
Code talks to the usage endpoint with its own credentials, and this module
never sees them. Runs from the tray, never from the hook (about 1.3 s)."""
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping, Optional

from .clamp import clamped_int
from .snapshot import ModelWindow, ProviderUsage, parse_date

SOURCE = "usage"
REQUEST_ID = "ai-usage-meter"
BINARY_ENV = "AI_USAGE_METER_CLAUDE"
MODEL_ENV = "AI_USAGE_METER_MODEL"
TIMEOUT_SECONDS = 30
# ``--setting-sources project`` with an empty cwd loads no hooks or MCP
# servers; ``--no-session-persistence`` leaves no transcript behind.
ARGUMENTS = [
    "-p", "--input-format", "stream-json", "--output-format", "stream-json", "--verbose",
    "--setting-sources", "project", "--no-session-persistence", "--strict-mcp-config",
]


def request() -> bytes:
    message = {"type": "control_request", "request_id": REQUEST_ID,
               "request": {"subtype": "get_usage", "skip_behaviors": True}}
    return (json.dumps(message) + "\n").encode("utf-8")


def find_claude(environ: Mapping[str, str] = os.environ) -> Optional[str]:
    explicit = environ.get(BINARY_ENV)
    if explicit:
        return explicit
    found = shutil.which("claude", path=environ.get("PATH"))
    if found:
        return found
    fallback = Path.home() / ".local" / "bin" / "claude"
    return str(fallback) if os.access(fallback, os.X_OK) else None


def _pick(scoped, model: Optional[str]) -> Optional[ModelWindow]:
    if not isinstance(scoped, list):
        return None
    for entry in scoped:
        if not isinstance(entry, dict):
            continue
        name = entry.get("display_name")
        if not isinstance(name, str) or (model and name != model):
            continue
        used = clamped_int(entry.get("utilization"))
        try:
            resets_at = parse_date(entry.get("resets_at"))
        except ValueError:
            continue
        if used is not None:
            return ModelWindow(used, resets_at, name)
    return None


def parse(output: bytes, model: Optional[str] = None) -> Optional[ModelWindow]:
    """First successful ``control_response`` wins; ``model`` narrows the pick
    to one display name, otherwise the first bucket is taken."""
    for raw_line in output.splitlines():
        try:
            message = json.loads(raw_line)
        except ValueError:
            continue
        if not isinstance(message, dict) or message.get("type") != "control_response":
            continue
        response = message.get("response")
        if not isinstance(response, dict) or response.get("subtype") != "success":
            continue
        body = response.get("response")
        limits = body.get("rate_limits") if isinstance(body, dict) else None
        return _pick(limits.get("model_scoped") if isinstance(limits, dict) else None, model)
    return None


def capture(cwd, claude: Optional[str] = None, model: Optional[str] = None,
            timeout: float = TIMEOUT_SECONDS, now: Optional[datetime] = None,
            environ: Mapping[str, str] = os.environ) -> Optional[ProviderUsage]:
    """Return a provider document carrying only the model window, or None."""
    binary = claude or find_claude(environ)
    if binary is None:
        return None
    env = {key: value for key, value in environ.items() if key != "CLAUDECODE"}
    try:
        os.makedirs(cwd, exist_ok=True)
        completed = subprocess.run([binary, *ARGUMENTS], input=request(), capture_output=True,
                                   cwd=str(cwd), env=env, timeout=timeout)
    except (OSError, subprocess.SubprocessError):
        return None
    window = parse(completed.stdout, model or environ.get(MODEL_ENV) or None)
    if window is None:
        return None
    return ProviderUsage(None, None, now or datetime.now(timezone.utc), SOURCE, seven_day_model=window)
