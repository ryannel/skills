# Orchestrate V2: what it is and how to build it

11 November 2026. Replaces the production-driving design in [V2-DESIGN.md](V2-DESIGN.md), which the owner judged a
step too far: agents should not deploy to production. Much of that design's planning and verification thinking
carries over; its delivery machinery does not.

## 1. The idea

Agents build the whole change ahead, at full speed, as if it were one big-bang build. But the change is planned from
the start as an **ordered list of small releases**, each safe to deploy while production is still running the
releases before it. Agents prove the finished system locally, and prove that each release in the list is safe at its
point in the order. They then hand people a **deployment plan**. People deploy the releases one at a time, at their
own pace. The code for every release is already written, reviewed and waiting.

Building and deploying run on separate clocks. Agents never wait for production, and never touch it.

What makes this work is that the release order is decided **before** building. Code built as one finished piece
rarely splits into safe releases afterwards: one commit adds the new field and drops the old one, and there is no
safe point in between. So the planner designs the end state and the path to it together, and builders build the
path.

## 2. The terms

Each is defined before it is used. V1's words are kept where the meaning holds.

- **Module.** As in V1: a part one builder can work on alone, with exactly one module in charge of each kind of
  state. New: a module names the **repository** (and folder) it lives in. Several modules may share one repository.
- **Home repository.** The repository that holds the plans, the records and the status page. For a one-repository
  project it is that repository, with plans in `docs/plans/` as now. For several repositories it is a separate
  repository holding no product code.
- **Contract.** What one module provides to others (an HTTP API, an event, a table another module reads), kept as a
  file a tool can compare: an OpenAPI file, a `.proto`, a JSON schema. V1's "interface", made checkable.
- **Change.** One thing the owner asked for. It has a brief, a plan and a record. It replaces V1's project as the
  unit that is planned: a production system is never finished, and the owner follows each request.
- **Step.** One piece of work in one module, built by one builder, with done-when items. V1's milestone, renamed
  because it now belongs to a change, not a module.
- **Release.** A group of finished steps that people deploy together, in its place in the change's **release
  order**. By default a release changes one module. Two releases that don't depend on each other can be marked as
  deployable in either order.
- **Release point.** The state of the whole system after releases 1 to *k* are deployed and nothing later: each
  module at the commit its latest release left it at.
- **Deploy condition.** Something that must be true in production before a release is deployed, which only people
  can confirm: "release 1 is live", or "nobody has used the old field for 30 days".
- **Held step.** A step whose release has a deploy condition that would make it unsafe to merge early (typically
  removing the old form). It is built, checked and reviewed, then kept on its branch, unmerged, until the condition
  is confirmed.
- **Deployment plan.** The document handed to people: for each release, in order, its deploy conditions, what to
  deploy, the database migrations, the flags it adds (off by default), how to check it worked, and how to undo it.

## 3. The rules

1. **Anything merged to a main branch is safe to deploy at any time.** Someone may deploy main for an unrelated
   fix, and that must never ship a removal early. This is why held steps stay unmerged.
2. **Every release is safe at its release point.** Each release must work while every other module runs at the
   previous release point. The script proves this locally (section 5).
3. **Breaking changes are planned in the order add, move, remove.** The providing module adds the new form and
   keeps the old; each user moves to the new form; the providing module removes the old form. Database changes
   inside a module follow the same order: add the column, write both, backfill, read the new, stop writing the old,
   drop it.
4. **A tool, not the planner, decides whether a change to a contract is breaking.** A breaking diff is allowed only
   in a planned remove step. A "tidy-up" that drops a field fails its checks, whatever the plan called it.
5. **Everything temporary has a step that removes it.** The plan lists each flag, old field and double write with
   the step that removes it, and the script refuses a plan where one has none.
6. **Every release says how it is undone,** and for releases touching data, an item proves locally that the
   previous version still works with data written by the new one.
7. **Agents never deploy, and hold no production access.** People deploy and tell the lead what is live.

## 4. Who does what

| Who | Does |
|---|---|
| **Lead** | Interviews the owner and writes the brief (`interview-me`, kept). Brings decisions to the owner. Records what people report as deployed, and deploy conditions they confirm, in their words. Hands over the deployment plan. |
| **Planner** | Writes the change: the end state, the steps, their items, the release order, deploy conditions, how each release is undone, and what is temporary. Settles contract changes, as in V1. |
| **Builder** | Builds one step in a worktree of its module's repository. As in V1. |
| **Reviewer** | A fresh session that judges a step, or the plan, by using the product. As in V1. |
| **The script** | Starts agents, runs the checks, runs the local proof at each release point, merges, holds and later merges held steps, writes the record, the status page and the deployment plan. |
| **People** | Deploy releases in order. Tell the lead what is live and whether a deploy condition holds. |

The owner still only chats. "Release 2 is live" is a sentence to the lead, who runs `owner live`.

## 5. Proving it locally

This is where V2 has to be strongest, because production no longer checks anything for the agents.

**The system module.** Each project with more than one module that runs as a service has a module that owns how
the modules run together (the idea all three microservice designs reached on 11 November). It holds:

- a start command that brings up every module locally **at a version chosen for each**, from a versions file
  (module → commit), with names taken from the checkout's path and ports chosen by the system, so two copies can run
  at once;
- the tests of flows that cross modules.

In the home repository of a several-repository project, it lives in `system/`.

**Tags for each release point.** When a release's steps are all merged (or, for a held step, Done on its branch),
the script tags each repository: `orchestrate/<change>/R<k>`. A release point is then a versions file the script
can write: each module at its latest tag at or before *k*.

**Checks at every release point.** For each release *k* the script runs, in clean copies:

- each module's own Check at its commit at point *k*;
- the contract comparison: each changed contract against its version at point *k* − 1;
- the cross-module flow tests with the system started at point *k* − 1, then at point *k*. That shows release *k*
  works beside the earlier releases, and that the system still works once it is in;
- for releases marked as deployable in either order, the flow tests with each of them alone on top of the earlier
  point.

The end state is simply the last release point. A release that fails at its point goes back to its builder with the
failure, as a failed check does in V1.

This is the proof that lets agents build everything ahead: compatibility mistakes that a staged rollout would have
caught in production are caught here, before anything ships.

**What this can't prove:** production data shapes, load, timing, third-party behaviour, and old clients nobody
listed. Each release's deployment notes say what to check in production for exactly these reasons.

## 6. Held steps and deployment

- A held step is built, checked at its release point and reviewed like any other, and is Done on its branch. It
  shows on the status page as "Ready, waiting for: release 3 live; old field unused for 30 days".
- People deploy releases and tell the lead. The lead records it with `owner live <change> R<k>` and each confirmed
  condition with `owner confirm`. Where a module has a read-only command that reports its running version, the
  script also checks the claim and says if it disagrees; it never needs production access beyond that.
- When every condition of a held step is confirmed, the script rebases it onto its main branch, runs its checks and
  its release point again, and merges it. The release is then ready to deploy.
- A problem found in production after later releases are built is fed back as a failed review of the release that
  caused it. Later steps that depended on it are re-checked at their release points, and rebuilt where they fail.
  This is the cost of building ahead. Small releases keep it small.

**The deployment plan** is written by the script from the plan and the record, not by an agent, at
`changes/<id>/DEPLOY.md`. For each release: its conditions, the exact commits or tags per repository, migrations,
flags, the planner's notes on what to check in production, and how to undo it. The status page shows two progress
lines per change: built and proven, and deployed.

## 7. What changes from V1

| | V1 | V2 |
|---|---|---|
| Unit the owner follows | Project, with modules and milestones | Change, with steps and releases |
| Repositories | One | One or several; plans in the home repository |
| Order of work | `needs` between milestones | Kept, plus the release order |
| What Done means for a step | Merged, checks pass, reviewed if needed | The same, plus: passes at its release point. Held steps are Done unmerged |
| Proof across modules | Each milestone's own items | Flow tests at every release point |
| Contracts | Interfaces in prose | Files a tool compares |
| Output | Merged code | Merged code, held steps, and a deployment plan |
| Production | Out of scope | Still never touched; planned for |

**Kept unchanged:** the interview and brief; the glossary; items written before building that the builder can't
change; the script as the only writer of the record; the fresh reviewer who uses the product; the escalation stages
after failed reviews; 2–4 builders, one per module; both hosts.

**Not in V2:** agents deploying, flags raised by agents, monitoring gates, health queries, a timer that drives
production, receipts from production systems. They are V2-DESIGN.md's territory if a later version ever needs them.

**Recommended, separately from V2:** the assessment's lighter changes (review by risk; a reviewer that writes nothing
and returns a verdict; the lead's result table moved into the script). They help V2 but don't depend on it, and
should be judged on their own.

## 8. How to build it

Built on a branch `orchestrate-2.0`, from main at the time. Each phase ends with something that works and is proven
on the fixture, so the work can stop after any phase with value kept. Each phase is a separate set of commits with
tests in `tests/orchestration/`.

### Phase 0: the fixture and a baseline (before any V2 code)

- Build `fixtures/orchestrate-v2/`: three tiny services in three repositories (`payments`, `orders`, `billing`) plus
  a home repository, each a few hundred lines, with OpenAPI contracts, a compose-based local start, and seed data.
  Plant three traps: an unlisted reader of the field being removed (a nightly export in `orders`), a migration whose
  old code can't read new rows, and a double conversion in `billing`.
- Write the change request: "amounts in whole pence, not decimals", the same worked example as before.
- **Baseline:** one strong agent (Opus 5.5, high) is given the request, the repositories and a done-when file, and
  asked for the code plus a deployment plan. Record what it caught, what it cost and how long it took. V2 must beat
  this to earn its weight.

Done when: the fixture starts locally at any combination of versions, and the baseline result is written down.

### Phase 1: the plan format and planner guidance

- Extend the done-when format: a step gains `release` and `held_until` (deploy conditions); each release gains
  `undo`, `deploy_notes` and `check_in_production`; the change gains `temporary` (each temporary thing and the step
  that removes it). Schema and validation in the script; `plan` refuses a plan that breaks rules 3 to 6 where they can
  be checked mechanically.
- `plan-module`: a new section on release order (add, move, remove; database steps; events: which side upgrades
  first, and replaying old messages through the new reader), and on choosing what to hold. Kept short, and marked as
  untested until Phase 6.
- Contract comparison: a `Contracts` line in the settings naming the compare command per contract kind (`oasdiff`,
  `buf breaking`, a JSON-schema diff), run as an Automated Check the script adds to any step that changes a contract
  file.

Done when: a planner, given the fixture's brief, writes a valid change whose release order is right, and the script
rejects three hand-made broken plans (a removal with no hold, a temporary flag with no removing step, a breaking
diff in a non-remove step).

### Phase 2: several repositories

- Settings: each module names its repository (a path or a URL) and its own Check and Integrate lines. The home
  repository holds `ORCHESTRATE.md`, the plans, records and status.
- The script makes worktrees in the module's repository, runs `land` against that repository's main branch under a
  lock per repository, and writes records only in the home repository.
- `needs` and `status` work across repositories, reading records from the home repository only.
- A one-repository project sees no change: every module's repository defaults to the home repository.

Done when: on the fixture, three builders in three repositories each land a step, the status page shows all three,
a `needs` across repositories holds a step back correctly, and V1's test suite still passes.

### Phase 3: release points and the local proof

- Tags per release point, and the versions file the script writes for a point.
- The system module's start command takes a versions file. The script builds each module at its commit in a clean
  copy (cached by commit), starts the system at points *k* − 1 and *k*, and runs the flow tests.
- Wired into `run`: a step isn't Done until its release passes at its point.

Done when: on the fixture, the migration trap fails at its release point (old code can't read new rows) and passes
once fixed, and the unlisted-reader trap fails at the point of the remove step.

### Phase 4: held steps and what people report

- Held steps: Done on their branch, shown as waiting; `owner live` and `owner confirm` record what people say; the
  script then rebases, re-runs checks and the release point, and merges.
- Optional read-only `Running version` command per module, compared with what people reported.
- Feedback from production: `owner problem <change> R<k> --text` sends the release back as a failed review and
  re-checks every later release point.

Done when: on the fixture, the remove step stays unmerged through a deploy of main, merges after both conditions
are confirmed, and a reported problem in release 2 re-checks releases 3 to 5.

### Phase 5: the deployment plan and the status page

- `DEPLOY.md` generated per change from the plan and record.
- Status: built-and-proven and deployed, per change and per release; what each held step waits for.
- `report` gains the deployment plan's summary.

Done when: a person who has not seen the build can deploy the fixture's releases in order from `DEPLOY.md` alone.
Test this with a fresh agent playing that person, given only `DEPLOY.md` and shell access to the fixture.

### Phase 6: the trial against the baseline

Run the whole fixture change through V2 with the lead in a chat, as the owner would. Compare with Phase 0's
baseline: traps caught, the number and size of releases, the owner's decisions, tokens and time. Then decide, from
the numbers, whether V2 ships as orchestrate 2.0, and which planner guidance has earned its place.

### After that

- Migration: a `migrate` path that turns a V1 project's open milestones into steps of one change, each module's
  remaining milestones becoming releases in their current order.
- Docs: README, glossary (change, step, release, release point, deploy condition, held step, deployment plan,
  contract, home repository), `build/SKILL.md`, `plan-module`, `build-milestone` (renamed `build-step` if the trial
  keeps the word), `review-milestone`.
- Publish: version 2.0.0 in `marketplace.json` and `package.json`; Thrum moves across only when its owner chooses.

## 9. Open questions

1. **One module per release.** It makes every release point simple to test, but a change touching five modules
   becomes at least five releases. Is grouping independent releases enough, or do people want bigger releases?
2. **Where the script's new code goes.** `agent_loop.py` is 7,243 lines in one file. Release points, several
   repositories and the deployment plan are natural separate files, if the install script copies the folder.
3. **Building many versions locally** may be slow for real services. Caching by commit helps; the fixture will show
   whether it is enough.
4. **Steps that build on a held step.** Rare if removals come last, as the planner is told; otherwise they need
   stacked branches, which agents handle badly. The plan should refuse it until a trial shows a need.
5. **How long a held step can wait** before its rebase becomes real work. The script re-runs everything on merge,
   so it is safe, but it may cost a builder session.
6. **Whether "a person says it is live" is enough.** The read-only running-version command makes it checkable where
   it exists; elsewhere the record says the fact came from a person.
