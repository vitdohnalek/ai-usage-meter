# CLAUDE.md -- ai-usage-meter (Linux fork)

> Coding style, git workflow, testing, security, memory protocol, agent
> rules: see ~/.claude/CLAUDE.md. This file: durable orientation only,
> per ~/.claude/rules/agent-docs.md. Target 40-60 lines.

## Project goal

A personal Linux tray meter for AI-subscription usage, forked from
DanielZucha/ai-usage-meter (macOS), that never handles a credential. It
renders Claude Code's 5-hour and 7-day rate-limit utilization on Ubuntu /
GNOME; the hook alone runs anywhere with Python 3, including WSL. Done
means: the glyph and two numbers sit in the tray, update after every Claude
Code turn, count down to reset while idle, and launch at login.

## Ultimate-goal alignment

Every change must keep three properties: no credential is read, stored, or
transmitted by any part of this repo; the snapshot stays provider-keyed and
byte-compatible with upstream so a second provider or a second reader is
additive; the hook never blocks or writes stderr.

## Architecture (pointers)

- Data path: Claude Code statusline hook -> snapshot JSON on disk -> tray
  app. The hook is the only writer; the tray is read-only, polling every
  30 s.
- Package: `ai_usage_meter/core` holds every rule and is stdlib only;
  `hook.py` and `tray/app.py` are thin shells; `tray/label.py` holds the
  tray's pure label rules. Test with `make test` (unittest, no packages),
  ship with `make install` (copies to `~/.local`, no pip, no venv).
- Language: Python 3 on the system interpreter; the tray needs the
  system PyGObject + AppIndicator3 typelibs, which pip cannot provide.
- Decisions: `knowledge/decisions/` (one page per non-obvious choice; the
  2026-09-06 pages supersede the macOS host decisions).
- Design spec for the port: `docs/superpowers/specs/2026-09-06-linux-port-design.md`.
- Install and wiring steps: `knowledge/entities/runbooks/install_and_wire.md`.

## Session rules

- Never read Claude Code credentials from code or tests. Never call
  `api/oauth/usage`. If a task seems to need either, stop and raise it.
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
