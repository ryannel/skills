---
name: dogfood-ui
description: Uses a web app in a real browser as a curious human would, maps its surfaces and user-question navigation graph, fixes dead ends, data mismatches, pattern gaps and visual flaws, and verifies every fix from screenshots. Use when asked to dogfood a UI, walk through an app's flows, audit navigation and polish, or find why a frontend feels confusing or incomplete. Not for backend-only tests, isolated unit tests, or designing a brand-new product from scratch.
---

# Dogfood UI

Use the running web application the way a fresh, curious user would, find everything that feels confusing, incomplete, clunky or broken, fix the underlying causes, and verify the result with your own eyes in a real browser.

Code reviews and DOM checks miss most of what makes a UI feel broken. An app can pass every test and still leave a user staring at a dead-end badge, hunting through three tabs for an item they already clicked, losing their place on Browser Back, or reading white text on a white card in Light Mode. The only way to catch those is to actually use the app and look at the rendered pixels.

## Think in a navigation graph, not a page tree

Web apps aren't trees where users only drill down from a home page. They are graphs of connected surfaces — full pages, sidebars, drawers, modals, popovers and command palettes — linked by the questions a human naturally asks when looking at what is on screen.

On every surface, look at each piece of information shown (every count, chip, row, badge, dependency, diagram node, edge or status) and actually try interacting with it — don't just visit URLs and take static screenshots. Ask what a user will want to know next:

- **Is this the whole truth, and does the UI explain surprising numbers?** Do counts, lists and labels match across cards, drawers and full views, or is one surface showing a stale stub, duplicates or leaked data? If a diagram shows a surprising count (like "2 calls" into a 73-endpoint API), check whether a user can click it to see *what* those items are and *why* the number is what it is.
- **Can I inspect this in one click — including truncated items and diagram edges?** If the UI names something or truncates it (an endpoint, table, `+4 more columns…`, an arrow with a count pill, a dependency, an error or a step), a user should be able to click it to peek the full details in place or jump straight to its definition, not hunt for it manually.
- **Can I zoom out to the bigger picture?** When inspecting a detail inside a narrow view (such as a table in a diff, or a step in a flow), can I reach the full database, service or system view cleanly?
- **Do I know what state I'm looking at, and does Back always return to the previous thing I looked at?** Context that changes meaning (such as proposed changes vs. current production, or a filtered subset) must be unmistakable. Test both the UI's Back button and native Browser Back after *every* transition — including in-page view switches (tabs, diagram vs. table views, foreign-key jumps, drawer selections). If Back skips over what you were just looking at, treat it as a navigation bug.

## Look for craft and proven patterns

While walking the app, judge each surface as a product designer as well as an engineer:

- **Borrow proven patterns over ad-hoc layouts.** When a view has an established modern convention (API references, schema and ER visualizers, triage queues, command palettes, diff views), follow the clarity and ergonomics of leading tools in that space rather than inventing a bespoke layout.
- **Inspect the actual rendered pixels in every theme.** Check Light, Dark and System modes (if supported), plus hover, scroll, zoom/pan and narrow widths where relevant. Watch for clipped text, broken padding, low-contrast or invisible text, outer-page scroll jumps, overlapping labels and awkward wrapping.
- **Fix causes in shared building blocks.** Prefer a single source of truth for data lookup and cohesive, reusable UI components over one-off patches on individual pages.

## Keep a living UX map

Record the app's ideal navigation graph in `docs/ux-map.md` (or update the UX map the project already has). Keep it concise and human-readable so future dogfood passes can diff against it and catch regressions.

```markdown
### System Map — Inspector Drawer
- **Shows:** summary, API groups, tables, dependencies, gaps
- **Questions → Destinations:**
  - "What routes exist?" → `Contracts` tab (all groups, searchable, inline schema peek)
  - "Show full spec for this route" → 1-click deep-link to `/entity/:id?tab=api&endpoint=:key`
  - "Take me back" → Browser Back restores map with entity selected
- **Verified:** Light & Dark, 2026-11-28
```

Focus the map on surfaces, the questions they raise, the expected transitions and return paths, and any open gaps you could not resolve yet.

## What finished means

A dogfood pass is done when:

1. Every surface and edge in the navigation graph has been exercised forward and backward in a real browser against a live build of the app.
2. You have visually inspected screenshots of each changed or audited surface in every supported theme — never claim a UI looks right from DOM text or code alone.
3. The app builds cleanly, existing tests pass, and the browser walk produces zero console or runtime errors.
4. `docs/ux-map.md` reflects the verified navigation graph and lists any remaining gaps that need a product decision.

When you report back, lead with what was broken and fixed, summarize the verified flows and any open questions, and keep what you confirmed in the browser separate from anything left untested.
