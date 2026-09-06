# Decision: the glyph ships as an SVG string constant, not a resource

> Inherited from the upstream project this port started from. It describes
> the original implementation, not this repository; kept for the reasoning
> behind the shared contracts. See [the port decision](../2026-09-06_linux-port-python-appindicator.md).

## What was decided
`assets/claude.svg` is embedded verbatim as the string constant
`ClaudeGlyph.svg` in MeterCore; a test keeps the constant byte-identical to
the asset. The app decodes that string once with `NSImage(data:)` and draws
it into the composite menu-bar label (`LabelImage`): a template image in
the normal state, an opaque-color image in the flipped state.

## Why
SwiftPM resources for an executable target resolve through `Bundle.module`,
which looks next to the binary or under `Bundle.main.bundleURL`; a
hand-assembled `.app` (no Xcode here) would have to reproduce that layout
exactly or crash at launch. A 1.7 KB string has no layout, no bundle, and
no runtime lookup. macOS 11 and later render SVG data in `NSImage`.

## Evidence
- Host decision: SwiftPM only, no Xcode. [host decision](2026-09-05_host-native-swift-menubarextra.md)
- Display decision: always filled, drawn into the label image (template
  normally, opaque when flipped). [display rules](../2026-09-05_app-refresh-and-display-rules.md)
- Measured 2026-09-05 via the AppKit ObjC bridge: `NSImage(data:)` on the
  asset returns an `_NSSVGImageRep`; filled and stroke-width-1 outline
  both rasterize at 32 and 128 px. The `1em` size attributes are harmless
  because the app sets the image size explicitly.

## Alternatives considered
- SwiftPM `resources: [.copy("claude.svg")]` plus `Bundle.module`: rejected
  for the bundle-layout coupling above.
- Parsing the path data into a SwiftUI `Shape`: rejected, the path uses
  arc commands and a parser is more code than the whole app.
- Two PNG sets at 1x and 2x: rejected, a raster loses the template
  crispness at fractional scales and doubles the asset count.

Related: [display rules](../2026-09-05_app-refresh-and-display-rules.md)

## History
- 2026-09-05: the outline variant (`outlineSVG`, `svg(filled:)`) was removed
  the same day when the display rules changed to an always-filled glyph;
  the embedded constant is now `ClaudeGlyph.svg`.

**Last updated**: 2026-09-05
