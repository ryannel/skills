# Planning for older versions, and for behaviour across modules

A design for two friction points found when the orchestrate set plans a microservice system kept in one
repository, one module per service. Nothing under `skills/` has been edited. Line numbers are against branch
`orchestrate-1.6.4` at `fea7c17`.

## The two problems, restated

**Older versions.** Done means merged with checks passing, and nothing more (the record file's `accepted` entry
holds a commit and the checks, `agent_loop.py:4629`, `:5026`). Services deploy one at a time and roll out
gradually, so for a while an old ORDERS calls a new PAYMENTS. A library has the same problem with its users,
who upgrade when they choose. Today the planner settles an interface change as one step, "with every module
that provides or uses that interface" (`plan-module/SKILL.md:108-109`), and the builder's route in is one
proposal line in `LOG.md` (`build-milestone/SKILL.md:133-134`). Nothing prompts a planner to split the change,
and no item ever says "the previous version still works".

**Behaviour across modules.** Every milestone belongs to one module, and the module lines are drawn around state
(`plan-module/SKILL.md:104-106`). An order that is paid for and then confirmed by email crosses three modules and
belongs to none, so nobody writes its items and no reviewer runs the whole system.

## The design in one paragraph

Two pieces of planner guidance, one new line in the project settings, one row in the targets table, and a
documented field of the record file. No script change. Behaviour across modules gets a module of its own that
owns no state, only the journey's tests and the harness that runs the modules together; its milestones `need`
the milestones that deliver each step, which the script already supports. When the settings say older versions
stay in use, the planner settles a breaking interface change as three milestones joined by `needs` (add the new
shape beside the old, move each caller, remove the old shape), proves the first with a check that runs the
caller's previous release against the new provider, and gives the removal an `attended` item in which the owner
confirms nothing running still uses the old shape. The same harness, owned by the journey module, runs both kinds
of check, so the two problems share one owner and one tool.

## Part 1: a module for behaviour across modules

### What it is

A module that owns a journey through other modules: the tests of that journey, and whatever runs the modules
together (a compose file, seed data, the script that waits for every service to be healthy). It owns no state.
Its milestones `need` the milestones that deliver each step, written `"PAYMENTS:M3"` as today.

This is not a new kind of module. The script treats it like any other: it has a design, a plan, a done-when file
and a design review. Nothing in the script assumes a module owns state. The module table's `Needs` column is for
display only (`agent_loop.py:6303`, `:6464`), and `need_cycles` works on milestones, not modules
(`agent_loop.py:1336-1365`), so a journey module that needs every service raises no cycle.

### Why it works with the existing rules

- **Who fixes a broken step.** The journey's builder may not change another module (`build-milestone/SKILL.md:135-137`).
  When a step fails, it ends `BLOCKED` naming the module, and the planner adds a milestone there and a `needs`
  entry here (`plan-module/SKILL.md:123-127`). That is the right owner for the fix, and it is the existing route.
- **Who reviews it.** The journey module's own reviewer, on a target that is the whole system. A target is a row
  in the settings' targets table (`profile.md:52-57`), with its own Run and Capture columns and edge conditions,
  so "run the whole system" becomes something the settings say how to do, not something each reviewer invents.
- **Keeping it working.** Once a journey milestone is Done, nothing re-runs its check when PAYMENTS changes later,
  because the script runs only the claimed milestone's checks plus the `Check:` line (`agent_loop.py:2757-2760`).
  The guidance is to add the journey's test to `Check:` once it passes, which is how the set already turns a
  repeated finding into a standing check (`plan-module/SKILL.md:211-213`).

### Rejected alternatives

- **Putting the journey's items in the last service's milestone** (NOTIFY's, say). Its builder would then need to
  fix ORDERS to pass, which it may not, and the journey's owner would be an accident of build order.
- **A milestone shared by several modules, or a new "flow" kind.** One builder works in one module's worktree;
  a shared milestone needs a new owner rule, new claim and record handling, and new statuses. The plain module
  gets the same result with none of that.
- **One module per journey from the start.** Milestones in a module run in order, so one module for every journey
  lets a stuck journey hold the rest. But the harness needs exactly one owner. So start with one module for
  behaviour across modules, holding the harness, and split a journey into its own module (needing the harness
  milestone) when the journeys are independent and numerous. This stays planner judgement; I would not write a
  rule for it until it has gone wrong.

## Part 2: older versions in use

### The settings line

The planner can't tell from the code whether a merged change is running everywhere at once. One new line in the
project settings says so. It is for agents, not the script, so `profile()` needs no change:

```markdown
- **Older versions:** <who keeps running an older version after a merge, and how to find the version they run, such as "services deploy one at a time; a service's running version is its newest tag <module>-v*", or "users pin releases; the previous release is the newest v* tag"; or none>
```

`none`, or no line, means a merge replaces everything at once, and none of Part 2 applies. That gates the new
guidance, so a single-binary project's planner pays nothing for it.

### The three milestones

When the line is not `none`, a change that would break an older caller is settled as three milestones joined by
`needs`. The industry names are expand and contract, or parallel change; the guidance should use plain words:

1. The providing module adds the new shape and keeps the old one working.
2. Each calling module moves to the new shape. Each of these `needs` step 1.
3. The providing module removes the old shape. It `needs` every step 2, and has an `attended` item in which the
   owner confirms that no running version still uses the old shape.

The `attended` item is what bridges "merged" and "deployed" without teaching the script about deployment. The
script already holds a milestone with an open `attended` item until the owner answers, and lists it on the owner's
page (`done-when.md:196-198`, `:65-66`). Deploying is usually on the `Owner decides` list anyway (`profile.md:62`).

The `needs` graph interleaves the two modules (PAYMENTS M4, then ORDERS M5, then PAYMENTS M6). The cycle check is
per milestone and counts each module's own order (`agent_loop.py:1344`), so this is not a cycle.

A database change inside one module takes the same three steps as three milestones of that module: add the column
and write both, move reads and backfill, drop the old column. The older version is then the module's own previous
release running against the new schema.

The planner records the change in the interface's entry in `ARCHITECTURE.md` as prose: both shapes, and the
milestone that removes the old one. I reject a version field that the script reads. The script can't check that
code matches a version number, so it would be one more thing to keep in step with nothing to enforce.

### The compatibility check

Step 1 gets an item that the previous release of each caller still works against the new provider, proved by an
Automated Check. Two questions decide whether that check means anything.

**Which commit is "the previous release"?** In order of preference:

1. What the `Older versions` line says, such as the newest `orders-v*` tag. This is the version really running.
2. Otherwise, the commit at which the caller's last milestone before the move was accepted. The record file
   already stores it, under `milestones.<id>.accepted.commit` (`agent_loop.py:4629` for a milestone Done on its
   checks, `:5026` for one Done by review; both are commits on the main branch). That milestone goes in `needs`,
   so the commit exists before the check runs.

I reject "the previous commit of the repository" (`HEAD~1`, or the base the builder started from). In one
repository the previous commit is usually some other module's work, and the base moves with every merge, so a
reviewer re-running the check later would compare against a different version. It also measures "merged",
which is the thing we already know is not "running".

**How does the check build an old version without breaking the rules on checks?** The script fails a check that
leaves files in its clean checkout (`agent_loop.py:2806-2808`). So the harness builds the old caller outside the
checkout, with `git archive <commit> <path> | tar -x -C <temp dir>`. That also avoids `git worktree add`, which
writes to the repository's `.git` and may be refused inside Codex's `workspace-write` sandbox (I have not tested
that).

Put the reading of the record file inside the project's harness script, so the check in `DONE.json` stays a
short command with no `jq` quoting inside JSON, which is the commonest way a check breaks
(`plan-module/SKILL.md:223-226`).

Where the projects allow it, a cheaper form of the same check is the old caller's own contract tests run against
the new provider, as consumer-driven contract tools such as Pact do. The harness can do either; the item says what
is observed, and the builder chooses how (`done-when.md:350-352`).

Keep these checks out of the `Check:` line. Step 3 makes them false on purpose.

If the project doesn't control deploy order, step 2 gets the mirror-image item: the new caller still works
against the provider's release from before step 1. Otherwise the planner writes the deploy order in the
interface entry. I am not sure the mirror item earns its place as default guidance; I would leave it as one
sentence.

### Rejected alternatives

- **The script enforces the split.** It can't tell whether a change breaks a caller, so it would enforce a
  format, not the property.
- **The script tracks deployment.** Out of scope for a set whose Done is "merged and checked", and deploying is
  the owner's.
- **An environment variable from the script naming the "previous" commit for checks.** Considered, because it
  would hide the record format. Rejected for now, because every candidate the script knows (the base, the last
  accepted commit of the module) is a merge, not a release, and the documented record field gives the same
  thing with no code. Revisit if the record format changes, with a read-only `agent_loop.py commit ORDERS:M3`.
- **A coined name** ("compat milestone", "flow module"). The guidance says what each thing is in plain words.

## Exact changes

No script change and no test change.

| File | Where | Change |
|---|---|---|
| `plan-module/SKILL.md` | "The whole project", after line 106 | New paragraph: behaviour across modules (text A) |
| `plan-module/SKILL.md` | lines 108-109 | Extend the interface paragraph with the three milestones (text B) |
| `plan-module/references/done-when.md` | "What makes a good item", after line 364 | New paragraph: the compatibility item (text C) |
| `plan-module/references/done-when.md` | "The record file", line 265 | Add: the commit is kept under `milestones.<id>.accepted.commit`, which a check may read. This makes the field a promise, so a later format change has to keep it |
| `plan-module/references/profile.md` | template, after `Purpose` (line 23) | The `Older versions` line above |
| `plan-module/references/profile.md` | targets example, line 57 | A `system` row: every module together; Run `docker compose up --wait`; Capture every service's logs and the test transcript; edge conditions such as one service restarted mid-journey, a slow downstream |
| `plan-module/references/proofs.md` | "Kinds to start from" table, line 54 | Row: Compatibility, `check`. What to write: which release of the other side, how it is found, and what runs against the new side. Too weak if: the "old" side was rebuilt from the tip, or it ran the new version against itself |
| `review-milestone/SKILL.md` | line 53 | In the list of Must Fix outside the items, after "breaks the design or an interface": "or, when the project settings say older versions stay in use, breaks a caller still running one" |
| `build-milestone/SKILL.md` | line 133-134 | The proposal says whether a caller on an older version would break. That one fact is what the planner needs to choose one step or three |
| `GLOSSARY.md` | after Interface (line 81) | **Previous release**: the version of a module that is still running somewhere after a newer one is merged. The `Older versions` line says how to find it |
| `README.md` | "Left out for now", line 558 | Add: knowing what is deployed; a milestone that belongs to several modules. Say Done is merged, and that the `attended` item on a removal is where deployment meets the plan |

### Text A, for `plan-module/SKILL.md` "The whole project"

> Behaviour that runs through several modules, such as an order that is paid for and then confirmed by email,
> gets a module of its own, even though it owns no state. Without one, nobody writes the items for the whole
> journey, and no reviewer runs the modules together. That module owns the journey's tests and whatever runs the
> modules together, such as a compose file, and its milestones `need` the milestones that deliver each step. Its
> builder changes no other module: when a step fails, it ends `BLOCKED` naming the module that owns that step.
> Once a journey passes, add its test to the `Check:` line, so a later change to any step can't merge while it
> breaks the journey.

### Text B, extending `plan-module/SKILL.md:108-109`

> If the project settings have an `Older versions` line, a merged change is not running everywhere at once.
> Services roll out one at a time, and a library's users upgrade when they choose. So settle a change that would
> break an older caller as three milestones joined by `needs`: the providing module adds the new shape and keeps
> the old one working; each calling module moves to the new shape; then the providing module removes the old
> shape. Give the removal an `attended` item in which the owner confirms that nothing running still uses the old
> shape, because the script knows what is merged, not what is deployed. Name both shapes in the interface's entry,
> and the milestone that removes the old one. A database change inside one module takes the same three steps.

### Text C, for `done-when.md` "What makes a good item"

> When the project settings have an `Older versions` line, the milestone that adds a new shape to an interface
> gets an item that each caller's previous release still works against it, proved by a `check`. The previous
> release is the one the `Older versions` line says how to find. Failing that, it is the commit at which the
> caller's last milestone before the change was accepted, kept in that module's record file under
> `milestones.<id>.accepted.commit`; put that milestone in `needs`. Build the old release outside the checkout,
> because a check that leaves files there fails. Keep these checks out of the `Check:` line, because removing the
> old shape makes them false on purpose.

## Worked example

Modules: ORDERS, PAYMENTS, NOTIFY, and CHECKOUT, which owns the journey and the harness. Settings:
`Older versions: services deploy one at a time; a service's running version is its newest tag <module>-v*`.

CHECKOUT's first milestone, which every compatibility check later depends on:

```json
{ "id": "M1", "name": "A placed order is paid for and the customer gets a confirmation email",
  "needs": ["ORDERS:M3", "PAYMENTS:M3", "NOTIFY:M2"],
  "items": [
    { "id": "M1.1", "statement": "A placed order is charged once and its confirmation email arrives within 30 s",
      "check": "scripts/system test e2e/checkout", "target": "system" },
    { "id": "M1.2", "statement": "The harness runs any one service at an older release while the rest run the tip",
      "check": "scripts/system compat --self-test", "target": "system",
      "ask": "Does e2e/checkout fail if the email is never sent, or is sent twice?" } ] }
```

A PAYMENTS builder needs `amount_cents` to become `amount` plus `currency`, and writes a proposal in
`PAYMENTS/LOG.md` saying ORDERS on an older release would break. The planner settles it as three milestones:

```json
{ "id": "M4", "name": "Payments accept a currency, and orders already running keep working",
  "needs": ["CHECKOUT:M1", "ORDERS:M3"],
  "items": [
    { "id": "M4.1", "statement": "A charge with amount and currency succeeds in EUR and USD",
      "check": "npm test -w payments -- charge-currency" },
    { "id": "M4.2", "statement": "ORDERS at its running release still places and pays for an order against this PAYMENTS",
      "check": "scripts/system compat ORDERS e2e/checkout", "target": "system" } ] }
```

`scripts/system compat ORDERS` takes the newest `orders-v*` tag, or, with no tag, ORDERS M3's
`accepted.commit` from `docs/plans/ORDERS/ACCEPTED.json`, extracts ORDERS at that commit with `git archive` into
a temporary folder, and runs the journey with every other service at the tip.

```json
{ "id": "M5", "name": "Orders are charged in the customer's currency", "needs": ["PAYMENTS:M4"], "items": ["…"] }
```
in ORDERS, then in PAYMENTS:

```json
{ "id": "M6", "name": "Payments accept only charges with a currency", "needs": ["ORDERS:M5"],
  "items": [
    { "id": "M6.1", "statement": "A charge with amount_cents alone is refused with a 400 naming the new fields",
      "check": "npm test -w payments -- charge-legacy-refused" },
    { "id": "M6.2", "statement": "No running ORDERS release sends amount_cents",
      "attended": "The owner confirms every ORDERS instance runs orders-v2.4 or later" } ] }
```

The interface entry in `ARCHITECTURE.md` reads: "PAYMENTS charge: accepts `amount_cents` (old) and
`amount` + `currency` (new) from PAYMENTS M4; the old shape is removed by PAYMENTS M6." M6 is the last milestone
in PAYMENTS's plan, because its `attended` item holds back every later PAYMENTS milestone
(`plan-module/SKILL.md:188-191`).

The library version of the same example: the `Older versions` line says "users pin releases; the previous release
is the newest v* tag"; M4 deprecates the old function and its check runs the previous release's public test suite
against the new library; M6 removes it, and its `attended` item is the owner choosing to cut a major release.

## What I am unsure about

- **The set's own rule for adding lines.** The domain spec says to add a line only for a failure that has been
  seen (`.agents/skills/orchestration-skill/SKILL.md`), and `plan-module/SKILL.md:131` says each rule is there
  because a plan without it went wrong. These came from an assessment, not a failed run. The `Older versions`
  gate keeps the cost off other projects, but the honest course may be to run one microservice project first and
  add only what it shows is missing. Text A in particular has no test run behind it.
- **Running the whole system as a reviewer.** Whether Docker, or several services on ports, work inside Codex's
  `workspace-write` sandbox. I expect not, in which case the same remedy as for browsers applies
  (`plan-module/SKILL.md:195-202`): a Claude reviewer, or `danger-full-access` as the owner's decision.
- **Cost of the journey test on every merge.** Adding it to `Check:` runs the whole system before every merge of
  every module. For a large system that may be too slow, and a smoke subset may be the right thing to add.
- **The record field as a promise.** `accepted.commit` is absent for work adopted before the record file existed
  (`agent_loop.py:1246`), so the harness needs a tag or an explicit commit in that case. Documenting the field ties
  the record format; that is the price of having no script change.
- **The mirror item on step 2** (new caller against the old provider). Only needed when deploy order isn't
  controlled; I would mention it in one sentence, not make it a rule.
- **`git archive` and monorepo builds.** An old service extracted alone may not build if it depends on shared
  code elsewhere in the repository at that commit; the harness may need to extract the shared folders too. That is
  the harness builder's detail, but it may make the first compatibility milestone larger than it looks.
