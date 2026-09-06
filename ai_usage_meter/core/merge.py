"""Every running Claude Code session invokes the hook with its own, possibly
stale, view of the rate limits. Within one window (same ``resets_at``) the
used percentage only rises, so the maximum is the truth; a later
``resets_at`` is a new window and replaces the old one outright."""
from dataclasses import replace
from typing import Optional

from .snapshot import CURRENT_SCHEMA_VERSION, ProviderUsage, Snapshot, UsageWindow


def merge_window(existing: Optional[UsageWindow], incoming: Optional[UsageWindow]) -> Optional[UsageWindow]:
    if incoming is None:
        return existing
    if existing is None:
        return incoming
    if incoming.resets_at > existing.resets_at:
        return incoming
    if incoming.resets_at < existing.resets_at:
        return existing
    return incoming if incoming.used_percentage >= existing.used_percentage else existing


def merge_provider(existing: Optional[ProviderUsage], incoming: ProviderUsage) -> ProviderUsage:
    return ProviderUsage(
        five_hour=merge_window(existing.five_hour if existing else None, incoming.five_hour),
        seven_day=merge_window(existing.seven_day if existing else None, incoming.seven_day),
        captured_at=incoming.captured_at,
        source=incoming.source,
        seven_day_model=merge_window(existing.seven_day_model if existing else None,
                                     incoming.seven_day_model),
    )


def merge_snapshot(snapshot: Optional[Snapshot], provider_id: str, incoming: ProviderUsage) -> Snapshot:
    """Return a new document; the input is never mutated."""
    providers = dict(snapshot.providers) if snapshot else {}
    providers[provider_id] = merge_provider(providers.get(provider_id), incoming)
    return Snapshot(schema_version=CURRENT_SCHEMA_VERSION, providers=providers)
