# CLAUDE.md -- ai-usage-meter (Linux fork)

> Coding style, git workflow, testing, security, memory protocol, agent
> rules: see ~/.claude/CLAUDE.md. This file: durable orientation only,
> per ~/.claude/rules/agent-docs.md. Target 40-60 lines.

## Project goal

A personal Linux tray meter for AI-subscription usage that never handles a
credential (started as a port of DanielZucha/ai-usage-meter). It
renders Claude Code's 5-hour, 7-day, and per-model weekly (Fable)
rate-limit utilization on Ubuntu / GNOME; the hook alone runs anywhere with
Python 3, including WSL. Done means: the glyph and three numbers sit in the
tray, update after every Claude Code turn, count down to reset while idle,
and launch at login.

## Ultimate-goal alignment

Every change must keep three properties: no credential is read, stored, or
transmitted by any part of this repo; the snapshot stays provider-keyed and
byte-compatible with upstream so a second provider or a second reader is
additive; the hook never blocks or writes stderr.

## Architecture (pointers)

- Data path: Claude Code statusline hook -> snapshot JSON on disk -> tray
  app, polling every 30 s. Second writer: every 5 min the tray asks a
  throwaway `claude -p` for the `get_usage` control request and merges the
  per-model window (`core/usage_probe.py`); both writers share the flock.
  Sessions: the hook also writes `sessions/<id>.json` beside the snapshot
  (`core/sessions.py`, one writer per file, no lock); the tray lists the
  ones updated in the last 3 min and prunes after a day.
- Package: `ai_usage_meter/core` holds every rule and is stdlib only;
  `hook.py` and `tray/app.py` are thin shells; `tray/label.py` holds the
  tray's pure label rules. Test with `make test` (unittest, no packages),
  ship with `make install` (copies to `~/.local`, no pip, no venv).
- Language: Python 3 on the system interpreter; the tray needs the
  system PyGObject + AppIndicator3 typelibs, which pip cannot provide.
- Decisions: `knowledge/decisions/` (one page per non-obvious choice);
  `knowledge/decisions/upstream/` holds the inherited pages that no longer
  apply to this port, kept for the reasoning behind the shared contracts.
- Design spec for the port: `docs/superpowers/specs/2026-09-06-linux-port-design.md`.
- Install and wiring steps: `knowledge/entities/runbooks/install_and_wire.md`.

## Session rules

- Never read Claude Code credentials from code or tests. Never call
  `api/oauth/usage` yourself; the only sanctioned route to usage data is
  Claude Code's own statusline JSON or its `get_usage` control request.
  If a task seems to need more, stop and raise it.
- Never write to `~/.claude/settings.json` from an installer; print the
  snippet and let the user apply it.
- Fail quietly in the hook: it runs inside Claude Code's render loop and must
  never block, raise, or emit stderr noise. Keep it stdlib only.
- Upstream (`upstream` remote) is read-only; never push there.

## Resources

- Knowledge wiki: `knowledge/` (index auto-injected; contract in
  ~/.claude/rules/llm-wiki.md). Flavor: tooling.
- Live state: see the Now block in knowledge/index.md (auto-injected).
- Statusline contract: https://code.claude.com/docs/en/statusline
