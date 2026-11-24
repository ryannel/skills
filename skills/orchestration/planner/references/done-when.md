# The module's files

A planner writes the plan, and builders and reviewers act on it. This file gives the shape of each file a planner
writes. The script reads several of them, so their shapes are strict. `agent_loop.py settings` prints where each
file is in a project.

Contents:
- [The files and their readers](#the-files-and-their-readers)
- [The module table](#the-module-table)
- [`PLAN.md`](#planmd)
- [`LOG.md`](#logmd)
- [`DONE.json`](#donejson)
- [Who changes what, and when](#who-changes-what-and-when)

## The files and their readers

| File | What it holds | Written for |
|---|---|---|
| `ARCHITECTURE.md` | The module list: the module table, then what each module owns and the interfaces between them | The user reads the table and work package names, so write those in plain words, as what someone can see or do |
| `<MODULE>/DESIGN.md` | The design: mechanisms, range and interfaces | Builders and reviewers, so write it precisely, with paths and IDs |
| `<MODULE>/PLAN.md` | What is left to build | Builders |
| `<MODULE>/LOG.md` | The module's history, oldest first | Planners and the lead, later |
| `<MODULE>/DONE.json` | The done-when file: each work package's items | Builders, reviewers and the script |

The plans folder also holds `VISION.md` and `GLOSSARY.md`, which the lead keeps with the user, and `STATUS.md`, the
user's status page, which the script writes. Reviews, captures and other proof go in the working folder, which is
never committed and is the same folder in every worktree.

A project's plans live in these files and nowhere else. A plan written in another shape or another place is
converted into these files and the old one deleted, because two plans for one thing drift apart and the user can't
tell which is current.

## The module table

`ARCHITECTURE.md` opens with a table of every module, in the order they are built. The script reads it, so keep
this exact header:

```markdown
| # | Module | What it's for | Needs |
|---|---|---|---|
| 1 | AUTH | People sign in, and stay signed in across devices | |
| 2 | ONBOARDING | A new end user gets from sign-up to a first project | AUTH |
```

`What it's for` is one sentence in plain words, for the user. The table has no status column, because the status
page shows each module's status.

## `PLAN.md`

The plan file says what is left to build, and nothing else. It holds no status, because the script knows each
work package's status, and status written by hand goes stale.

```markdown
# <Module> plan

## Open for the user
- Assumption: <a reading of the user's words the planner chose, which the user can overturn>

## WP1 <what someone can see or do>: done
[review](<link to WP1-review.md in the working folder>)

## WP2 <what someone can see or do>
<A few sentences for the builder, on what the items and the design don't say. Nothing, when there is nothing.>

## WP3 <what someone can see or do>

## WP4 <what someone can see or do>
```

A work package with no items yet, such as WP4, has only its heading. A Done work package shrinks to its heading and one
link to its review, because the detail stays in the review, the log and git. `Open for the user` holds only open
assumptions. [Planning a module](../tasks/module.md#the-work-packages) says how to name a work package and what goes in the
note under one.

A limit on what a builder may do goes where it holds, with its reason beside it. One that is true of every module,
such as how a browser is started or a path nobody edits, goes in the project settings or the guidance their `Project
guidance` section links to. One about this module goes in the design. Only a limit on this one work package goes in its
note.

## `LOG.md`

The log is the module's history: decisions, proposals to change an interface, what a failed review found, and what
the user said. Each entry is one dated line, with at most a few lines under it, and the newest at the bottom. Longer
detail goes in the working folder, with a link. Nobody reads the log to find out where the module stands, so it may
grow.

```markdown
- 2026-11-03 WP2: review failed on the empty state; fixed, and the second review passed.
- 2026-11-05 User: "keep the old URL working" (quoted from chat).
```

## `DONE.json`

The done-when file lists, for each work package, its items: the things that must be true before the work package is
Done. It is JSON because the script reads it. A new work package starts like this, with every item open:

```json
{
  "module": "ONBOARDING",
  "work_packages": [
    {
      "id": "WP2",
      "name": "A new end user signs up and lands on an empty dashboard",
      "status": "not_started",
      "depends_on": ["AUTH:WP1"],
      "quality_bar": "As quick and calm as Linear's sign-up, with an empty state as clear as Things'",
      "items": [
        {
          "id": "WP2.1",
          "statement": "A valid email reaches the dashboard in three screens or fewer; invalid input is rejected inline",
          "check": "npx playwright test e2e/signup.spec.ts",
          "target": "web-chrome",
          "builder_result": "open",
          "evidence": ""
        },
        {
          "id": "WP2.2",
          "statement": "Every step is readable and tappable at 375 px with no layout shift as fields validate",
          "inspect": "From screenshots of each step and each validation state at 375 px: 1. every label and error reads without zooming; 2. every button and field is at least 44 px tall; 3. nothing moves when an error appears or clears.",
          "target": "web-mobile-safari",
          "builder_result": "open",
          "evidence": "",
          "verdict": "",
          "review": ""
        }
      ]
    }
  ]
}
```

The planner writes the fields that say what a work package asks for:

- `statement` says what must be true, as a closed claim a reviewer can judge once, as [the items](../SKILL.md#the-items)
  describes.
- `check`, `inspect` and `ask` say how the item is proved. An item uses at least one, and may use more. An `inspect`
  is a checklist drawn from the reference in `quality_bar`: a line saying what to look at, then numbered points the
  reviewer answers yes or no. [Ways to prove an item](proofs.md) describes each.
- `target` is one of the targets in the project settings, meaning a device or platform the product runs on. When
  the proof runs on a stand-in, it is `stand_in:<what it stands in for>`.
- `quality_bar` is how good the work package has to be. It makes the settings' quality bar specific to this work package,
  and names the reference each `inspect` is drawn from. For a mix it names several, each saying what it is the
  reference for.
- `depends_on` is optional. It lists the work packages in other modules that must be Done before this one starts,
  written `"AUTH:WP1"`. Work packages inside one module already run in order, so leave out earlier ones from the same
  module. An entry may name a work package that so far has only a heading in the other module's plan file, so a
  work package's ID stays the same once written.
- `lock` is optional. It names a resource from the settings' `Exclusive resources` or `Shared resources` line that
  the item's `check` needs, and the script takes that lock while the check runs. For a shared resource, `gpu` shares
  it with other runs, and `gpu.alone` waits to have it alone, which only a run that needs the whole device calls for.
- `reads` is optional, for an item with a `check`. It lists the files the check reads, as git pathspecs from the top
  of the repository, such as `["src/render/", "models/*.json"]`, so the script can reuse the check's last pass while
  those files stay the same. Without it, a pass is reused only while the whole tree stays the same.
- `needs` is optional. It marks an item a builder can't finish alone, as `{"type": ..., "what": ...}`, where `what`
  says in plain words what is needed, such as "plug in the iPhone". The `type` is one of three:
  - `human_feedback`: someone has to look at the result and judge it, because no agent can tell, such as whether a
    sound is pleasant. The user's reply is recorded as User Feedback.
  - `access`: the user has to approve a permission or a prompt, such as Computer Use for an app, so the builder can
    finish it only in a visible session with the user at the machine.
  - `hardware`: a device has to be connected, such as an iPhone.
- `alone` is optional, `true` for a work package measured with no other agent working, such as precise timings.

Once approved, those fields are fixed: only a planner that `plan` started, or the user through `human scope`,
changes them, because a builder who could edit them could pass anything.

## Who changes what, and when

Each field of the done-when file has one owner, and the script refuses a change from anyone else:

- The planner writes the fields above, and starts a new work package at `not_started` with its items open.
- A builder sets `status` to `in_progress` when it starts, and each item's `builder_result` (`open` or `pass`) and
  `evidence`, the path to its proof, while it builds.
- A reviewer sets each item's `verdict` (`pass`, `fail` or `could_not_judge`) and the work package's `findings`.
- The script sets every other status, the review counts, `review` and the `blocked` field, and keeps the record file
  beside the done-when file. A work package is Done only when the record file says so.

A planner leaves the counts, `findings` and the record file alone, and changes `status` only on a work package it adds.
