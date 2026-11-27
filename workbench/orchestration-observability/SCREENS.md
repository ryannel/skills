# Screens and the page's data

The second step after [ACTIVITIES.md](ACTIVITIES.md): what each screen shows, how you move between them, and the data the script serves to the page. Names follow orchestrate's glossary: goal, milestone, module, work package, item, task, vision and scope document.

## How the page is served

`agent_loop.py serve [--port 8787]` serves the page on `127.0.0.1` and keeps running until stopped. It builds one model from the plan files, the records, the run state and the delivery history (the same reading `status`, `flow` and `dashboard` already do), serves it at `/model.json`, and pushes a short `changed` event over `/events` (server-sent events) when any of its sources changes. The live page refetches the model on that event and defers applying it while a panel has focus. The static prototype exercises that interaction with a simulated refresh. The page takes no actions, so there is nothing to post back.

Where a source isn't on this machine (a collaborator's clone has no run state, delivery history or evidence), the model says so under `project.here`, and the screens that need it say "not on this machine" instead of showing empty charts.

## Layout and navigation

The project bar names the connection state and shows the last update. The static prototype says Snapshot. The live server is expected to report Live or Disconnected. A refresh preserves focus and disclosures. If a panel has focus, an update waits behind **Updated, show changes**, with a polite announcement. Routes focus their heading, anchored jumps focus their target, and Back and Forward restore the viewer's place.

On desktop the areas are tabs. On phones Now, Plan and Delivery sit in a bottom bar. More contains Machinery and Retro. The short-screen header scrolls away, and focus stays clear of the bottom bar. Module and work package pages highlight Plan and have shareable URLs.

Chips use status colours and shapes together. Done uses a quiet outline with ✓, Building ●, Reviewing ◐, Ready for Review ◆, Ready to build ▷, Waiting ⏸, Blocked !, Failed ✕, and Not started a dashed outline. Links, indicators and charts that do not encode status use neutral ink. The chip popover gives the work package name, status, waiting reason and date, module, milestone and dependency counts. It opens on hover or focus and closes on Escape.

## Names first

Modules and work packages are shown by name, with the code only as a small reference after it: "Clouds" rather than `CLOUDS`, "Mist lies in the valley's hollows… WP14" rather than `CLOUDS:WP14`. A module's name is the title of its design (`DESIGN.md`), up to any colon or dash and without goal codes such as "(G3c)"; where the title is only the code again, the code is spelled out ("Game UI"). Waiting reasons name the work package waited on, shortened to about 60 characters. Codes stay in tooltips, page references and URLs.

## Now

1. **Needs you** leads at full width. Cards show the builder's question and the milestones and unfinished work packages held up. They sort by milestone impact and downstream count. The count follows explicit dependencies and work package order within modules.
2. **State** shows supervision, builders, reviews and the time since the last merge on one line. Running tasks get their own rows when present.
3. **Milestones** shows the open milestones with progress and the remaining chain inline. The first waiting reason is visible. A user blocker holds the estimate. Otherwise the estimate uses the slower of the remaining volume at the last seven complete days' throughput and the chain length at the median recent builder session duration. The date is an estimate anchored to the saved snapshot; once it has passed, the milestone says "Overdue" in amber. "Next up" names the first unfinished work package and why it waits. Closed milestones are summarised in one line linking to Retro on desktop and omitted from Now on phones.
4. **Since you last looked** is measured from the snapshot's own time, never from after it. It opens with counts by event kind, followed by status events, plan changes and merges, with a fold for bulk tooling commits.
5. **Not moving** groups stalled packages by reason. Dependency rows identify the packages they wait on and any upstream blocker that needs the user.

## Plan

- **Goal** opens the page, because the plan only makes sense against what it is for. "What we're building" leads with the goal's first sentence as the headline and the rest beneath it, then "V1 is done when" with the V1 exit. Beside it, "Still open" lists the vision document's open decisions by title, each expandable, with a link to the full vision and scope document. Below, one line says how many milestones are closed, which is next and when it is expected (or that it is overdue), and how many work packages are open, over the milestone ladder ending in "V1 done".
- **Program board** replaces the plan map. Rows are modules and columns are milestones, in the order they closed, then the open ones in plan order. A work package sits under the first milestone that needs it. Work no milestone needs stays in its own wide **Not tied to a milestone** column rather than being guessed into one, so the board shows how much of the plan sits outside the milestones. Milestones that closed before they recorded their work show "Work not recorded". The next milestone's column is highlighted, and the board opens scrolled to it. **Whole plan** shows finished work as one-line rows; **From here on** is the default; it hides finished work and narrows closed milestones to ✓ counts. In Whole plan, more than three done cards fold into "✓ n done". The sticky module column has a visible edge. On phones the board becomes a list per milestone, long lists folded after five. A **Dependencies** toggle chooses between lines **For the selected card** and **All**, and the choice is remembered. With All on, links into unfinished work are blue and links between finished work are faint, every line has an arrow toward the work that waits, and hovering, focusing or selecting a card highlights its links while the rest fade. A card that depends on work in a later column gets a red outline, because the plan is out of order. The board is one tab stop with arrow navigation and a skip link.
- **Modules** shows delivery, progress and exact open dependencies on desktop; design state appears only when it is not approved. Phones use one line per module.
- **Choices made for you** leads with a flat list of new choices with their modules. Older choices are grouped by module and newest first. The section starts closed on phones.
- **Plan changes** leads with changed work packages, and includes definition, design, vision and architecture changes. An All commits disclosure includes other plan-area commits. The section starts closed on phones.

## Delivery

- **Board** includes a count and toggle for Not started, narrow headers for empty statuses, waiting reason tags and age when available. Phones use one column of cards per status. Cards show two lines of title and expose full details on focus.
- **Timeline** has a named scroll region and one tab stop with arrow keys. The list view presents the same window in rows.
- **Pace** has a daily completion chart with a seven-day average and a separate 0–100% review pass-rate chart. Each has an accessible sentence summary and the daily-counts fallback.
- **Warnings** use plain sentences as rows, once per work package, with the same text in its header. Warnings on work packages that have since finished fold under "n on work that has since finished".

## Machinery

Machinery replaces the separate `dashboard` page, so there is one view. It opens with the agents: tiles for sessions, weighted tokens, recorded cost, the Codex weekly limit and turns that ended badly; tokens per day stacked by kind of agent; a table per kind of agent (sessions, turns, median and 90th-percentile turn length, tokens, cost, aborted turns, context fill); why turns ended badly and errors per day; how long turns run and how full the context got; models and script versions. The machine and merge sections follow. `history.json` carries these as `agents`, reduced from the dashboard's session and turn records. Once `serve` ships, `dashboard` can go, or stay as a static export of the same page.

The saved machine load readings are a snapshot. The 24-hour chart counts recorded agent sessions by hour. Slow checks show the ten largest ratios to usual duration, named as package · test (skipping environment set-up at the front of the command), a module when attributable and the full expandable command. Counts have their saved windows and definitions. Error entries link to recorded sessions where identifiable. Cost leads with session count, adds dollars with pricing coverage and folds unpriced groups. The Codex weekly limit compares usage with a projection to reset; the tile and the projection turn amber when the projection reaches 100%, and the verdict shows beneath the chart.

## Retro

A table lists closed milestones only, newest first, each linked to its milestone page. It gives closure, duration, cost as "at least $X" with how many sessions were priced, planned and added work, failed work package reviews and failed design reviews, and review outcomes by task and host. Drill-downs show added packages and affected modules. Planned counts use the first plan revision containing the closing work package.

## Module and work package pages

The module page header carries a progress bar and "x of y done". Work packages come first, in build order, with status, the waiting reason for unfinished ones, and failed-review counts muted once done; empty optional columns are removed. Dependencies on and from other modules follow. Module titles and work package names use ink.

Detail pages put the name first and the reference after it. The milestone page lists the work left by name. The work package header shows warnings and "Needed for" each milestone whose remaining chain includes it; Depends on and Needed by collapse to one line when both are empty. A proof grid summarises items and reviews, and each cell jumps to the item. Item rows put enlarged verdicts alongside the item ID, mark the latest failures with a red rule, collapse the statement to its first line and tint the reviewer question. Evidence labels are relative to the work package folder. Reviews keep their linked findings, generated-summary label and full text when available. The runs section loads on demand.

## The data model

The script writes two JSON documents. The page loads `model.json` first, with the data for Now, Plan, the Delivery board and pace, and module and work package pages. It loads `history.json` once on demand when a viewer opens Machinery, Retro, the timeline, or a work package's Builder runs section, or follows a recorded session from Machinery. References between things are `MODULE:WPn` strings.

### `model.json`

```json
{
  "project": {
    "name": "Thrum",
    "goal": "…",
    "built_at": "2026-11-24T16:00:00Z",
    "script_version": "3.1.0",
    "state": "paused | running",
    "here": {"run_state": true, "history": true, "evidence": true}
  },
  "milestones": [
    {"label": "apple-reconstruction", "ref": "milestone/apple-reconstruction", "name": "Apple reconstruction", "about": "…", "closed_by": "APPLE-PRESENTATION:WP11",
     "needs": ["…"], "done": 21, "total": 27, "left": ["…"], "longest_chain": ["…"], "closed_at": null, "held_by": ["APPLE-PRESENTATION:WP7"], "expected_at": null}
  ],
  "modules": [
    {"id": "CLOUDS", "name": "Clouds", "order": 17, "delivers": "…", "design": "approved | in_review | not_approved",
     "waits_on": ["EFFECT-GRAPH:WP2"], "work_packages": ["CLOUDS:WP1", "…"],
     "choices": [{"text": "…", "since": "2026-11-20T…"}], "links": {"design": "…", "plan": "…", "log": "…"}}
  ],
  "work_packages": {
    "CLOUDS:WP7": {
      "module": "CLOUDS", "id": "WP7", "name": "…", "status": "blocked",
      "waiting": {"on": "user", "detail": "needs_context: …", "since": "…"},
      "depends_on": ["…"], "needed_by": ["…"], "closes": null,
      "items": [{"id": "WP7.1", "statement": "…", "check": "…", "ask": "…",
                 "verdicts": ["fail", "pass"], "evidence": [{"path": "…", "here": true}]}],
      "reviews": [{"n": 2, "at": "…", "verdict": "fail", "summary": "…", "host": "codex", "model": "…",
                   "findings": [{"name": "…", "item": "WP7.4", "repeat": false}], "tokens": 120000,
                   "text": ".orchestrate/evidence/CLOUDS/WP7-review-2.md", "text_here": true}]
    }
  },
  "now": {"running": [], "builders": {"running": 0, "limit": 10}, "reviews_running": 0,
          "last_merge": "…", "supervisor": "stopped", "needs_you": [], "warnings": [{"ref": "CLOUDS:WP7", "text": "…"}],
          "recent_events": [], "event_times": [[1795536000, "done"]]},
  "documents": {"CLOUDS/plan": {"path": "docs/plans/CLOUDS/PLAN.md"}},
  "plan_changes": [{"at": "…", "commit": "…", "subject": "…", "modules": ["…"], "definitions_changed": ["…"]}],
  "pace": []
}
```

The model keeps document references, short log excerpts, and evidence paths. The prototype copies linked plan documents and available evidence to `content/` and loads each file when opened. A review's `summary` stays null until the reviewer supplies one. The page labels its fallback as generated and builds it from recorded item verdicts and findings.

### `history.json`

```json
{
  "sessions": [{"kind": "builder", "ref": "CLOUDS:WP7", "start": "…", "end": "…", "host": "codex",
                "model": "…", "ended": "ready_for_review", "cost": 1.2}],
  "events": [{"at": "…", "kind": "done | ready_for_review | review_failed | blocked | plan_changed | merged",
              "ref": "CLOUDS:WP7", "text": "…"}],
  "checks": [],
  "machinery": {"…": "the current dashboard's records"},
  "retro": {"sky-and-atmosphere": {"first": "…", "cost": 1.2, "sessions": 4, "priced": 1}}
}
```

**Waiting has exactly one value** for each work package that isn't Done or Not started, taken from what `flow` already reports in `not_moving`: `dependency`, `review`, `merge`, `user`, `lock`, `failure`, or `none` while it's moving.

**Since you last looked** uses the browser's last-seen time in local storage. The recent event excerpt in `now.recent_events` supplies the visible rows. The full event index in `now.event_times` (Unix seconds and kind) supplies the counts without loading history. The All commits disclosure reads `content/plan-commits.json` separately.

## What the script needs that it doesn't have yet

1. **Milestones in the plan.** A milestone is a mark on the work package that closes it: a `closes` field on that work package in its done-when file (`"closes": "apple-reconstruction"`), and a line per milestone in the vision and scope document's milestones section naming it. The model computes the rest from `depends_on` and plan order. Planners set the mark; `migrate` doesn't guess it. For Thrum the lead adds the marks once, through a planner task. This field sits outside the definitions hash, so adding it doesn't reset any work package.
2. **A summary per review.** The reviewer writes two or three sentences in its result saying why the work package passed or failed, and the script stores it in the record's review entry as `summary`. Older reviews use a generated line based on their recorded verdicts and findings.
3. **`serve`.** The command, the model builder (shared with `status` and `flow` so the numbers agree), and change detection: the plan folder's and records' modification times, the run state folder and the history file, polled every few seconds.
4. **The page itself**, shipped beside the script like `dashboard.html`, with no build step and no network fetches beyond its own server.

## Prototype first

Before the script changes, a prototype in this folder: a small extractor that builds the model above from Thrum as it is now (`prototype/build_model.py`), and the page reading the saved `model.json`. It shows the screens with real data, so the layout can change before anything is built into the script. Milestones are marked by hand in the extractor for the prototype, by slug, such as `sky-and-atmosphere`. Each milestone has its own page, `#/milestone/<slug>`, which every milestone link opens.
