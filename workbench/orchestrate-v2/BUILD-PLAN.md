# Orchestrate V2: what it is and how to build it

11 November 2026, second draft. The first draft ([BUILD-PLAN-draft1.md](BUILD-PLAN-draft1.md)) was reviewed by Fable
5.2 ([review-of-build-plan.md](review-of-build-plan.md)), which found that it didn't deliver its own main rule, that
its local proof tested less than it claimed, and that its phases left out the two largest pieces of work. This draft
takes the review's five main changes. Section 10 maps each finding to where it is answered. **Nothing here has been
built or run.**

## 1. The idea

Agents build the whole change ahead, at full speed, as if it were one big-bang build. But the change is planned from
the start as an **ordered list of small releases**, each safe to deploy while production still runs the releases
before it. Agents prove that locally, release by release, on a running copy of the system. People deploy one release
at a time, at their own pace. The code for every release is written, proven and waiting.

Building and deploying run on separate clocks. Agents never wait for production, and never touch it.

The release order is decided **before** building, because code built as one finished piece rarely splits into safe
releases afterwards.

## 2. The terms

Each is defined before it is used. V1's words are kept: V2 is built by adding to V1, not by replacing its model.

- **Module.** As in V1: a part one builder can work on alone, with one module in charge of each kind of state. New:
  it names the **repository** (and folder) it lives in, and its own test command and integration settings.
- **Milestone.** As in V1: a piece of one module, built by one builder, with done-when items written before building.
- **Home repository.** Holds the settings, plans, records and status page. For a one-repository project it is that
  repository. For several repositories it is a separate one holding no product code.
- **Contract.** What one module provides to others, kept as a file a tool can compare (an OpenAPI file, a `.proto`, a
  JSON schema, a table's schema). V1's "interface", made checkable.
- **Change.** One thing the owner asked for. It is a **label** on milestones, not a new container: each milestone
  says which change it belongs to, and the change has a brief and a release-order file. Modules and milestones stay
  the units the script runs, so V1's model and tests mostly survive.
- **Release.** One or more milestones of **one module** that people deploy together. Releases of a change are in a
  strict order.
- **Live state.** What people report is running: "module M is running commit C", per environment (staging,
  production). The lead records it from people's words.
- **Release point.** The state of the system just after release *k* is deployed and nothing later: every module at
  the commit the release order says.
- **Change branch.** In each module's repository, the branch where the change's releases are built, in order, on top
  of main. The script owns it. Builders land on it, as V1 builders land on main today.
- **Deploy condition.** Something people must confirm before a release may be deployed, beyond the release before it
  being live: "nobody has used the old field for 30 days".
- **Promotion.** The script moving a module's main forward to the end of its next release, once that release's
  conditions hold and its checks pass against the live state. This is the only way change code reaches main.
- **Deployment notes.** Written by the script when it promotes a release: what to deploy, the migrations, the
  configuration that must exist first, the flags (off by default), what to check after deploying, how to undo it,
  and the commits they are valid for.

## 3. The rules

1. **Main is what people may deploy.** Each module's main holds what is live plus at most the next release. Change
   code reaches main only by promotion. This makes "anything on main is safe to deploy" true without conditions: the
   first draft held only removal steps, and a routine deploy of `orders` main would have shipped a reader of a field
   production `payments` didn't send yet.
2. **A release is promoted only if it passes beside the live state.** The script starts the system with the module
   at the release's commit and every other module at its live commit, on kept data, and runs the flow tests (section
   5). If main moved since the release was built (someone's hotfix), the change branch is rebased first.
3. **Breaking changes go add, move, remove.** The providing module adds the new form and keeps the old; each user
   moves; the providing module removes the old form once its deploy condition holds. Database changes inside a module
   follow the same order. **A new meaning takes a new name**: changing `amount` from pounds to pence in place is
   forbidden, because no tool can see it.
4. **A tool decides whether a contract change is breaking,** and a breaking diff is allowed only in a planned remove
   milestone. The contract file must match the code: it is generated from the code, or a provider check (the running
   service against its file) is an Automated Check on every module with a contract.
5. **Everything temporary has a milestone that removes it.** The script refuses a plan where a flag, an old field or
   a double write has none.
6. **Agents never deploy and hold no production access.** People deploy, and tell the lead what is running.

## 4. Who does what

| Who | Does |
|---|---|
| **Lead** | Interviews the owner and writes the brief (kept). Brings decisions to the owner. Records what people say is running, and deploy conditions they confirm, in their words. Hands over deployment notes. |
| **Planner** | Writes the change: the end state, milestones per module, the release order, each flow test with the release points it must hold at, deploy conditions, what is temporary. |
| **Builder** | Builds one milestone in a worktree of its module's repository, on the change branch. Writes code and opens its pull request or lands; writes nothing in the plan files. |
| **Reviewer** | A fresh session that uses the product and returns a verdict. Writes nothing; the script records it. |
| **The script** | Starts agents; runs checks and the local walk; keeps the change branches; promotes releases; writes records, status and deployment notes. |
| **People** | Deploy what is on main, in order. Tell the lead what is running, and whether a deploy condition holds. |

## 5. Proving it locally: one walk on kept data

The first draft started the system twice per release from seed data. That misses old and new copies of one module
running side by side, data written before a release, and undo. One walk through the release order on kept data
catches all three, for fewer starts.

**The system module** owns how the modules run together: a start command that brings up each module at a commit from
a versions file, with names from the checkout path and ports chosen by the system, so copies can run at once; seed
data; and the flow tests. Its first milestone must be Done before any other milestone can be. In a several-repository
project it lives in the home repository.

**Flow tests carry a range.** Each says the release points it must pass at (`from R2`, `until R3`, or `always`),
written by the planner before building. The builder can't narrow it, by the same rule as V1's items.

**The walk.** For each release *k*, changing module M:

1. With the system at point *k* − 1, run the flow tests, so real data exists: rows, queue messages, cached entries.
2. Run M's migration for *k*. Start M at *k* **beside** the old copy, both on the same database and queues, sharing
   traffic. Run the flow tests. This is a rolling deploy.
3. Stop the new copy and run the flow tests on the old one, against the data the new one wrote. This is the undo.
4. Finish moving M to *k* and run the flow tests at point *k*.

The walk runs when a milestone is claimed (on the change branch, so failing code never reaches main), again at
promotion against the live state, and again from the changed release onwards whenever an earlier release changes.
Releases are undone only in reverse order; deployment notes say so.

**Contracts** are compared at each release against the previous point, and the provider check runs with every
module that has a contract.

**What the walk can't prove,** and what covers it instead:

| Not provable locally | What covers it |
|---|---|
| Readers nobody listed | A search of every repository for the old name before a remove milestone, and a deploy condition that people confirm from production logs |
| Migrations on production-sized tables | Each migration states its size assumption, whether it is reversible, and whether it runs before or with the deploy; people confirm |
| Old clients (browser tabs, mobile apps) | Client bundles listed as modules where possible; otherwise "old clients gone" is a deploy condition for any removal on a public contract |
| Third-party services | A named stand-in in the system module; the owner confirms it is faithful |
| Configuration and infrastructure | Each release lists what must exist before it; the local system fails when one is absent instead of supplying a default |
| Load and timing | Called out in the deployment notes' "check after deploying" |

## 6. When people do things agents didn't plan

- **A hotfix lands on main.** The script notices main moved under a change branch, rebases the branch, re-runs the
  walk from the first affected release, and rewrites any deployment notes not yet deployed. Conflicts go to a builder.
- **An early release needs a fix after later ones are built.** If it isn't promoted yet, the fix goes into that
  release and the script rebases the later releases on top and re-runs the walk from there. If it is already live,
  the fix becomes a new release placed next in the order.
- **People report a state that is no release point** ("we deployed `orders` main yesterday", or one release was
  skipped). The lead records "module M is running commit C". The script works out which point that is, or says it is
  none and which combinations were never tested, and promotes nothing until the live state is a tested point.
- **People undo a release.** The lead records the new running commit. The live point moves back, and nothing later
  is promoted until it is live again.
- **Two changes touch one module.** A module's main holds one next release at a time. The second change's releases
  are ordered after the first's in that module, and its planner plans against the first change's end state.
- **The owner abandons a change halfway.** Releases not yet promoted are dropped. The planner writes a short clean-up
  change for anything temporary in the releases already live.
- **Staging.** Live state is recorded per environment, so people can walk the releases through staging first.

## 7. What changes from V1

| | V1 | V2 |
|---|---|---|
| Repositories | One | One or several, with plans in the home repository |
| Unit the owner follows | Project | Project, with each request a labelled change and its release order |
| Where builders land | Main | The change branch; main moves only by promotion |
| Who writes plan files | Planner, builder, reviewer, script | Planner and script only |
| Integration | Push or fast-forward main | The same, or through pull requests where main is protected |
| Proof across modules | Each milestone's items | The walk, on kept data, at each release |
| Contracts | Interfaces in prose | Files a tool compares, proven against the code |
| Output | Merged code | Code on main one release at a time, with deployment notes |

**Kept unchanged:** the interview and brief, the glossary, items written before building, the script as the only
writer of the record, the fresh reviewer, the escalation stages, 2–4 builders, both hosts.

**Not in V2:** agents deploying, flags raised by agents, monitoring, a timer that drives production.

## 8. How to build it

On a branch `orchestrate-2.0`. Each phase leaves something that works and is useful on its own, so the work can
stop after any phase. Each phase has its tests in `tests/orchestration/`, and V1's tests keep passing throughout.

### Phase 0: the fixture and a fair baseline

- `fixtures/orchestrate-v2/`: three small services in three repositories (`payments`, `orders`, `billing`) and a
  home repository, with OpenAPI contracts, a compose-based start that takes a versions file, seed data, a queue, and
  one migration.
- **Two** change requests with planted traps. The first is used while building V2. The second, with different traps
  that nobody writing V2's guidance has seen, is held back for Phase 6.
- **Baseline:** one strong agent (Opus 5.5, high) gets the same rules (section 3) in one prompt, the same system
  start, the repositories and the first request, and is asked for the code, the release order and the deployment
  notes. Record what it caught, tokens, and time.

Done when the fixture starts at any versions file, and the baseline is recorded.

### Phase 1: on V1, builders and reviewers write nothing in plan files, and pull requests

Useful for V1 projects whether or not V2 continues, and the base the rest needs.

- The builder stops editing `DONE.json`: it reports in a fixed final message, and the script records it. The
  reviewer returns its verdict the same way. This removes V1's checks that each changed only its own fields
  (`delta_problems`, 1187).
- `Integrate: pull request`: `land` opens or updates a pull request and merges through the code host, waiting for
  required checks, instead of pushing to main (`land`, 2625). Branch protection then works.

Done when V1's suite passes with both changes, and one Thrum-shaped fixture milestone runs end to end through a pull
request.

### Phase 2: several repositories

The largest phase. In V1 one worktree holds settings, plans, record and code, and the script relies on that in
`profile` (500), `cmd_run` (4474), `claim_problems` (2786–2825), `verify_tree` (2562) and `review_once` (4822).

- Settings: a `Repository` line per module (a path or URL, defaulting to the home repository), with that module's
  `Check` and `Integrate`.
- The script reads settings, plans and records from the home repository, and makes builder and reviewer worktrees in
  the module's repository. Locks are per repository.
- `needs`, `status` and `report` read records from the home repository only.
- A one-repository project sees no change.

Done when three builders in three fixture repositories each land a milestone, a `needs` across repositories holds one
back correctly, the status page shows all three, and V1's suite passes.

### Phase 3: the system module and the walk

- The release-order file per change: releases in order, each with its module, milestones, deploy conditions and the
  configuration it needs; flow tests with their ranges. The script validates rules 3 to 5 where they are mechanical,
  and that the system module's first milestone comes first.
- The versions file, and the walk of section 5: kept data, side-by-side copies, undo, flow test ranges.
- Contract comparison and the provider check as Automated Checks the script adds to any milestone touching a contract.
- Wired into claiming: a milestone isn't Done until the walk passes at its release.

Done when, on the fixture, the migration trap fails at step 3 of the walk (old code can't read new rows) and passes
once fixed, a meaning changed in place is refused, and a handler changed without its contract fails the provider
check. Record the walk's time and cost per release: this decides whether small releases are affordable.

### Phase 4: change branches, promotion and what people report

- Change branches per module repository; builders land on them (V1's `Branch` setting, pointed at the change branch).
  This keeps V1's guard that a claimed commit must be on the branch (2803) true.
- `owner running <module> <commit> --env production` and `owner confirm <condition>`; promotion by rule 2;
  deployment notes written at promotion with the commits they are valid for. (Not `owner release`, which already
  exists at 7173.)
- The cases in section 6: hotfix rebase, a fix to an early release, a reported state that is no point, undo, two
  changes on one module, abandoning a change.
- Status: per change, how far it is built and proven, and how far it is deployed, per environment.
- Review rule: V1 gives the last milestone of a module a reviewer (`needs_review`, 1113). V2 gives the last milestone
  of each change one too, and a reviewer for any release touching a contract or data.

Done when, on the fixture: a deploy of `orders` main never ships unpromoted work; a hotfix to `payments` main
rebases the change branch and re-walks; a fix to release 1 after releases 2 to 4 are built lands in release 1; a
reported state that is no point blocks promotion and says why; and a fresh agent given only the deployment notes
deploys the releases in order on the fixture.

### Phase 5: planner guidance

Written last, so it can be tested against the walk. In `plan-module`: choosing the release order (add, move, remove;
database steps; events: which side upgrades first, messages in flight); writing flow test ranges; deploy conditions;
migrations with size and reversibility; configuration a release needs; what to do about readers nobody listed. Each
rule marked untested until Phase 6 keeps it.

Done when a planner given the fixture's first request writes a release order the script accepts and the walk passes.

### Phase 6: the trial against the baseline

Run the **held-back** request through V2, with the lead in a chat as the owner would. Compare with the baseline on
the same request: traps caught (including whether the plan contains a deploy condition for the unlisted reader, not
only whether a test failed), releases, the owner's decisions, tokens, time. Decide from the numbers whether V2 ships
as 2.0, and which guidance stays.

### After that

- `migrate` for V1 projects: existing modules and milestones carry over unchanged, since V2 keeps them; open work
  becomes a change with its own release order.
- Docs: README, glossary (change, release, live state, release point, change branch, deploy condition, promotion,
  deployment notes, contract, home repository), `build/SKILL.md`, `plan-module`, `build-milestone`,
  `review-milestone`.
- Publish 2.0.0. Thrum moves across only when its owner chooses.

## 9. Open questions

1. **One module per release.** A change touching five modules is at least five releases. Phase 3's cost figures
   decide whether that is affordable.
2. **Where the new code goes.** `agent_loop.py` is 7,243 lines in one file. Several repositories, the walk and
   promotion are natural separate files, if the installer copies the folder.
3. **Long-lived change branches** cost a rebase whenever main moves. The script does it, but conflicts need a builder.
4. **Protecting the home repository.** It decides what is Done. Where the code host allows it, only the script's
   account pushes to its main; V1's commit-trailer check stays as the fallback.
5. **Whether the baseline wins.** If one agent with the rules and the system start does as well, V2 should ship only
   the parts that beat it.

## 10. Where each review finding is answered

| Finding | Answer |
|---|---|
| 1.1 Rule 1 fails when only removals are held | Rule 1: main moves only by promotion; "held step" is gone |
| 1.2 A failed early release can't be fixed in place | Section 6: fixed in place before promotion, appended after |
| 1.3 Code merges before its release point is checked | The walk runs at claim on the change branch; main is untouched until promotion |
| 1.4 Two clean starts miss production states | Section 5's walk on kept data; undo in reverse order only; reported states that are no point block promotion |
| 1.5 Flow tests have no range | Flow tests carry a range the builder can't narrow; the system module comes first |
| 1.6 Contract files are trusted | Rule 4: generated, or proven by a provider check |
| 1.7 The unlisted reader | A search plus a deploy condition; the trial scores the plan, not a test |
| 1.8 Unplanned deploys | Section 6 |
| 2.1 The change-and-step data model | Change is a label; modules and milestones are kept |
| 2.2 Several repositories underestimated | Phase 2 names the functions, and is the largest phase |
| 2.3 Phase order backwards | Reordered: V1 groundwork, repositories, walk, promotion, guidance |
| 2.4 Held steps contradict V1's guards | Builders land on the change branch, so the guards hold |
| 2.5 `land` pushes to main | Phase 1: integration through pull requests |
| 2.6 Name clashes | `owner running` and `owner confirm`; "held" dropped |
| 3 Cuts | Tags, "either order", the optional running-version command, rule 6's item and held steps are gone |
| 4 Missing | Migrations, queues, configuration, staging, third parties, stale notes, abandoning, home repository protection, cost and a fair, held-back baseline: sections 5, 6, 8, 9 |
