"""The on-disk document, byte-compatible with upstream's Swift encoder."""
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional

CURRENT_SCHEMA_VERSION = 1
CLAUDE_PROVIDER_ID = "claude"
_ISO = "%Y-%m-%dT%H:%M:%SZ"


@dataclass
class UsageWindow:
    """One rate-limit window as reported by a provider."""
    used_percentage: int
    resets_at: datetime


@dataclass
class ModelWindow(UsageWindow):
    """A per-model weekly window; ``model`` is the server-supplied label."""
    model: str = ""


@dataclass
class ProviderUsage:
    """Everything the snapshot knows about one provider. ``seven_day_model``
    is the per-model weekly bucket (the "Fable" row of ``/usage``); it is
    additive, so documents without it still decode."""
    five_hour: Optional[UsageWindow]
    seven_day: Optional[UsageWindow]
    captured_at: datetime
    source: str
    seven_day_model: Optional[ModelWindow] = None


@dataclass
class Snapshot:
    """Provider-keyed so a second provider is an added key."""
    schema_version: int
    providers: Dict[str, ProviderUsage] = field(default_factory=dict)

    @property
    def claude(self) -> Optional[ProviderUsage]:
        return self.providers.get(CLAUDE_PROVIDER_ID)

    @claude.setter
    def claude(self, usage: Optional[ProviderUsage]) -> None:
        if usage is None:
            self.providers.pop(CLAUDE_PROVIDER_ID, None)
        else:
            self.providers[CLAUDE_PROVIDER_ID] = usage


def format_date(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime(_ISO)


def parse_date(text) -> datetime:
    if not isinstance(text, str):
        raise ValueError(f"date is not a string: {text!r}")
    try:
        return datetime.strptime(text, _ISO).replace(tzinfo=timezone.utc)
    except ValueError:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)


def _window_to_json(window: UsageWindow) -> dict:
    return {"used_percentage": window.used_percentage, "resets_at": format_date(window.resets_at)}


def _window_from_json(raw) -> UsageWindow:
    if not isinstance(raw, dict):
        raise ValueError("window is not an object")
    used = raw["used_percentage"]
    if isinstance(used, bool) or not isinstance(used, int):
        raise ValueError("used_percentage is not an integer")
    return UsageWindow(used_percentage=used, resets_at=parse_date(raw["resets_at"]))


def _model_window_to_json(window: ModelWindow) -> dict:
    return {**_window_to_json(window), "model": window.model}


def _model_window_from_json(raw) -> ModelWindow:
    window = _window_from_json(raw)
    model = raw.get("model", "")
    if not isinstance(model, str):
        raise ValueError("model is not a string")
    return ModelWindow(window.used_percentage, window.resets_at, model)


def _provider_to_json(usage: ProviderUsage) -> dict:
    document = {"captured_at": format_date(usage.captured_at), "source": usage.source}
    if usage.five_hour is not None:
        document["five_hour"] = _window_to_json(usage.five_hour)
    if usage.seven_day is not None:
        document["seven_day"] = _window_to_json(usage.seven_day)
    if usage.seven_day_model is not None:
        document["seven_day_model"] = _model_window_to_json(usage.seven_day_model)
    return document


def _provider_from_json(raw) -> ProviderUsage:
    if not isinstance(raw, dict):
        raise ValueError("provider is not an object")
    source = raw["source"]
    if not isinstance(source, str):
        raise ValueError("source is not a string")
    return ProviderUsage(
        five_hour=_window_from_json(raw["five_hour"]) if "five_hour" in raw else None,
        seven_day=_window_from_json(raw["seven_day"]) if "seven_day" in raw else None,
        captured_at=parse_date(raw["captured_at"]),
        source=source,
        seven_day_model=(_model_window_from_json(raw["seven_day_model"])
                         if "seven_day_model" in raw else None),
    )


def encode(snapshot: Snapshot) -> bytes:
    """Pretty-printed, sorted keys, ISO-8601 dates, like the Swift encoder."""
    document = {
        "schema_version": snapshot.schema_version,
        "providers": {key: _provider_to_json(usage) for key, usage in snapshot.providers.items()},
    }
    return json.dumps(document, indent=2, sort_keys=True, ensure_ascii=False).encode("utf-8")


def decode(data: bytes) -> Snapshot:
    """Raise ``ValueError`` on anything that is not a snapshot document."""
    try:
        document = json.loads(data)
        if not isinstance(document, dict):
            raise ValueError("snapshot is not an object")
        version = document["schema_version"]
        providers = document["providers"]
        if isinstance(version, bool) or not isinstance(version, int) or not isinstance(providers, dict):
            raise ValueError("bad schema_version or providers")
        return Snapshot(
            schema_version=version,
            providers={key: _provider_from_json(raw) for key, raw in providers.items()},
        )
    except (KeyError, TypeError, ValueError, OverflowError, UnicodeDecodeError) as error:
        raise ValueError(f"not a snapshot: {error}") from error
