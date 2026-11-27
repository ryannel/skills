# Design review: orchestrate's observability page

I'd like a UI design review of a prototype dashboard, from the screenshots and the code. You're reviewing only;
I'll make the changes, and the owner looks at the polished result in the morning. So what I need from you is a
ranked list of concrete problems and fixes I can act on.

## What the page is

Orchestrate runs a software project with AI agents: planners split the work into modules and work packages,
builders build them, reviewers check them. This page lets a person watch one such project, called Thrum (a Rust 3D
engine), without taking any actions: it only shows. The data is a real snapshot of Thrum.

The pages and who each is for:

- **Now**: the owner coming back after a while, often on a phone. "Do I need to do anything, and is it moving?"
- **Plan**: the owner steering, and a collaborator arriving cold. "What are we building, how was the work broken up,
  and where are we in it?" It opens on the goal, then a program board (rows are modules, columns are milestones, a
  work package sits under the first milestone that needs it, and work no milestone needs has its own column on
  purpose).
- **Delivery**: "How is the work flowing right now?" Board, pace, warnings, timeline.
- **Machinery**: the owner improving orchestrate itself. Agent sessions, tokens, cost, quota, errors, slow checks.
- **Retro**: what each closed milestone cost and how good its plan was.
- **Module, work package and milestone pages**: where every question ends up.

Decisions already made, which aren't up for review: the page takes no actions; things are shown by name first, with
an ID only as a small reference after it (milestones are done; modules and work packages still show codes such as
`APPLE-PRESENTATION` or `WP12`, which is known and next on my list, so you can mention it but don't spend findings
on it); the program board keeps its "Not tied to a milestone" column. Odd text inside the data, such as "G4" in a
work package name, comes from Thrum and isn't a UI problem.

## What you have

- Screenshots in `review-2026-11-26/before/`: `pages/` holds whole pages at desktop width (1440 px) and phone
  width (390 px), and `panels/` holds each panel cropped from the desktop pages, named `<page>--<panel>.png`.
- The code: `prototype/index.html` is the whole page (CSS, markup and script in one file); `prototype/model.json`
  is the data it renders. `DIRECTION.md`, `SCREENS.md` and `ACTIVITIES.md` describe the intended design.
- The live page, if you can open a browser: `http://127.0.0.1:8772/prototype/index.html` (routes such as `#/now`,
  `#/plan`, `#/delivery`, `#/wp/APPLE-PRESENTATION:WP12`). Hover and click work there; the screenshots can't show
  them.

All paths are relative to `workbench/orchestration-observability/` in this repository. Please don't edit any
files.

## What I want back

Look at every page at both widths, and at the panels up close. Judge it as a designer would: whether each page
answers its question at a glance, visual hierarchy, layout and spacing, typography, colour and status encoding,
consistency between pages, how it works on a phone, accessibility, and whether the words are plain and clear to
someone who hasn't seen the project.

Your reply is the report, in markdown:

1. **The five changes you'd make first**, each in a sentence or two.
2. **Findings**, most important first. For each one give the page and panel, the problem, why it matters to the
   person reading that page, and a concrete fix, down to the CSS or markup where you can (cite `index.html` line
   numbers or selectors). Name the screenshot that shows it. Say whether you confirmed it in the screenshot, code or
   browser, or are inferring it.
3. **What works well** and should be kept, briefly.
