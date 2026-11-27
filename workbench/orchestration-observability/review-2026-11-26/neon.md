# Design Review — Orchestrate Observability Dashboard

Reviewed all 13 desktop/phone page captures and 25 panel crops in `review-2026-11-26/before/`, alongside [index.html](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html), [model.json](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/model.json), [history.json](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/history.json), [DIRECTION.md](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/DIRECTION.md), [SCREENS.md](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/SCREENS.md), and [ACTIVITIES.md](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/ACTIVITIES.md). *(Note: the live localhost server was not reachable from this sandboxed environment, so interactive states—hover, focus, popovers, disclosures, and light mode—were verified from code and data rather than a live browser; also note that `panels/plan--modules.png` appears to have captured the lower half of the Program board rather than the Modules table, so Modules was reviewed from code.)*

---

## 1. The five changes I'd make first

1. **Fix the broken item-statement truncation on the Work package page.** Inline `<code>` elements break out of `.statement-toggle`'s single-line truncation and slice off leading characters (`IPELINE_CACHE`, `reate_pipeline_cache`, `patch]`), making acceptance criteria look corrupted.
2. **Fix the snapshot clock anchor (`snapshot_at` vs `built_at`) and `Since you last looked` cutoff.** Because `snapshot` uses a 2-day-old `snapshot_at` while events are from Nov 26, nearly every relative age collapses to `<1m`, "Done today" is inflated from **26** to **61**, and `Since you last looked` defaults to `Date.now()` (after the snapshot) so it renders permanently empty.
3. **Mark overdue milestones consistently and fix the miswired `Ready for Review` tile on Now.** `Now` and the `Milestone` page still show past dates (`24 Nov, 20:32`) as calm future forecasts ("Expected around…") while `Plan` correctly calls them overdue; meanwhile clicking `Ready for Review` on `Now` jumps to the empty `Since you last looked` panel instead of `#wait-review`.
4. **Make the Program board usable on phones and add a seam to its sticky `Module` column.** Hardcoding `200px` inline for the sticky `Module` column eats 55% of a 390 px phone screen (leaving no room to read a single column header or card), and on desktop scrolled columns clip mid-letter directly into the module column with no border or shadow.
5. **Restore interactive link affordances, right-align table numbers, and fix the `Now` header/tiles on phone.** Standalone links (`Design · Plan · Log`, `On the … chain`, Evidence file paths) look like static text; CSS defines `td.num` but `table()` never applies it so every metric table is left-aligned; and on phone `.state-pill` splits `Paused` into a broken two-column layout while the `Next milestone` tile breaks the stat-row baseline.

---

## 2. Findings (most important first)

### 1. Item statements with inline `<code>` garble and lose leading characters when collapsed
- **Page & panel:** Work package → `Items`
- **Screenshot:** `panels/workpackage--items.png`, `pages/workpackage-desktop.png`, `pages/workpackage-phone.png`
- **Verified in:** Screenshots + code ([index.html](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L52), [L455-L457](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L455-L457), [L1464](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L1464)) + `model.json`
- **Problem:** In `WP12.1`, `WP12.3`, and `WP12.5`, collapsed statements wrap onto multiple ragged lines and chop off the first characters of inline code tokens (`IPELINE_CACHE`, `reate_pipeline_cache`, `allback off`, `patch]`, `rc/pipeline_cache.rs`).
- **Why it matters:** Work package items are the proof contract; garbled text destroys confidence on the page where every question ends up.
- **Root cause & fix:** [index.html:52](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L52) sets `code, pre { white-space: pre-wrap; overflow-wrap: anywhere; }`, which overrides `white-space: nowrap` on `.statement-toggle:not([open]) summary span` ([L457](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L457)). Plain text refuses to wrap and ellipses, then each `<code>` breaks onto a new line inside the `overflow: hidden` inline-block box.
  - Scope `white-space: pre-wrap` to `pre, pre code` only (let inline `code` inherit `white-space`).
  - Replace the fragile `display: inline-block; white-space: nowrap` hack with line-clamping on a flex child:
    ```css
    .statement-toggle summary { display: flex; align-items: baseline; gap: 0; }
    .statement-toggle:not([open]) summary span {
      display: -webkit-box;
      -webkit-box-orient: vertical;
      -webkit-line-clamp: 1;
      overflow: hidden;
      flex: 1;
      min-width: 0;
    }
    ```

---

### 2. Stale clock anchor (`snapshot_at`) collapses ages to `<1m` and inflates "Done today" from 26 to 61
- **Page & panel:** `Now` (state pill, `Done today` tile, `Not moving`), `Delivery` (`Board` cards)
- **Screenshot:** `pages/now-desktop.png`, `pages/now-phone.png`, `panels/now--not-moving.png`, `panels/delivery--board.png`, `pages/delivery-phone.png`
- **Verified in:** Screenshots + code ([index.html:591](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L591), [L734-L739](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L734-L739), [L1100](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L1100), [L1927](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L1927)) + `model.json`
- **Problem:** Nearly every recent timestamp renders as `<1m` (`last merge <1m`, `CLOUDS:WP9 <1m`, `GAME-UI:WP4 <1m`, and all 61 cards in `Done · 24h`), and `Done today` / `Done · 24h` counts **61** work packages instead of **26**.
- **Why it matters:** "Is it moving?" is `Now`'s core question. Seeing `Paused · 0/10 builders · last merge <1m` and 61 items all completed `<1m` ago makes the data look broken, and `GATE-TIME:WP5` shows `11h 20m` instead of `2d 2h` waiting on the owner.
- **Root cause & fix:** In `model.json`, `snapshot_at` is `2026-11-24T15:53:33Z`, while `built_at` is `2026-11-26T07:03:21Z` and `recent_events[0].at` is `2026-11-26T07:01:30Z` (what the top-right badge displays as `Snapshot 26 Nov, 08:01`). Line [1927](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L1927) sets `snapshot = Date.parse(model.project.snapshot_at || model.project.built_at)`, so Nov 26 timestamps subtract to negative numbers clamped to `0` (`<1m`) by `Math.max(0, ...)` ([L591](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L591)), and `snapshot - day` reaches back 63 hours to Nov 23.
  - Anchor `snapshot` to the newest project clock:
    ```js
    snapshot = Math.max(
      Date.parse(model.project.built_at) || 0,
      Date.parse(model.project.snapshot_at) || 0,
      Date.parse(model.now.recent_events[0]?.at) || 0
    );
    ```
  - Also use the same `snapshot` in `connectionStatus()` ([L1645](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L1645)) so the badge time and all relative ages share one clock.

---

### 3. `Since you last looked` is permanently empty on snapshots, and the `Ready for Review` tile jumps to it
- **Page & panel:** `Now` → stat tiles & `Since you last looked`
- **Screenshot:** `pages/now-desktop.png`, `pages/now-phone.png`, `panels/now--since-you-last-looked.png`
- **Verified in:** Screenshots + code ([index.html:745](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L745), [L1928-L1934](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L1928-L1934))
- **Problem:**
  1. `Since you last looked` says `since 26 Nov, 23:08` — **15 hours after** the `26 Nov, 08:01` snapshot — and therefore always shows `"Nothing changed since you last looked."`
  2. The `Ready for Review` stat tile (`2 waiting on a reviewer`, [L745](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L745)) links to `#recent-events` (`Since you last looked`) instead of `#wait-review` (under `Not moving`).
- **Why it matters:** When the owner opens a snapshot (or refreshes a live page), their primary "what changed?" feed goes blank, and clicking the `Ready for Review` count drops them onto an unrelated empty box instead of the two work packages awaiting review.
- **Fix:**
  - In [L1928-L1933](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L1928-L1933), anchor `seen` to `snapshot` when viewing a static snapshot (`!model.project.live`), e.g. `seen = snapshot - day`, or clamp `seen = Math.min(previous, snapshot - 3600000)` when `previous >= snapshot`. Even on a live page, avoid advancing `localStorage` on every instant reload so a quick refresh doesn't wipe the feed.
  - Change [L745](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L745) from `tile("#recent-events","Ready for Review",...)` to `tile("#wait-review","Ready for Review",...)` (falling back to `#/delivery` when none are waiting).

---

### 4. Program board is unusable on phones (`200px` inline sticky column) and clips content abruptly on desktop
- **Page & panel:** `Plan` → `Program board`
- **Screenshot:** `pages/plan-phone.png`, `pages/plan-desktop.png`, `panels/plan--program-board.png`
- **Verified in:** Screenshots + code ([index.html:302-315](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L302-L315), [L923](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L923))
- **Problem:**
  - On phone (`plan-phone.png`), [L923](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L923) sets `style="grid-template-columns:200px ..."` inline. On a 390 px viewport (~362 px inner panel width), the sticky `Module` column consumes **55% of the width**, leaving ~160 px for milestone columns—cutting headers down to `here` / `App` and cards down to a bare `✓`.
  - On desktop (`plan--program-board.png`), `.pb-module` and `.pb-corner` have no right border or shadow, so scrolled columns slice off mid-word (`tent-addressed loop`, `very pixel of the valley`) directly against the module labels with no visual edge.
- **Why it matters:** On mobile the board is effectively broken; on desktop the hard clipping reads like a layout bug rather than a scrolled table.
- **Fix:**
  - Replace the hardcoded `200px` with a CSS custom property (`grid-template-columns: var(--pb-mod, 200px) ...`) and override `--pb-mod: 112px;` (or unstick `.pb-module { position: static; }` and show a compact module header) inside `@media (max-width: 760px)`.
  - Add a clean seam to the sticky column:
    ```css
    .pb-corner, .pb-module {
      border-right: 1px solid var(--line-strong);
      box-shadow: 6px 0 12px -8px #00000080;
    }
    ```

---

### 5. Overdue milestones display as calm future forecasts on `Now` and the `Milestone` page
- **Page & panel:** `Now` → `Milestones`; `Milestone` page → header
- **Screenshot:** `panels/now--milestones.png`, `pages/now-desktop.png`, `pages/now-phone.png`, `pages/milestone-desktop.png`, `pages/milestone-phone.png` (contrast with `panels/plan--goal.png`)
- **Verified in:** Screenshots + code ([index.html:683](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L683), [L1035](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L1035), [L1345](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L1345)) + `model.json`
- **Problem:** `Plan` (`goalHeader()`, [L1035](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L1035)) checks `Date.parse(next.expected_at) < Date.parse(project.built_at)` and states *"was expected around 24 Nov, 20:32 and is overdue"*. Both `Now` ([L683](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L683)) and `Milestone` ([L1345](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L1345)) omit that check and print `Expected around 24 Nov, 20:32` and `Expected around 25 Nov, 00:11` in neutral pills—even though the snapshot is `26 Nov, 08:01`.
- **Why it matters:** The owner checking `Now` on a phone misses that both remaining milestones are already 1–2 days past forecast, and two tabs of the same dashboard contradict each other.
- **Fix:** Share one helper `forecastInfo(m)` across `Now`, `Plan`, and `Milestone` that checks `Date.parse(m.expected_at) < snapshot` and outputs `{ text: "Overdue · expected " + dateText(m.expected_at), overdue: true }`, styled with `.forecast-pill.held` (or `.forecast-pill.overdue` using `--amber` / `--amber-bg`).

---

### 6. Standalone links look identical to plain body text and collide when adjacent
- **Page & panel:** `Work package` (header chain links, `Evidence`), `Module` (header doc links, `Full log`), `Milestone` (`Plan map`), `Now` (`Needs you` work package title)
- **Screenshot:** `pages/workpackage-desktop.png`, `panels/workpackage--evidence.png`, `pages/module-desktop.png`, `panels/module--recent-log-entries.png`, `pages/milestone-desktop.png`, `panels/now--needs-you.png`
- **Verified in:** Screenshots + code ([index.html:38-39](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L38-L39), [L1353](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L1353), [L1388](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L1388), [L1396](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L1396), [L1485-L1486](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L1485-L1486), [L1491](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L1491))
- **Problem:** Global `a { color: var(--link); text-decoration: none; }` with `--link === --ink` strips every visual cue from links outside `.doc`/`.prose`. On `workpackage-desktop.png`, `On the Apple reconstruction chain On the V1 showcase chain` run together with no separator and look like static metadata. In `Evidence` (`workpackage--evidence.png`), nothing signals that `WP12.1` jumps to the item or `qualification/D12.1.log` opens a file dialog. On `module-desktop.png`, `Design · Plan · Log` and `Full log` look unclickable.
- **Why it matters:** A collaborator arriving cold cannot tell what is interactive without sweeping the mouse across every word—and on a phone there is no hover at all.
- **Fix:**
  - Keep list rows un-underlined per `DIRECTION.md`, but style standalone navigation links explicitly with a `.link-pill` or `.inline-link` class (subtle border/background pill or muted underline + `→`), e.g.:
    ```css
    .action-link { display: inline-flex; align-items: center; gap: 5px; padding: 3px 10px; border-radius: 7px; border: 1px solid var(--line); background: var(--panel); font-size: .75rem; color: var(--ink); }
    .action-link:hover { background: var(--subtle); border-color: var(--line-strong); }
    ```
  - Apply `.action-link` to `Design`, `Plan`, `Log` ([L1388](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L1388)), `Full log` ([L1396](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L1396)), `Plan map` ([L1353](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L1353)), and each `On the … chain` link ([L1491](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L1491)).
  - In `Evidence` ([L1485-L1486](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L1485-L1486)), style `.path` with an underline (`text-decoration: underline; text-decoration-color: var(--line-strong); text-underline-offset: 3px;`) and give `.path-list .row` the same hover tint as `.list-row`.

---

### 7. `Now` header breaks on phones (`.state-pill` two-column glitch) and the `Next milestone` tile disrupts the stat row
- **Page & panel:** `Now` → header `.state-pill` & `.tiles`
- **Screenshot:** `pages/now-phone.png`, `pages/now-desktop.png`
- **Verified in:** Screenshots + code ([index.html:81](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L81), [L105-L110](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L105-L110), [L506-L510](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L506-L510), [L735-L747](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L735-L747))
- **Problem:**
  1. On `now-phone.png`, `.state-pill` is `display: inline-flex; align-items: center; gap: 8px`, containing `<strong>Paused</strong>` plus a single long text node `" · 0/10 builders · 0 reviews · last merge <1m · supervisor stopped"`. Flex splits those into two columns—`Paused` floats vertically centered on the left while a wrapped line starting with a dangling `·` sits beside it.
  2. In `.tiles` (`now-desktop.png` and `now-phone.png`), four tiles show crisp numbers (`1`, `11`, `2`, `61`), while `Next milestone` stuffs `Apple reconstruction` into `.tile-value` at `1.75rem`, wrapping onto two oversized lines and misaligning the sub-labels across all five tiles.
- **Why it matters:** Both sit above the fold on the owner's primary mobile entry screen—the first thing seen at a glance looks visually uneven.
- **Fix:**
  - Change `.state-pill` from `display: inline-flex` to `display: block; line-height: 1.45;` (or wrap each item in its own `<span>` with `flex-wrap: wrap` and CSS middot separators) so `Paused` flows naturally inline on phones.
  - Keep `.tiles` strictly "one strong number per idea": put **`2 left`** (or **`28/30`**) in `.tile-value` and **`Apple reconstruction`** in `.tile-note`, and add `grid-template-rows: auto 1fr auto` on `.tile` so all five sub-labels share a baseline.

---

### 8. `Plan` → Goal milestone stepper has colliding labels, misleading green connectors, and hides the active milestone on phones
- **Page & panel:** `Plan` → `Goal` (`ol.stepper.goal-ladder`)
- **Screenshot:** `panels/plan--goal.png`, `pages/plan-desktop.png`, `pages/plan-phone.png`
- **Verified in:** Screenshots + code ([index.html:254](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L254), [L262-L272](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L262-L272), [L1038-L1042](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L1038-L1042))
- **Problem:**
  1. `Apple reconstruction` touches `Content-addressed` with zero gap (`Apple reconstructionContent-addressed`, `plan--goal.png`) because `.stepper.goal-ladder li { flex: 1 0 84px }` is narrower than the word `reconstruction`.
  2. Milestones appear in plan order (open `Apple reconstruction` before closed `Content-addressed loop` and `Creator experience`), conflicting with the Program board directly beneath it (which uses closure order). Worse, `.stepper li.closed::before { background: var(--green) }` draws a green line *out of* `Creator experience` into the unclosed `V1 showcase`.
  3. On `plan-phone.png`, the scrollable stepper opens at the far left showing only the 4 oldest historical milestones, hiding `Apple reconstruction`, `V1 showcase`, and `V1 done` with no scroll cue.
- **Why it matters:** The stepper is meant to tell a cold visitor "where are we?" in one second; colliding text and a green line running into an unclosed milestone undercut that story.
- **Fix:**
  - Raise `.stepper.goal-ladder li` to `flex: 1 0 104px; padding-right: 14px;` with `overflow-wrap: break-word; hyphens: auto;`.
  - Match `boardColumns()` ordering (closed milestones first, then open milestones in plan order) so the stepper and Program board agree and the green progress bar stays monotonic—or only colour a segment green when *both* the current and next milestone are closed.
  - On render, scroll `.goal-ladder` to center `li.current` (just as `drawMap()` scrolls `#pb-current`), and add a subtle right-edge fade mask on mobile to signal horizontal scroll.

---

### 9. Every numeric table column is left-aligned (unused `.num` CSS rule)
- **Page & panel:** `Machinery` (`Each kind of agent`, `Models`, `Script versions`, `Lock contention`, `Cost by host, task, and model`), `Retro` (`Closed milestones`), `Module` (`Work packages`)
- **Screenshot:** `panels/machinery--each-kind-of-agent.png`, `panels/machinery--models.png`, `panels/machinery--cost.png`, `pages/machinery-desktop.png`, `panels/retro--closed-milestones.png`, `panels/module--work-packages.png`
- **Verified in:** Screenshots + code ([index.html:285](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L285), [L979-L982](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L979-L982))
- **Problem:** `td.num, th.num { text-align: right }` is defined at [L285](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L285) and specified in `DIRECTION.md`, but `table()` ([L979](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L979)) never adds `.num` anywhere in the file. Numbers like `$227.88` vs `$1,470.12` and `10.3K` vs `252` are left-aligned.
- **Why it matters:** Right-aligning tabular numerals is essential for scanning order-of-magnitude differences down cost, token, and error columns.
- **Fix:** Extend `table(headings, rows, announced=headings, numeric=new Set())` to emit `class="num"` on `<th>` and `<td>` for numeric column indices, and pass the numeric columns from Machinery, Retro, and Module tables.

---

### 10. `Delivery` → `Warnings` shows active failure warnings for already-Done work packages
- **Page & panel:** `Delivery` → `Warnings`
- **Screenshot:** `panels/delivery--warnings.png`, `pages/delivery-desktop.png`, `pages/delivery-phone.png`
- **Verified in:** Screenshots + code ([index.html:1182](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L1182)) + `model.json`
- **Problem:** All four warnings (`T2-CAPTURE:WP4`, `CREATOR:WP4`, `ATMOSPHERE:WP7`, `RAY-TRACING:WP3`) carry green `✓` Done chips while saying *"Ready work has waited 9h 52m…"* and *"The next try uses a fresh builder"*. They also render as a raw bulleted list with inline chips rather than `.list-row` items.
- **Why it matters:** Seeing active-tense warnings on finished work packages makes `Delivery` ("How is the work flowing right now?") look stale or contradictory.
- **Fix:** In [L1182](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L1182), filter `model.now.warnings` to active work packages (`!w.ref || packages[w.ref]?.status !== "done"`), and optionally fold warnings for already-done packages into a `<details class="more">` labelled `"N resolved warnings"`. Render warning items as `.list-row` rows (chip + wrapped text, no bullets) for consistency with `Now`.

---

### 11. Awkward/redundant waiting copy ("First waits on No reason recorded", "A dependency" under "A dependency") and stale "Plan map" label
- **Page & panel:** `Now` (`Milestones`, `Not moving`), `Delivery` (`Board`), `Milestone` page, `Module` (`Work packages`)
- **Screenshot:** `panels/now--milestones.png`, `panels/now--not-moving.png`, `panels/delivery--board.png`, `pages/milestone-desktop.png`, `panels/module--work-packages.png`
- **Verified in:** Screenshots + code ([index.html:610](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L610), [L628-L636](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L628-L636), [L690-L691](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L690-L691), [L722](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L722), [L1353](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L1353)) + `model.json`
- **Problem:**
  - `waitNames.none` (`"No reason recorded"`, [L610](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L610)) produces broken mid-sentence capitalization: **`First waits on No reason recorded`** (`now--milestones.png`), even though `APPLE-PRESENTATION:WP12`'s `waiting.detail` actually explains `"No active run in the saved output."`
  - Under `A dependency` in `Not moving` (`now--not-moving.png`), `PUDDLES:WP3` repeats **`A dependency`** as its own subtitle because `w.waiting.targets` is empty (even though `w.waiting.detail` says `"Waiting, on WATERS:WP8"`).
  - Links in `Now → Milestones` ([L691](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L691)) and `Milestone` ([L1353](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L1353)) still read **`Plan map`** instead of **`Program board`**.
- **Why it matters:** Plain, consistent language is an explicit design goal for collaborators arriving cold.
- **Fix:**
  - When `w.waiting.on === "none"`, display `w.waiting.detail || "Idle (no active run)"` instead of `"No reason recorded"`, and omit `"First waits on …"` when `head.waiting.on === "none"` (or say `"Not running"`).
  - In `reason()` ([L628-L633](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L628-L633)), fall back to `w.waiting.detail` when `on === "dependency"` and `targets` is empty; in `waitingRow()` ([L722](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L722)), omit `.reason` if it duplicates `waitNames[on]`.
  - Rename `Plan map` → `Program board` at [L691](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L691) and [L1353](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L1353).

---

### 12. `Machinery` → `Codex weekly limit` hides a 104% projected overrun in the top tile and lacks warning styling
- **Page & panel:** `Machinery` → top stat tiles & `Codex weekly limit` panel
- **Screenshot:** `pages/machinery-desktop.png`, `panels/machinery--codex-weekly-limit.png`
- **Verified in:** Screenshots + code ([index.html:1238](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L1238), [L1268-L1270](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L1268-L1270), [L1293-L1295](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L1293-L1295)) + `history.json`
- **Problem:** The top tile displays `37%` in neutral ink (`used_percent > 80` is false at [L1238](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L1238)), hiding that `quota.warn` is `true` and projected usage is **104%** before reset. Inside the lower panel (`machinery--codex-weekly-limit.png`), both the progress bar and line remain neutral white, and the warning verdict is rendered as a single-item bullet list.
- **Why it matters:** Answering "will we hit the weekly limit?" is one of `Machinery`'s headline jobs (`ACTIVITIES.md` #7).
- **Fix:** Trigger `.attention` on the top tile when `m.quota?.warn || projected >= 100 || m.quota?.used_percent > 80`, include `104% projected` in `.tile-note`, colour the panel's `104% projected` figure and progress bar with `--amber` when warning, and render `quota.verdict` as a `.notice` banner (or plain `<p>`) instead of a one-bullet `<ul>`.

---

### 13. `Machinery` data-viz & table craft issues (unreadable stacked shades, broken slow-check names, empty `Model` column, oversized `24h` chart text)
- **Page & panel:** `Machinery` → `Tokens per day`, `Slow checks`, `Cost by host, task, and model`, `Machine load`, `Logged check results`
- **Screenshot:** `panels/machinery--tokens-per-day.png`, `panels/machinery--slow-checks.png`, `panels/machinery--cost.png`, `pages/machinery-desktop.png`
- **Verified in:** Screenshots + code ([index.html:1194](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L1194), [L1200-L1219](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L1200-L1219), [L1277-L1281](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L1277-L1281), [L1285-L1286](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L1285-L1286), [L1292](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L1292), [L1307](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L1307)) + `history.json`
- **Problem:**
  1. **Stacked bar chart (`machinery--tokens-per-day.png`):** Six opacity steps of `--ink` (`1, .72, .5, .36, .24, .14`, [L1200](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L1200)) blur together at the top of each bar, and `Approval reviewer` (`0.14` opacity on `#141519`) is nearly invisible (~1.5:1). `rx="1.5"` creates tiny notched seams between stacked blocks.
  2. **Slow checks (`machinery--slow-checks.png`):** The command shortener ([L1277-L1278](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L1277-L1278)) produces `export PATH="$(dirname "$(rustup` for the worst offender (`226.9×`) and bare `it` for three distinct checks (`RIVERS`, `SESSION`, `Module unrecorded`).
  3. **Cost table (`machinery--cost.png`):** The `Model` column is `—` on every single priced row, wasting a full column, and its totals repeat `Each kind of agent` while renaming `Lead` → `Interactive` with different session counts (`135` vs `24`).
  4. **Machine load & Logged check results (`machinery-desktop.png`):** `activityTrend()` ([L1194](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L1194)) uses `viewBox="0 0 480 74"` inside a ~720 px column, scaling `11px` SVG labels (`24h ago`, `Snapshot`) up to ~16.5 px (larger than the heading!), and [L1292](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L1292) has a stray closing `</p>`. Meanwhile `Logged check results` devotes a full card to four unstyled words (`3609 passed · 0 failed`).
- **Why it matters:** `Machinery` is dense; low-contrast charts, garbled check names, and redundant tables slow down diagnosis.
- **Fix:**
  - Group the stacked chart into 4 distinguishable series (or use a restrained categorical palette with `rx="0"` and a `1px` `var(--panel)` stroke between segments).
  - Strip leading `export ...;` / `VAR=val` prefixes in the slow-check shortener and, when `--test it` matches, extract `-p <pkg>` and `-E 'test(=<name>)'` (e.g. `thrum-network · reliable_delivery`).
  - Omit the `Model` column in `costs()` when every priced row has `!c.model` (mirroring `moduleScreen()` [L1383](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L1383)).
  - Set `activityTrend()`'s `viewBox` to `0 0 680 90` so `11px` labels stay `11px`, delete the stray `</p>` at [L1292](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L1292), and style `Logged check results` as compact stat figures (or fold it into `Merge queue and main`).

---

### 14. `Retro` mixes open milestones into "Closed milestones", leaves dates unsorted, and treats rows inconsistently
- **Page & panel:** `Retro` → `Closed milestones`
- **Screenshot:** `pages/retro-desktop.png`, `panels/retro--closed-milestones.png`
- **Verified in:** Screenshots + code ([index.html:1322-L1336](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L1322-L1336))
- **Problem:**
  1. Despite the heading `Closed milestones`, open milestones (`Apple reconstruction`, `V1 showcase`) appear mid-table with six `—` cells.
  2. Closed dates aren't sorted (`5 Nov`, `7 Nov`, `5 Nov`, `—`, `23 Nov`, `14 Nov`, `17 Nov`, `Open`, `19 Nov`, `18 Nov`).
  3. Rows with retro data render as `<details>` disclosures with `milestone/…` refs and **no link to the milestone page**, whereas rows without retro data render as milestone links with no ref.
  4. `$30.31 · 6/139 priced` displays `$30.31` at full emphasis even though 96% of sessions are unpriced.
  5. `Design changes` actually renders `r.failed_by_task["design review"]` (failed design reviews), and `By task and host` wraps each entry across two lines.
- **Why it matters:** Retro is for comparing closed milestones over time ("did our planning and cost improve?"); unsorted rows interrupted by open milestones and 4%-coverage dollar figures obscure the trend.
- **Fix:** Filter `model.milestones` to `!m.left.length` (sort reverse-chronologically by `closed_at`, placing pre-orchestration milestones in a footer section or collapsed fold). Always provide a consistent link to `#/milestone/<label>` alongside the `<details>` disclosure. Rename `Design changes` → `Failed design reviews`, shorten `Work package review` → `WP review` (`white-space: nowrap`), and visually mute costs when pricing coverage is under 50% (or lead with `6/139 priced`).

---

### 15. `Delivery` → `Pace` charts borrow the `Ready for Review` status purple, use `33%`/`67%` ticks, and shrink labels to ~5 px on phones
- **Page & panel:** `Delivery` → `Pace`
- **Screenshot:** `panels/delivery--pace.png`, `pages/delivery-desktop.png`, `pages/delivery-phone.png`
- **Verified in:** Screenshots + code ([index.html:393-398](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L393-L398), [L1154-L1161](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L1154-L1161))
- **Problem:**
  1. `.chart-line` and `.chart-point` use `var(--purple)` ([L397-L398](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L397-L398)), which encodes `Ready for Review` everywhere else—contradicting `SCREENS.md` ("charts that do not encode status use neutral ink") and inconsistent with `limitChart()` (`stroke: var(--ink)`).
  2. `Review pass rate` uses thirds (`0%`, `33%`, `67%`, `100%`, [L1156](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L1156)).
  3. On `delivery-phone.png`, `viewBox="0 0 680 128"` scales down to ~330 px wide, turning `11px` axis labels into ~5.3 px micro-text.
- **Why it matters:** Status colours lose meaning when reused decoratively, and phone viewers cannot read the dates or percentages on `Pace`.
- **Fix:** Set `.chart-line` / `.chart-point` to `var(--ink)` and lower `.chart-bar` opacity from `.85` to `.35` so the 7-day average line reads crisply in neutral ink. Use `[0, 0.5, 1]` for percentage guides (`0%`, `50%`, `100%`). Under `@media (max-width: 760px)`, increase `.chart text { font-size: 16px; }` (in SVG user units) so labels render at ~8–9 px on phone screens.

---

### 16. `Milestone` page has double-indented `Longest remaining chain`, a pulsing `Building` badge for `Next`, and IDs placed above titles
- **Page & panel:** `Milestone` → header & `Progress`; `Work package` → header
- **Screenshot:** `panels/milestone--progress.png`, `pages/milestone-desktop.png`, `pages/milestone-phone.png`, `pages/workpackage-desktop.png`
- **Verified in:** Screenshots + code ([index.html:163](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L163), [L1343](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L1343), [L1352](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L1352), [L1356-L1357](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L1356-L1357), [L1488](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L1488))
- **Problem:**
  1. On `milestone--progress.png`, `Longest remaining chain` is indented 20 px right of the bar and chips because `<h3 class="group-label">` (`padding: 14px 20px 8px`, [L163](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L163)) sits inside `panelBody()` (which already has `padding-inline: 20px`).
  2. Line [1343](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L1343) uses `tag("building", "Next")`, giving `Next` a **pulsing blue `●` dot** (`building` status class) even when `0/10` builders are running and the project is Paused.
  3. Both `milestoneScreen()` ([L1352](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L1352)) and `workPackageScreen()` ([L1488](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L1488)) place the monospace ref (`milestone/apple-reconstruction`, `APPLE-PRESENTATION:WP12`) *above* the `<h1>` as a kicker instead of after the name (contrasting with `Now → Milestones` and `DIRECTION.md`).
- **Why it matters:** Misaligned headings look unpolished, and reusing the pulsing "actively building" glyph for a paused milestone misleads the reader.
- **Fix:** Add `.panel-content .group-label { padding-inline: 0; }`. Replace `tag("building", "Next")` with a neutral non-pulsing `<span class="badge">Next</span>` (or static blue pill without `.building`). Move `.ref` after `<h1>` (or inline on the metadata bar beneath it) so the human name leads.

---

### 17. Layout friction on `Module`, `Work package`, and `Now` mobile rows
- **Page & panel:** `Module` (`Needed by modules`, `Work packages`), `Work package` (empty panels, mobile `Proof summary` head), `Now` (mobile `Milestones` title)
- **Screenshot:** `pages/module-desktop.png`, `panels/module--work-packages.png`, `pages/workpackage-desktop.png`, `pages/workpackage-phone.png`, `pages/now-phone.png`
- **Verified in:** Screenshots + code ([index.html:93](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L93), [L180](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L180), [L1365-L1369](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L1365-L1369), [L1378](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L1378), [L1392](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L1392), [L1495-L1499](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L1495-L1499))
- **Problem:**
  - `Module → Needed by modules` (`module-desktop.png`) stuffs 14 `<details>` elements into a horizontal `.bar` (`flex-wrap: wrap`), creating a tangled wall of chevrons (`> EFFECT-GRAPH 1 > CONTENT-LOOP 2 ...`) that shifts layout erratically when opened.
  - `Module → Work packages` (`module--work-packages.png`) duplicates status encoding in every row (`✓ WP1` in `ID` and `✓ Done` in `Status`).
  - `Work package` (`workpackage-desktop.png`, `workpackage-phone.png`) renders three nearly empty boxes (`Proof summary`, `Depends on`, `Needed by`) taking ~400–500 px above `Items`. On `workpackage-phone.png`, `.panel-head` squeezes `Proof` / `summary` onto two lines beside `0/5 items pass · 0 reviews · 0` / `failed`.
  - On `now-phone.png`, `.milestone-title` lacks `flex-wrap: wrap`, forcing `Apple` / `reconstruction` and `milestone/apple-` / `reconstruction` into two narrow side-by-side wrapping columns. *(Also note that long `MODULE:WPn` chips in `Not moving` squeeze phone titles down to 2–4 words—worth keeping in mind as you do the upcoming name-first pass.)*
- **Why it matters:** Wastes prime vertical space on detail pages and creates awkward wrapping on 390 px screens.
- **Fix:**
  - Give `Needed by modules` a tidy multi-column grid (`display: grid; grid-template-columns: repeat(auto-fill, minmax(170px, 1fr)); gap: 6px 12px;`) instead of `.bar`.
  - When a work package has `0` reviews and no dependencies, collapse `Depends on` / `Needed by` into a single compact metadata line in `.detail-head` (or omit empty panels) so `Items` starts near the top.
  - Add `flex-wrap: wrap; row-gap: 4px;` to `.milestone-title` ([L180](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L180)) and mobile `.panel-head` ([L511](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L511)).

---

### 18. Accessibility contrast edge cases, nested-box density, and data-excerpt clipping
- **Page & panel:** Cross-page (light mode tokens, `Milestones` legend, nested `.panel` surfaces); `Module` (`Choices made for you`, `Recent log entries`)
- **Screenshot:** `panels/now--milestones.png`, `panels/milestone--progress.png`, `pages/delivery-desktop.png`, `panels/module--recent-log-entries.png`, `pages/module-desktop.png`
- **Verified in:** Code + WCAG contrast calculation (light mode tokens, [index.html:12](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L12)), screenshots (dark mode swatches & nested boxes), and `model.json` (excerpt truncation)
- **Problem:**
  1. **Light-mode AA contrast failure (verified in code):** `--faint` (`#71717c`) on `--subtle` (`#f2f2f5`) measures **4.32:1**—below WCAG AA's 4.5:1 threshold for small text (`11.5px` `.ref`, `.module-cell small`, `.stepper .step-name` on subtle/hovered surfaces).
  2. **Dark-mode `not_started` swatch (`now--milestones.png`):** `border: 1px dashed var(--line-strong)` (`#34353e` on `#141519`, [L665](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L665)) is barely visible (~1.4:1).
  3. **Boxes inside boxes:** `DIRECTION.md` calls for dropping the outer border around every section ("Whitespace separates, not borders"), yet `Needs you`, `Delivery → Board`, and `Work package → Items` still nest 2–3 bordered containers inside `.panel`.
  4. **Mid-sentence/mid-word clipping in `model.json` (note for extractor, not CSS):** `Module → Choices made for you` (`module-desktop.png`) ends mid-phrase (`…written and`, `…D8.3 allows`), and `Recent log entries` (`module--recent-log-entries.png`) ends mid-word (`Stationary contro`).
- **Why it matters:** Small contrast regressions accumulate in light mode, nested chrome makes cards feel heavier than intended, and raw byte-sliced excerpts look broken even though they originate in the extractor.
- **Fix:**
  - Darken light-mode `--faint` from `#71717c` to `#63636e` (5.14:1 on `--subtle`, 5.75:1 on `--panel`).
  - Use `var(--muted)` for the dashed border of the `not_started` swatch in [L665](file:///Users/ryannel/Workspace/skills/workbench/orchestration-observability/prototype/index.html#L665).
  - Consider adding a borderless `.section` wrapper (just heading + content, separated by `margin-top: 40px`) for sections that already contain cards (`Needs you`, `Delivery → Board`, `Program board`) to eliminate box-in-box clutter.
  - Trim `choices` / `excerpt` in `build_model.py` on word or sentence boundaries with a trailing `…`.

---

## 3. What works well (keep these)

- **Overall dark-mode tone, typography, and restraint:** The neutral slate palette (`#0c0d10` / `#141519` / `#1b1c21`), crisp SF Pro / tabular numerals, and strong dark-mode contrast ratios (all primary and status tokens pass AA comfortably at 5.3:1–11.5:1) feel genuinely calm and modern.
- **`Plan` → `Goal` hero layout (`panels/plan--goal.png`):** Leading with "What we're building", the green-accented "V1 is done when" callout, and collapsible "Still open" decisions beside it immediately orients a cold collaborator.
- **Segmented milestone progress bars (`panels/now--milestones.png`, `panels/milestone--progress.png`):** Showing done, waiting, and not-started shares in a single bar with exact counts and the remaining dependency chain directly underneath answers "how close are we?" at a glance.
- **Delivery board empty-state handling (`panels/delivery--board.png`):** Collapsing `Not started 38` into a disclosure and summarizing empty columns (`Empty now: ▷ Ready to build · ● Building · ◐ Reviewing`) in one quiet strip keeps the board focused on active flow instead of wasting half the width on empty lanes.
- **Thoughtful accessibility & resilience foundations in code:** Skip links, `aria-live="polite"` announcements, deferred live updates while a panel has focus, `prefers-reduced-motion` support, semantic `<time datetime>`, keyboard arrow navigation on the Program board and Timeline, and zero external font/CDN dependencies are all cleanly engineered and worth preserving.
