# Review of BUILD-PLAN.md (orchestrate V2)

11 November 2026. Reviewed against `skills/orchestration/` as published (orchestrate 1.7.1), chiefly
`build/scripts/agent_loop.py`. Line numbers are in that file unless another is named. The owner's direction (agents
never deploy; build ahead; ordered small releases; people deploy at their own pace) is taken as settled.

## Verdict

The idea in section 1 is right, and deciding the release order before building is the part most worth keeping. The
plan as written does not yet deliver its own rule 1, its local proof tests less than section 5 claims, and the build
phases leave out the two largest pieces of work: the change-and-step data model, and a builder that works in two
repositories at once. I would not start Phase 1 until the six design holes below are answered on paper, because
three of them change what Phases 2 to 4 build.

Terms used here, beyond the plan's own:

- **Live point.** The release point people have most recently reported as deployed.
- **Module head.** The newest commit on the main branch that touches a module.

---

## 1. Does the design hold?

### 1.1 Rule 1 is not achieved by holding only removals

Rule 1 says anything merged to a main branch is safe to deploy at any time. The plan holds a step only when it
removes an old form. But a step can be unsafe to deploy early for three other reasons, and each of these is merged
under the plan.

**A user moves before the provider has added.** Releases: R1 `payments` adds `amount_pence`; R2 `orders` reads
`amount_pence`; R3 `billing` reads it; R4 `payments` removes `amount`. Agents build all four on day one. R1, R2 and
R3 are merged; R4 is held. Production runs none of them. Someone deploys `orders` main for an unrelated fix. `orders`
now reads a field that production `payments` does not send. The plan's own example of a deploy condition, "release 1
is live", is exactly this case, yet only removals are held.

**A later release of the same module is merged on top of an earlier one.** Module `payments`: R1 add column, R2 write
both, R3 backfill (people run it), R4 read the new column. All merged. Production is at R1. Someone deploys `payments`
main: R4's code reads a column the backfill has not filled. There is no removal anywhere in that sequence.

**People cannot deploy a single release at all once later ones are merged**, unless they deploy by tag. If they
deploy by tag, then the next unrelated fix has no place to go: it lands on main above R2 to R4, and deploying it
ships them all.

So rule 1, applied honestly, makes almost every step after the first of a change a held step. Held is the common
case, not the exception, and section 9's question 4 ("steps that build on a held step, rare") is the normal case.
The design has to be built around that. Two ways out, and the plan must choose one:

- **(a) Every release sits on its own unmerged branch, stacked in release order, and the script moves the next one
  to main when people report the one before it live.** The script rebases the stack; agents never do. Main then
  always equals "what is live, plus at most the next release", which is the only state in which rule 1 is true
  without conditions. "Held step" stops being a separate concept: every release waits its turn. Cost: a long-lived
  stack that must be rebased whenever other people change main. The plan already pays that cost for held steps
  (question 5), and (a) pays it for the whole tail.
- **(b) Keep merging early, but require every merged step to be inert until switched on**: a flag that is off by
  default, or a reader that accepts both forms. Then the proof must run each release point with flags off and on,
  and the plan must say who turns a flag on (people) and that a release point includes flag states. The plan
  mentions flags only as a line in the deployment plan.

I recommend (a). It maps onto the real code better too (see 2.4), and it lets the script decide what waits by a rule
rather than by the planner's judgement of what is "unsafe to merge early".

### 1.2 A release that fails after later ones are built cannot be fixed in place

Section 6: a production problem "is fed back as a failed review of the release that caused it", and a release that
fails its point "goes back to its builder". Main is linear. State: `payments` R1 and R4-prep are both merged; R2
(`orders`) then fails at its point because of a defect in R1. The fix to R1 lands above R4-prep. There is no commit
that is "R1, fixed, without the later work", so the tag `orchestrate/<change>/R1` has nowhere correct to move, and
people cannot deploy the fix without everything after it in that module. Option (a) above solves this (rebase the
stack from the fixed release up; nothing above it is on main). Under the plan as written the only honest answer is
"a fix is a new release appended to the order", and that should be stated, with what it does to the releases already
handed to people in `DEPLOY.md`.

### 1.3 Steps are merged before their release point is checked

Section 5 tags a release "when a release's steps are all merged" and then runs the point checks. So code that fails
its release point is already on main, and rule 1 is broken for however long the fix takes. The point check has to
run on the candidate commit before the merge, which means `land` (2602) must be able to start the system with one
module at an unmerged commit. That is a Phase 3 capability Phase 2's `land` needs.

### 1.4 Points k − 1 and k do not prove what section 5 says they prove

With one module per release, "point k" is the mixed state (module M new, the rest old), so checking across modules
is sound. What the two clean starts miss:

| Situation in production | Why two clean starts miss it | What would catch it |
|---|---|---|
| Rolling deploy: old and new copies of **one module** share a database and both take traffic | The versions file holds one commit per module, so the local system never runs two copies of a module | Start module M at k − 1 and at k together against one database, after M's migration at k has run |
| Data written before the release | Each point starts in a clean copy from seed data, so release k never meets rows, queue messages or cache entries written by k − 1 code | Keep the data: start at k − 1, run the flows, upgrade in place, run the flows again |
| Undo of release k | Only covered by rule 6's item, which the planner writes and only "for releases touching data" | After the step above, put module M back to k − 1 code on the data k wrote, and run the flows |
| Undo of release k after k + 1 is live | State {1..k − 1, k + 1} is never started | Either test it or have `DEPLOY.md` say "undo in reverse order only" for each pair |
| A release skipped, or deployed out of order | Only pairs the planner marked "either order" are tested, each alone. Three such releases have six two-at-a-time states; none is run | State in `DEPLOY.md` that order is a hard condition, and make the running-version check (section 6) required for it, or test every subset of a marked group |
| Someone deploys a module's main ahead of the plan (1.1) | Not a release point | Start each module head against the others at the live point |
| A browser tab or mobile client loaded at point k − 2 | Clients are not modules in the versions file | List client bundles as modules, or make "old clients gone" a deploy condition by default for any removal on a public contract |
| The meaning of a field changes but its shape does not (decimal pounds to integer pence in a field still called `amount`) | The contract comparison sees no difference; this is the fixture's own third trap | Rule 3 must forbid changing meaning in place: a new meaning always takes a new name |

The first three rows are one mechanism, and it should replace the pair of clean starts: **one walk through the
release order on data that is kept**. For each k: run the flows at k − 1 so data exists, bring module M to k (run
its migration, with the old copy still running), run the flows, stop the new copy and run the flows on the old one
(the undo), then finish the move to k. It costs fewer starts than the plan's scheme, and it makes rule 6 a thing the
script does for every release rather than an item a planner must remember to write.

### 1.5 Which flow tests run at which point is not defined

The flow tests live in the system module. A test of the end state ("totals are in pence") fails at point 1, where
nothing has changed yet. A test of the start state fails at the last point. Section 5 does not say which tests apply
at which points, who writes them, or when. Without that the proof either fails wrongly or is trimmed to the tests
that happen to pass everywhere, and those are the tests that prove least. Each flow test needs the range of release
points it must hold at, written by the planner before building, and the builder must not be able to narrow it (the
same rule as V1's items, `delta_problems`, 1187).

A related order problem: the flow tests are the system module's steps, and the first release point check needs them
to exist. So the system module's first step must be Done before any other step can be Done. The plan does not say so.

### 1.6 The contract file is trusted, not proven

Rule 4 lets a tool decide whether a contract change is breaking. Nothing proves the OpenAPI file describes what the
service does. A builder who changes a handler and leaves the file alone passes the comparison. That is "depends on
an agent saying so" by another route. Either the contract file is generated from the code by a command the script
runs, or a provider check (the running service validated against its contract file) is a required Automated Check
on every module with a contract. Also unnamed: the compare tool for "a table another module reads".

### 1.7 The unlisted reader is caught only if a test happens to use it

Phase 3 is done when "the unlisted-reader trap fails at the point of the remove step". It fails only if some flow
test runs the nightly export. Nobody listed that reader, so who wrote its test? If the fixture ships one, the trap
is rigged in V2's favour and the baseline agent gets the same test. Real protection against unlisted readers is the
deploy condition ("nobody has used the old field for 30 days", confirmed by people from production logs), and a
search of every repository for the old name before the remove step. Say that plainly, and score the trap on
whether the **plan** contains that condition, not on a test.

### 1.8 When people deploy something agents did not plan

The plan has no answer for these, and each will happen:

- **A human hotfix lands on main above a release tag.** Tags are fixed commits. `DEPLOY.md` now names commits that
  lack the hotfix. The script must notice that main has moved in a module with undeployed releases, re-run the
  affected points, and rewrite `DEPLOY.md`. Under the plan nothing triggers this.
- **People report a state that is not a release point** ("we deployed `orders` main yesterday"). `owner live
  <change> R<k>` cannot express it. The record needs "module M is running commit C", from which the script works
  out which point that is, or says it is none and what was never tested.
- **Two changes in flight touch one module.** V1 runs a module's milestones strictly in order: `next_step` (1382)
  returns the first milestone that is not accepted and goes no further. A step held for 30 days stops every later
  step of that module, including those of an unrelated change. Section 2 makes the change the planned unit but never
  says how two changes share a module, a main branch or a release order.
- **People undo a release.** There is no `owner undone`. The live point moves backward, and held steps whose
  conditions were confirmed may already have merged.

---

## 2. Is the build plan feasible against the real code?

### 2.1 The largest piece of work is in no phase: the change-and-step data model

Section 2 says a step "belongs to a change, not a module", and section 6 writes `changes/<id>/DEPLOY.md`. Phase 1
then describes the format change as "a step gains `release` and `held_until`", as though a step were still a
milestone in `docs/plans/<MODULE>/DONE.json`. It is one or the other. Everything in the script is keyed by module:

- module discovery is "every folder under the plans folder holding `DONE.json`" (`module_of` 882, `modules_here`
  899, `modules_at` 907);
- `project` (1321) builds `{MODULE: {doc, record, design}}`; `next_step` (1382) walks one module's milestones in
  file order; `need_cycles` (1350) adds an edge from each milestone to the one before it in its module;
- `needs_review` (1113) says the **last milestone of a module** always gets a reviewer. With changes there is no
  last milestone of a module; a module is never finished;
- the record file, the run lock (`run_lock` 2091), the claim refs (`take_claim` 2736, `refs/orchestrate/claims/
  <MODULE>/<id>`), the verify checkout (`verify_tree` 2562) and the status page (`status_page` 6390) are all one
  per module;
- the design review is one per module, against a hash of `DESIGN.md` (`design_ok` 1312). A change that touches a
  module changes its design, which under V1 rules sends the whole module back to Design Ready for Review and
  stops every step in it, for every change.

Moving the planned unit from module to change touches most of the 7,243 lines and most of the 304 tests in
`tests/orchestration/`. The plan puts migration and the rename under "After that". This cannot come after: Phases
1, 4 and 5 all read and write the new shape.

**Cheaper alternative:** keep V1's files exactly. A step stays a milestone in its module's `DONE.json`, with three
added optional fields (`change`, `release`, and the conditions). A change is a small file listing its releases in
order. "Change" is then a label and a view on the status page, not a new container. Decide this before Phase 1.

### 2.2 Phase 2 (several repositories) is underestimated by a wide margin

The script assumes, everywhere, that one working copy holds the settings, the plan, the record and the code:

- `profile` reads `ORCHESTRATE.md` from the worktree it is given (500). A worktree of `payments` has none.
- `cmd_run` loads the done-when file from the builder's worktree (4474, 4609), and the builder itself edits
  `state`, `status` and `evidence` there (`BUILDER_FIELDS` 1182) and merges that with its code. With plans in the
  home repository, the builder must write to two repositories in one step.
- `claim_problems` (2786 to 2825) does eight things with one `worktree` and one `ref`: a clean working copy, HEAD
  merged into the main branch, no tampering with records between two tips, the items at the tip matching the
  approved hash, a clean checkout at the tip, the checks, and no leftovers. Half of those are about the home
  repository and half about the code repository. Each needs splitting.
- `verify_tree` (2562) makes its clean checkout with `git worktree add` from the given repository, stored under
  that repository's git folder (`loop_dir` 723). The per-run state file, the run locks and the record of live runs
  hang off the same folder.
- `review_once` reads the done-when file **at the reviewed commit** (4823) and requires that commit to be on the
  main branch (4822). In V2 the code commit and the done-when file are in different repositories.
- Writes to the record and to the code stop being one commit. `cmd_run` 4634 to 4658 already handles "the claim
  held but couldn't be recorded", so this is survivable, but every `loop_write` (2648) call site needs the same
  care.
- Codex's sandbox is `workspace-write` on one worktree (421); a second repository needs `Writable roots`, and
  V1's own settings template gives "never modify ../other-repo" as its example of a path not to touch
  (`plan-module/references/profile.md:63`).

One thing is easier than the plan suggests: the integrate lock is already one per repository, because `held` (2054)
keeps its lock file in the repository's git folder. "A lock per repository" needs no new code.

The plan's own "Recommended, separately" list (a reviewer that writes nothing and returns a verdict) is in fact a
precondition here. If builders and reviewers write nothing in the home repository, and hand `status`, `evidence`
and verdicts to the script as its return values, most of the two-repository problem disappears. Do that first, on
V1, as its own release.

Also missing from Phase 2: who clones the module repositories and where, and that a builder or reviewer proving a
step needs the **other** repositories checked out at the right versions to start the system. That is Phase 3's
machinery, needed by Phase 2's done-when line ("three builders in three repositories each land a step").

### 2.3 Phase order: three dependencies point backward

- **Phase 1 depends on Phase 2.** The automatic contract check is added "to any step that changes a contract file".
  Contract files live in module repositories, which the script cannot reach until Phase 2. And the Phase 1 test
  "the script rejects a breaking diff in a non-remove step" needs a built step, not a plan: it is a `run`-time
  check filed under plan validation.
- **Phase 3 depends on Phase 4.** Section 5 tags a release point when a held step is "Done on its branch". Tagging
  and checking unmerged work is held-step machinery. Phase 3's second done-when line ("the unlisted-reader trap
  fails at the point of the remove step") is about the held step. Under 1.1, held is the normal case, so Phases 3
  and 4 are one phase.
- **Phase 1's planner guidance depends on Phase 3.** A planner cannot write flow tests with point ranges (1.5), or
  know what the proof will and will not catch, before the proof exists.

### 2.4 Held steps contradict three V1 invariants (Phase 4)

"Done on its branch, unmerged" is one line in the plan. In the code, Done means merged, in three separate places:

- `claim_problems` 2803: `if not is_ancestor(worktree, "HEAD", ref)` refuses any step not on the main branch;
- `review_once` 4822: refuses to review a commit that "isn't on main, so it isn't integrated";
- `accepted` (1303) needs `state == "done"` in the done-when file **at the main branch's tip**, and the builder
  sets that field in the same commits as its code. For a held step in one repository that commit is, by
  definition, not on main, so the status page never sees it as Done.

Each can be changed, but each is a guard V1 added for a reason ("nothing depends on an agent saying so"), and the
plan does not say what replaces it. Under option (a) in 1.1 none of the three needs to change: V1's settings already
have a `Branch` line (421), so agents build onto a per-change branch with `land` exactly as today, the checks at
2803 and 4822 hold against that branch, and the only new command is the one that moves the next release from that
branch to main. That is a far smaller Phase 4.

"The script rebases the held step and merges it" also assumes the rebase is clean. `land` aborts on a conflict
(2615 to 2617) and V1 hands the conflict to the builder's live session. Thirty days later there is no session. The
plan needs to say that a conflicted rebase starts a new builder, that its result is a new commit, and that the
review and the release point no longer cover that commit. Question 5 says "it is safe"; it is safe only if the
review is run again, which the plan does not say.

### 2.5 `land` pushes straight to main

`land` ends with `git push <remote> HEAD:refs/heads/<branch>` (2625). A team running a real distributed web
application will have protected main branches, required reviews and required CI on every repository. V2's whole
delivery path goes through a command those repositories will reject. The brief said V2 should use the CI that
exists. Opening one pull request per release, and treating "merged by a person, CI green" as the event the script
waits for, is the missing integration mode, and it fits the owner's direction well: people then control both the
merge and the deploy.

### 2.6 Smaller points against the code

- **`owner release` already exists** (7173, 6844): it gives up a lead's hold on a milestone. V2 makes "release" its
  central noun. One of them must be renamed before the glossary is written.
- **"Held" is already used**: `held()` is the lock helper (2054) and `next_step` uses `held` for attended items
  (1402). The owner already found "parked" and "claimed" confusing; "held step" beside "blocked", "parked" and
  "waiting" is a fourth word for "not moving". "Waiting for a deploy condition" as a status says it plainly.
- **`check_failures` (2769) runs every command with a 3,600 s limit in one clean checkout.** A release-point proof
  that builds several services at two versions and starts them twice will not fit one check slot; it needs its own
  runner, time limit, lock and cached builds. Phase 3's "wired into `run`" hides this.
- **Local ports and names.** Section 5 wants "two copies at once". V1 allows two to four builders. With the walk in
  1.4, a builder, a reviewer and the script may each have a system running. That is the same disk problem
  `build/SKILL.md:199` records (15 GB of checkouts), multiplied by services.
- **Phase 2's "V1's test suite still passes"** is the right gate, but 4,781 lines of tests assume one repository.
  Budget for the tests, not only the script.
- **`plan` validation for rule 5** ("everything temporary has a step that removes it") can only check what the
  planner chose to list. A flag the planner forgot is invisible. Say that it checks the list, not the code.

---

## 3. Is it the simplest thing that works?

**Cut or merge:**

1. **Held step, as a separate concept.** See 1.1: with every release waiting its turn on a stack the script owns,
   there is one rule and no exceptions. This removes `held_until` as distinct from deploy conditions, question 4 and
   most of question 5.
2. **Change as a container.** See 2.1: a label on milestones plus a release-order file gives the owner the same view
   for a fraction of the rewrite. With it goes the rename of milestone to step, and of `build-milestone`.
3. **Tags per release point.** The versions file for each point can be written straight into the record (module →
   commit). Tags in every repository are a second copy of that fact, need push rights for tags, and go stale when a
   branch is rebased (1.2, 1.8).
4. **Rule 6's item.** Replaced by the walk in 1.4, which does it for every release.
5. **The "either order" marking and its extra test runs.** Start with a strict order. Add this only when a real
   team asks; it multiplies states (1.4) for a convenience.
6. **The `Running version` command.** Either it matters, in which case it should be how the live point is learned,
   or it is optional and the script must work without it. As an optional cross-check it is weight with no guarantee.
   I would make "module M runs commit C" the one fact recorded, typed by the lead from people's words, and add the
   command later.
7. **Phase 5's status changes** fold into whichever phase writes the record; a generated `DEPLOY.md` is the one
   deliverable there.

**A simpler statement of the guarantee.** Replace rules 1 and 2 with one check the script can run: *a module's
commit may reach main only if that module at that commit passes the flow tests beside every other module at the
live point, and beside every other module at its newest commit on main.* That is the literal meaning of "safe to
deploy at any time", it needs no planner judgement about what to hold, and it covers the unplanned deploy in 1.8.
The release order then follows from it rather than being asserted.

**Keep, and do first:** Phase 0. The baseline is the best thing in the plan. Strengthen it (section 4, last item).

---

## 4. What is missing

A team running a real distributed web application would ask for these before trusting the plan:

1. **Pull requests, branch protection and existing CI** (2.5). Today there is no path that works with them.
2. **Database migrations as a first-class thing.** Who runs them, whether they run before or with the deploy,
   whether each is reversible, how long a backfill takes on production-sized tables, and locking. The plan lists
   "the database migrations" as a line in `DEPLOY.md`. Migrations are where staged releases most often fail, and
   local seed data proves nothing about a table with 200 million rows. At the least, each migration should carry a
   stated size assumption that people confirm.
3. **Events and queues.** Phase 1 gives them one clause. Messages already in a queue at deploy time, replays, dead
   letters, and consumers that lag by hours are the event form of "old and new side by side".
4. **Configuration, secrets and infrastructure.** A release that needs a new environment variable, queue, bucket or
   permission fails on deploy with correct code. `DEPLOY.md` needs a "must exist before this release" list, and the
   local system must fail when one is absent rather than supplying a default.
5. **Environments between local and production.** The plan goes from a laptop to production. Most teams have staging.
   The same `owner live` record should work per environment, so the release order is rehearsed in staging first.
6. **Third-party and other teams' services** that the fixture cannot start. What stands in for them locally, and
   who says the stand-in is faithful?
7. **What `DEPLOY.md` is when it is stale.** It is generated once; main moves (1.8). It needs a "valid for these
   commits" header and a check people can run before deploying.
8. **Abandoning a change half deployed.** R1 and R2 live, the owner cancels. Which temporary things are now
   permanent, and which step removes them? Rule 5 assumes the change finishes.
9. **Security of the home repository.** It holds the record that decides what is Done. With several repositories and
   teams, who may push to it? V1's protection is a commit trailer (`record_tampering`, 2703), which is a convention,
   not access control.
10. **Cost.** Every release point runs a full multi-service start, twice, and re-runs after any upstream fix. Phase 0
    should record wall-clock and token cost of the proof alone, because that decides whether small releases are
    affordable.
11. **A fairer baseline.** One strong agent "asked for the code plus a deployment plan" is a weak opponent if it is
    not told the releases must be safe in order. Give the baseline the same rules (section 3) in one prompt, and the
    same local system start. Otherwise Phase 6 measures the prompt, not the machinery. And the fixture's three traps
    are known to whoever writes the planner guidance; hold back a second change request with different traps for
    Phase 6.

---

## 5. Top five changes, ranked

1. **Make rule 1 true before building anything.** Choose between a script-owned stack of unmerged releases promoted
   one at a time (recommended) and inert-until-switched merges with flags as part of the release point. Then restate
   rule 1 as the mechanical check in section 3. As written, a routine deploy of main breaks production in the plan's
   own worked example (1.1), and a failed early release cannot be fixed (1.2).
2. **Replace the two clean starts with one walk through the release order on kept data,** with old and new copies
   of the changing module side by side and an undo at every step (1.4), and give every flow test the range of
   release points it must hold at, fixed before building (1.5).
3. **Do not rebuild the data model. Keep modules and milestones; make change and release labels** (2.1). If the
   owner wants the full change-as-container model, put it in a numbered phase with its own estimate and say which
   V1 tests are rewritten.
4. **Reorder the phases around what the code needs.** First, on V1: builders and reviewers write nothing in the
   plan files, and integration through a pull request (2.2, 2.5). Then several repositories. Then release points and
   waiting releases as one phase. Planner guidance last, once the proof exists to show a planner what it catches.
5. **Add the unplanned cases to the design and the fixture:** a hotfix on main between releases, a reported state
   that is no release point, an undo, two changes on one module, and a stale `DEPLOY.md` (1.8). Each is a sentence
   in the plan today or absent, and each is an ordinary week for the team this is aimed at.
