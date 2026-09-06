# Decision: native Swift menu-bar app built with SwiftPM

> Inherited from the upstream project this port started from. It describes
> the original implementation, not this repository; kept for the reasoning
> behind the shared contracts. See [the port decision](../2026-09-06_linux-port-python-appindicator.md).

## What was decided
The menu-bar item is a native SwiftUI `MenuBarExtra` app built with
SwiftPM (no Xcode project), bundled by a small script, installed to
`~/Applications`, registering itself for launch at login with
`SMAppService`. Logic (snapshot parsing, formatting, reset and threshold
rules) lives in a library target tested with Swift Testing; the UI shell is
untested.

## Why
Zero third-party runtime matches the "code I own" motivation. Swift 6.2 is
already on the machine via Command Line Tools, which is enough for SwiftPM
but not for `xcodebuild`, so the build must stay Xcode-free.

## Evidence
- Toolchain and missing SwiftBar/xbar/Hammerspoon installs. [S1]
- Locally built apps need no notarization; `SMAppService.mainApp.register()`
  is the modern launch-at-login API. [S1]

## Alternatives considered
- SwiftBar plugin with a Python script: simplest possible, but adds a
  third-party host app. Kept as the fallback if Xcode-free bundling turns
  into a fight.
- Python rumps app: adds pyobjc and a LaunchAgent plist for no gain.
- Hammerspoon: needs Accessibility permission and a Lua runtime.

Related: [data-source decision](../2026-09-05_data-source-statusline-snapshot.md)

**Last updated**: 2026-09-05
