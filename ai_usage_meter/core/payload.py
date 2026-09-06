"""The subset of Claude Code's statusline stdin JSON this project reads.
Every field is optional and every top-level key decodes independently, so
one field's type change upstream cannot fail the whole payload."""
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from .clamp import clamped_int
from .snapshot import ProviderUsage, UsageWindow

SOURCE = "statusline"


def _number(value) -> Optional[float]:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _string(value) -> Optional[str]:
    return value if isinstance(value, str) else None


def _boolean(value) -> Optional[bool]:
    return value if isinstance(value, bool) else None


@dataclass
class RateWindow:
    used_percentage: Optional[float]
    resets_at: Optional[float]  # Unix epoch seconds, as Claude Code sends it

    @classmethod
    def from_json(cls, raw) -> Optional["RateWindow"]:
        if not isinstance(raw, dict):
            return None
        return cls(_number(raw.get("used_percentage")), _number(raw.get("resets_at")))

    def to_window(self) -> Optional[UsageWindow]:
        if self.used_percentage is None or self.resets_at is None:
            return None
        percentage = clamped_int(self.used_percentage)
        if percentage is None:
            return None
        try:
            reset = datetime.fromtimestamp(self.resets_at, tz=timezone.utc)
        except (OverflowError, ValueError, OSError):
            return None
        return UsageWindow(percentage, reset)


@dataclass
class RateLimits:
    five_hour: Optional[RateWindow]
    seven_day: Optional[RateWindow]

    @classmethod
    def from_json(cls, raw) -> Optional["RateLimits"]:
        if not isinstance(raw, dict):
            return None
        return cls(RateWindow.from_json(raw.get("five_hour")), RateWindow.from_json(raw.get("seven_day")))


@dataclass
class PromptCache:
    """``prompt_cache`` (2.1.251+): whether the cached prefix is still live
    and when it goes cold, in epoch seconds like ``resets_at``."""
    warm: Optional[bool]
    observed: Optional[bool]
    expires_at: Optional[float]

    @classmethod
    def from_json(cls, raw) -> Optional["PromptCache"]:
        if not isinstance(raw, dict):
            return None
        return cls(_boolean(raw.get("warm")), _boolean(raw.get("caching_observed")),
                   _number(raw.get("expires_at")))


@dataclass
class StatuslinePayload:
    model_display_name: Optional[str]
    effort_level: Optional[str]
    context_used_percentage: Optional[float]
    rate_limits: Optional[RateLimits]
    context_tokens: Optional[float] = None       # total_input_tokens: what is in the window now
    context_window_size: Optional[float] = None  # context_window_size for the current model
    exceeds_200k: Optional[bool] = None          # exceeds_200k_tokens: long-context pricing applies
    prompt_cache: Optional[PromptCache] = None
    session_id: Optional[str] = None
    session_name: Optional[str] = None           # --name / /rename, else the AI-generated name, else absent
    project_dir: Optional[str] = None            # workspace.project_dir, falling back to cwd

    @classmethod
    def decode(cls, data: bytes) -> "StatuslinePayload":
        """Raise ``ValueError`` unless ``data`` is a JSON object."""
        try:
            document = json.loads(data)
        except (ValueError, UnicodeDecodeError) as error:
            raise ValueError(str(error)) from error
        if not isinstance(document, dict):
            raise ValueError("payload is not an object")
        model = document.get("model")
        effort = document.get("effort")
        context = document.get("context_window")
        workspace = document.get("workspace")
        project_dir = _string(workspace.get("project_dir")) if isinstance(workspace, dict) else None
        return cls(
            model_display_name=_string(model.get("display_name")) if isinstance(model, dict) else None,
            effort_level=_string(effort.get("level")) if isinstance(effort, dict) else None,
            context_used_percentage=_number(context.get("used_percentage")) if isinstance(context, dict) else None,
            rate_limits=RateLimits.from_json(document.get("rate_limits")),
            context_tokens=_number(context.get("total_input_tokens")) if isinstance(context, dict) else None,
            context_window_size=_number(context.get("context_window_size")) if isinstance(context, dict) else None,
            exceeds_200k=_boolean(document.get("exceeds_200k_tokens")),
            prompt_cache=PromptCache.from_json(document.get("prompt_cache")),
            session_id=_string(document.get("session_id")) or None,
            session_name=_string(document.get("session_name")),
            project_dir=project_dir or _string(document.get("cwd")),
        )

    def provider_usage(self, captured_at: datetime) -> Optional[ProviderUsage]:
        """``None`` when no usable window arrived, so the stored snapshot and
        its ``captured_at`` stand rather than read as freshly updated."""
        if self.rate_limits is None:
            return None
        five = self.rate_limits.five_hour.to_window() if self.rate_limits.five_hour else None
        seven = self.rate_limits.seven_day.to_window() if self.rate_limits.seven_day else None
        if five is None and seven is None:
            return None
        return ProviderUsage(five, seven, captured_at, SOURCE)
