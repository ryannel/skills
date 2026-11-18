# Orchestrate V2: merged design

11 November 2026. Merged from two independent drafts written from [BRIEF.md](BRIEF.md), Opus 5.5's
([draft-opus.md](draft-opus.md)) and Fable 5.2's ([draft-fable.md](draft-fable.md)), and from each one's critique of
the other ([critique-of-fable.md](critique-of-fable.md), [critique-of-opus.md](critique-of-opus.md)). Where this file
is short, the drafts have the detail and the citations. **Nothing here has been run.**

## The idea in one paragraph

V1 answers one question well: how do we know work is finished without believing the agent that did it? It writes
down what "finished" means before building, keeps that out of the builder's reach, and has a script and a fresh
reviewer check it. V2 keeps that answer and applies it to more facts. In production, "finished" also means "merged",
"running in production", "every user is on it", "healthy", and "the old way is gone". Each of those is written down
beforehand and read by the script from a system no agent can write to. The owner's request becomes a **change**,
carried out as **steps**, each of which is one small piece that can be released alone and undone alone. The script
moves steps forward on a timer. The lead only talks.

## 1. The terms

Each term is defined before it is used. V1 words are kept wherever the meaning survives.

- **Owner.** The person the system is built for. They only chat, with the lead. Unchanged.
- **Module.** A part of the system with its own code, tests and usually its own release: a service, a front end, a
  worker, a shared library, a database schema, a piece of infrastructure. V1's module, plus five facts: which
  repository and folder it lives in, how it is released, how to read which commit is running, how to tell whether
  it is healthy, and its **risk level** (set by the owner: normal or high; anything that moves money or personal data
  is high). Each kind of state still has exactly one module in charge of it. *(Both drafts' critiques agreed to keep
  "module" rather than Opus's "component", because the owner already knows the word.)*
- **Contract.** A file one module provides that others rely on, in a form a tool can compare: an OpenAPI file, a
  `.proto`, an event schema, a database schema another module reads. Each has one providing module and a list of
  known users. V1's "interface", required to be a file.
- **Home repository.** The one repository that holds the settings, the system description, every plan and every
  record. In a one-repository project it is that repository, in `docs/plans/` as now. Module repositories receive
  only pull requests with code in them.
- **Change.** One thing the owner asked for, such as "charge amounts in whole pence". It has a brief, a plan, a
  record, and an **end condition**: how anyone can tell, in production, that it is finished. It replaces V1's
  project as the unit the owner follows, because a production system is never finished.
- **Step.** One small piece of a change, touching one module, merged alone, released alone, undone alone. It
  replaces the milestone. A step is one of three kinds:
  - a **build step**: a builder writes code and opens one pull request;
  - an **operation step**: the script runs one command from the module's closed list of operations, such as "run
    the backfill job" (a planner can name an operation but never write a new command into a plan);
  - a **watch step**: nobody acts; the script measures something for a stated time, such as "nobody has used the
    old field for 31 days". A watch step holds nothing, so other work on the module carries on.
- **Item.** One thing that must be true before a step is Done. Written by the planner before building, unchanged by
  anyone after approval. V1's three ways of proving one (Automated Check, Reviewer Inspection, Reviewer Question)
  gain a fourth: a **production signal**, a metrics query with a bound, which the script runs.
- **Place.** Where an item is proved: the builder's machine, the module's CI, a preview (a temporary copy of the
  system for one pull request), staging, production. V1's targets, extended. Each module lists the places it has,
  in order; that ordered list is its **path to production**, and the status page shows each step's position on it.
- **Exposure.** How many users a step's new behaviour reaches: none (deployed but off), some (a flag or canary at a
  percentage), or all.
- **Record.** What is true about each step, written only by the script. Every fact names its source (the script
  ran it, CI reported it, an environment reported it, the owner said it), stores the result that was read, and
  keeps the identifier of the CI run, deployment, flag change or query as a **receipt**: a pointer that can be
  fetched again while the outside system still keeps it.
- **Standing permission.** A line in the owner's settings saying "you may do this without asking each time".

**Done** keeps one meaning, as in V1: every item proved, in the place it names, recorded by the script. For a
module that is released, the script adds two items to every build step so the planner never has to: "the merged
commit is running in production for everyone" and "the module stayed healthy for its observation period". A module
with no release gets neither, and its steps are Done when merged, as in V1.

A change is **Finished** when every step is Done, its end condition holds in production, and its **list of things
to remove later** is empty. That list holds everything a step adds that is meant to be temporary: a flag, a field
kept for old callers, a double write. The script refuses a plan in which something on the list has no step that
removes it. That one check is how "the old path is removed" becomes part of finished.

*Why one mechanism and not two.* Opus's draft had items plus a separate fixed list of gates, with the step's kind
choosing which gates apply. Fable showed the failure: a planner labels a removal as an ordinary build step and it
skips the safety gates. With production as one more place where items are proved, there is one rule for Done, and
the path is only how it is displayed.

## 2. Who does what

| Who | Does | Never |
|---|---|---|
| **Lead** (the agent the owner chats with) | Finds out what the owner wants and writes the brief (`interview-me`, kept); keeps the glossary (`domain-language`, kept); brings the owner each decision; records answers in their words | Writes or judges code; merges or releases; decides anything on the owner's list; keeps the build moving (the script does that now) |
| **Planner** | Writes a change's plan, steps, items, how each step is undone, the list of things to remove later, the end condition; drafts changes to `SYSTEM.md` | Touches code, the record, or the owner's settings |
| **Builder** | Builds one build step in a checkout of one module's repository; runs tests; uses a preview; opens one pull request; answers review findings | Merges; releases; writes to the home repository; holds staging or production credentials; marks anything passed |
| **Reviewer** | A fresh session that reads the pull request or plan, uses the product in a preview, and returns a verdict in a fixed form | Writes to any repository (the script records the verdict) |
| **The script** | Starts every agent; reads pull requests, CI, deployments, flags and metrics; merges and requests releases where permitted; turns exposure down when health fails; writes the record and the status page | Decides anything an item or a permission doesn't already decide; raises exposure without permission |
| **Monitoring** | Answers the script's queries | (Not an agent. A "watcher agent" was rejected by both drafts: the most consequential decision would rest on an agent's word.) |
| **People on other teams** | Review and approve pull requests in their repositories, as usual | (Their approval is a place on the path the script waits for) |

**The script drives, on a timer.** One new command, `advance`, replaces the lead's table from results to commands
(most of V1's 5,553-word `build/SKILL.md`). Each run reads the real state (the record, pull requests, CI,
environments), moves every step that can move, and stops. It is safe to run at any moment, because it keeps no plan
of its own. A timer runs it every few minutes. It wakes the lead only for an owner's decision, a builder that says
it is blocked, a failed health check, a step that has failed enough reviews to need a planner or the owner, and the
daily report.

**How the owner is reached.** Only in the chat, plus one thing: the settings name one command that sends the owner
a one-way message ("something is waiting, open the chat"). No decision is taken there. Each question on the status
page says what happens if nobody answers, and questions don't wait silently: after a day the notice is repeated,
and anything holding a module is released after the time the owner set.

## 3. Several repositories

```
home repository
  ORCHESTRATE.md   the owner's settings: permissions, risk levels, notify command, daily spend cap
  SYSTEM.md        modules, their repositories, places and commands; contracts and their users
  GLOSSARY.md  STATUS.md (written by the script)
  changes/<id>/    BRIEF.md  PLAN.md  DONE.json  RECORD.json (script only)  reviews/
  system/          the command that starts every module together, and the tests of flows that cross modules

each module's repository
  its code, tests, contract files, CI and release pipeline, as before
```

**Two settings files, not one.** What only the owner controls (permissions, risk levels, spend cap) sits in a short
file planners never draft, so a planner's edit to the system description can't quietly widen a permission in the
same diff. *(Fable's position, which held against Opus's single `SYSTEM.md`.)*

**The `system/` folder** is where all three earlier microservice designs ended up: how the modules run together
needs an owner. Here the home repository is that owner, and its flows across modules are tested there.

**Ordering across repositories is one rule:** a step starts only when every step it `needs` is Done, and for a
released module Done means live and watched. There is no merging several repositories at once: GitHub can't, and
merging together isn't releasing together. Every step must instead be safe to release with every other module at
the version it is running now. A `needs` entry may name a place only where Done is the wrong wait, such as
`ui-lib:S2@published` for a library; add that only when a trial shows the need.

**One step per module is being released at a time, across all changes**, from merge until its observation period
closes, so a health drop has one suspect. Building and reviewing the module's next step may overlap with it; the
next step is checked again once the earlier one is live. *(Fable held the module for the whole step, which leaves
it idle overnight while an approval waits; Opus locked per change, which lets two changes release into one module
at once. This takes the safe half of each.)*

**One open change per contract.** Two changes can each be compatible with production and incompatible with each
other: one adds a field while another removes one the first still reads. Until a trial shows this is too slow, the
script won't let two open changes alter the same contract.

**Modules the owner's agents don't control** are marked `Ours: no`. A step there is a pull request the script opens
and waits on, or a request the owner makes of that team. The status page shows it as waiting on that team.

## 4. Backwards compatibility and data

**The rule every step meets:** it is safe to release alone, beside every version of every other module that can be
running at the same time. "Can be running" includes the old and new copies side by side during a rollout.

**How a breaking change is planned.** As four steps across the modules involved:

1. **Add**: the providing module accepts and returns the new form while keeping the old.
2. **Move**: each user moves to the new form, one step per user module, usually behind a flag.
3. **Watch**: a watch step until the old form is unused.
4. **Remove**: the providing module drops the old form.

Database changes inside one module follow the same order (add a column, write both, backfill as an operation step,
read the new one, stop writing the old, drop it). For events, the plan says which side upgrades first, and an item
replays old messages through the new reader.

**How it is checked without believing anyone:**

- **Whether a diff breaks a contract is decided by a tool, not by the planner's label.** Every pull request that
  touches a contract file is compared (with `oasdiff`, `buf breaking` or the schema registry) against the version
  running in each environment. A breaking diff is accepted only on a planned Remove step whose `needs` are Done. A
  "tidy-up" that drops a field fails here, whatever the plan called it.
- **Consumer-driven contract tests** (Pact's "can I deploy") where the project has them.
- **Before a Remove step**, three things must hold: every listed user's running commit is past its Move step; a
  counter on the old form has read zero for a window set from the users' longest cycle (a month where billing is
  monthly, not a default week); and the owner confirms. The plan must say what the counter can't see: readers of a
  table, messages still in a queue, and clients that never all upgrade (mobile apps, partners). For those, "zero"
  may never come, and removing becomes the owner's deprecation decision, not a measurement.
- **What is running is always read from the deploy system**, never from a file someone keeps up to date.

**Undoing is planned, not assumed.** Every step carries one line saying how it is undone ("turn the flag off",
"release the previous version", "cannot be undone"). For a step that touches data or a contract, an item proves the
undo in staging before production, including that data written under the new behaviour is readable by the old.
Otherwise turning a flag off can make things worse: rows written only in the new form break the old code that now
reads them.

**Data already written wrongly.** Turning exposure down stops new damage; it doesn't repair rows written badly at
25%. When a step is undone after writing data, the planner is asked whether a repair step is needed, and the owner
decides.

## 5. Delivery in small increments

**One rule for permission: raising exposure needs permission; lowering it never does.** Deploying to production,
raising a flag, starting a canary or running an operation in production needs the owner's yes or a standing
permission. Turning a flag off, setting a canary to zero, or releasing the previous version is always allowed, and
the script does it at once when health fails, then tells the owner. Destroying data always needs the owner and
can't be granted standing.

```markdown
## Standing permissions            (ORCHESTRATE.md; only the owner changes it)
| Action | Where | Granted |
|---|---|---|
| Merge once checked and reviewed | all modules | yes |
| Release | staging | yes |
| Release with new behaviour off | production | yes, except high-risk modules |
| Raise a flag to 25% | production | yes, while healthy |
| Raise a flag beyond 25% | production | ask |
| Run an operation | production | ask |
| Destroy data | anywhere | ask (can't be granted) |
```

A new project starts with every production line on "ask", and the owner loosens it as trust builds.

**Rules that keep a release honest:**

- **A permission belongs to a commit.** A yes given for one diff lapses if review changes the pull request.
- **Exposure doesn't rise during trouble.** Not while an incident is open on the system, nor when the module's
  error budget is spent.
- **Exposure rises without the owner present only where something always on can lower it**: the rollout tool's
  own analysis (Argo Rollouts, Flagger) or a timer in CI. A laptop that may be asleep can't be the only thing
  watching a 25% rollout.
- **An empty answer is not a healthy answer.** If the metrics query returns nothing, times out or errors, the script
  treats health as unknown and stops raising exposure.
- **Each module's health check is shown to fail once.** The module's first step breaks a staging copy on purpose
  and proves `Healthy` notices. A query that always passes is the most dangerous thing in the design.
- **Step-level signals and a shadow comparison.** A step that changes how money or personal data is computed runs
  old and new side by side at 0% exposure and counts disagreements before any user sees the new result. This is
  what catches a double currency conversion before the first failed renewal.
- **After an undo, the module is held**: nothing else merges or releases there until it is healthy. If the undone
  step wasn't behind a flag, the script opens a revert pull request, because otherwise the bad commit stays on main
  and the next person's unrelated release ships it again. An undo that fails stops everything on that module and
  sends the owner an urgent notice.

**Who records Done:** the script only. A step that was undone goes back to a builder with what was measured, and
counts as a failed round on V1's escalation stages (kept as they are; they were debugged on a real deadlock). A
failure the owner says "wasn't us" (a flaky check, someone else's outage) doesn't count. A required check that
fails is retried once before it counts.

## 6. Verification

**Check before merging wherever merging can reach users or other people share the branch.** V1 merges first and
checks after: its claim check refuses until the builder's commit is already on main (`agent_loop.py:2803`), then
runs the checks on main's tip (`:2814-2817`). In V2 the script runs every Automated Check on the pull request's
commit merged onto the target branch, reads CI for that exact commit, and runs the reviewer there, before merging.
Only in a solo repository where nothing is released from main does the reviewer judge after merging, as in V1,
because otherwise the next step has to be built on a stacked branch, which agents handle badly.

| Place | What is proved | By |
|---|---|---|
| Builder's machine | Fast feedback only; proves nothing | Builder |
| CI and the script's clean copy | Tests, Automated Checks, contract comparison | CI, read through the code host; the script |
| Preview | Reviewer Inspections; flows across modules | Fresh reviewer; the script |
| Staging | Release works; undo works; health check fails when broken | The script, through the pipeline |
| Production | Running for everyone; healthy for the window; production signals; old form unused | Deploy system and monitoring, read by the script |

**When a reviewer is used** (by risk, not by kind of proof):

- any step on a high-risk module, including a step that only *uses* a high-risk contract;
- any step that touches a contract or data, or can't be undone;
- any step the script flags because its diff changes CI configuration, deletes tests, or changes a script that a
  check calls;
- once at the end of every change, in production, with a test account. This is the one review pass Anthropic kept
  when it stripped its own harness back.

**Plan review** happens only for a change that crosses modules, touches a contract or data, or has a step that can't
be undone, and it answers a fixed set of questions. *(On Thrum, design review was 18 of 24 reviews, but 6 of the 18
asked for changes, so it is narrowed, not dropped.)*

**Where the guarantee could still break, and what stops it:**

- **The script's credentials are reachable by agents.** On one laptop, as one operating-system user, a builder can
  run `kubectl`, `gh` or a flag tool with whatever the owner's home folder holds. V1 only strips Claude's own
  variables, and only for Claude sessions; Codex sessions get the whole environment (`agent_loop.py:3266-3271`,
  `:3346`). So for any project with a production line in its settings, **the script runs where agents can't read
  its credentials**: in CI, or as a separate operating-system user. The script's own writes to staging and
  production are limited to triggering named pipeline jobs and lowering exposure; the pipeline holds the real
  credentials.
- **The record is edited.** The home repository's main branch accepts pushes only from the script's account where
  the code host can enforce it, and receipts let `audit` catch an entry forged even with that account. `audit`
  treats an expired receipt (CI logs and metrics are kept for weeks, not for ever) as unverifiable, not as false.
- **A second approval outside the chat, for destroying data only.** The pipeline itself asks the owner. This
  protects anything only if the owner's own code-host login is absent from every machine that runs agents and the
  pipeline blocks self-approval. Without those two conditions, an agent can approve through the API, so the set
  must say plainly that the second approval protects nothing.
- **Untrusted text reaching agents.** Logs, pull request comments from other teams and production query results are
  handed to agents as data inside a marked block, never as instructions.
- **Personal data.** The settings list what an agent may read from production. Evidence is scrubbed before it is
  committed to the home repository.

## 7. What it costs a small project

A one-repository app with no pipeline sees: the home repository is its own repository; one module; no contracts,
staging or production; steps Done when merged, after the script's checks in a clean copy; no plan review unless
asked; one reviewer at the end of each change and on steps the planner marks; no timer (the lead runs `advance`
while the chat is open). That is less than V1, which requires a design review per module and has a lead running a
table. A job small enough for one chat should still use none of this.

Each production part switches on with one line, and the owner can see what each costs:

| The owner adds | What switches on |
|---|---|
| A second repository | A separate home repository and the script's own account |
| Pull requests and CI | Checking before merging; CI results read through the code host |
| A contract | Contract comparison; the Add, Move, Watch, Remove plan |
| A release command and a running-version command | "Running in production" items; release order between steps |
| A health command | Observation periods and automatic undo |
| A production line in the permissions | The script must run where agents can't reach its credentials |
| A flag or operations command | Operation steps; flags with removal steps |

## 8. What is kept, changed and dropped from V1

**Kept:**
- items written before building, which the builder can't change;
- the script as the only writer of the record, now extended to CI and environments;
- a fresh reviewer who uses the product;
- the planner says what, the builder decides how;
- files and git for all state;
- 2–4 builders, one per module;
- the owner only chats, and the lead interviews first;
- the brief and the glossary;
- both hosts, with the model and effort named at every start;
- the escalation stages after failed reviews;
- the work led by taste (the owner picks a look before the build).

**Changed:**
- milestones under modules become steps under changes;
- Done means proved where the item says, including production;
- `advance` on a timer replaces the lead's result table;
- the builder's whole output is a pull request, and the reviewer's is a verdict, which removes V1's checks that each
  changed only its own fields;
- checking happens before merging;
- review is triggered by risk;
- the record carries sources and receipts;
- each change has one plan file and one done-when file (V1's per-module `DESIGN.md` and `LOG.md` go; a builder who
  finds the plan wrong ends `BLOCKED` with a proposal in its report, and the planner settles it);
- V1's single integrate lock remains only for repositories that merge directly.

**Dropped:**
- Ready for Review as a builder's claim;
- design review of every module;
- showing sessions inside the desktop apps as a core part (it becomes optional);
- the quota forecast, reduced to "used, and when it resets";
- the marks that let several leads share one project.

**Moving a V1 project across.** A `migrate` command turns each module's open milestones into steps of one change,
keeping their items, reviews and failed-review counts, and leaves finished milestones in the record as history.

## 9. Worked example: making payment amounts exact

Three repositories: `payments` (high risk) provides `POST /charges` with `amount` as a decimal; `orders` and
`billing` (both use money, so high risk) call it. A nightly finance export in `orders`' repository also reads
`amount`, and nobody has listed it. The owner says: "Stop the rounding errors. Amounts should be whole pence."

1. **Lead.** Asks why (refund mismatches), what is out of scope (currencies other than GBP and EUR) and how the owner
   will judge it (no mismatches in a month). Writes the brief; the owner approves it.
2. **Planner** writes change `2026-11-minor-units`: P1 *Add* `amount_minor` to payments, writing both columns; O1
   and B1 *Move* orders and billing behind flags, each with a shadow comparison; P2 *operation*: backfill old rows;
   W1 *watch*: old field unused for 31 days (billing runs monthly); P3 *Remove* `amount`. To remove later: flags
   `orders.minor` and `billing.minor`, the `amount` field, the double write. End condition: no refund mismatches for
   30 days. Plan review runs (the change crosses modules and touches a contract) and asks for a `NOT NULL` default on
   the new column.
3. **P1.** Builder opens a pull request in `payments`. The script runs checks on the merged commit; the contract
   comparison says "additive"; a reviewer uses it in a preview. Merged under standing permission. Released with
   nothing using the new field; healthy for 30 minutes. The undo (release the previous version) was proved in
   staging with rows written in both columns. Done.
4. **O1 and B1** start, because they need P1. At 0% exposure, billing's shadow comparison counts 412 disagreements
   on yearly euro plans: a double conversion. Billing's builder fixes it before any user sees it. The owner approves
   "5%, then 25% at one-hour intervals while healthy". The rollout tool's own analysis watches the ramp. Done for
   both.
5. **P2** runs after the owner says yes. **W1** watches the counter on `amount`: it doesn't reach zero. The script
   shows that the nightly export still reads it. The planner adds O2 (move the export), and W1 restarts after it.
6. **P3.** The contract comparison says "breaking", which is allowed because P3 is a planned Remove step with its
   `needs` Done. The owner confirms the removal. Dropping the old column destroys data, so the pipeline asks the
   owner a second time. Done.
7. **The end-of-change review** places an order with a test account in production. The flags are removed by their
   steps. Thirty days without a mismatch: the change is Finished.

The owner was asked six things over about five weeks, almost all of it watching: the brief, the ramp, the backfill,
the removal, the second approval for the drop, and nothing else.

## 10. Still open

**Not designed, deliberately:** several owners (on-call rotation, release freezes, approvers per service), and the
cost of previews. The design assumes one owner and lists both as the next extensions.

**Abandoning a change halfway.** If the owner cancels after P1, the new field, the double write and any flags are
live. The plan's list of things to remove later is exactly what has to be undone, so cancelling turns that list
into removal steps. That works on paper and hasn't been tried.

**The guesses that would hurt most if wrong:**
- **Planners write good health signals and step sequences.** A loose bound lets a broken change through. The owner
  approves each module's health signals once, and steps can only add to them.
- **Small steps stay cheap.** The example takes about ten steps; V1 showed that a fixed cost per step pushes towards
  bigger pieces. The full machinery may be worth it only for breaking changes.
- **Quiet services give monitoring nothing to judge.** 5% of very little traffic measures nothing.
- **The script stays small enough to trust.** V1's script grew from 3,600 to 7,200 lines. V2's gate logic has
  production behind its mistakes, so it is tested directly with injected faults (a check that times out, a lagging
  deploy record, an empty metrics answer) before any agent relies on it.
- **Running agents in CI** needs an agent sign-in there, which on Claude means an API key and metered billing, not
  the owner's plan. A daily spend cap in the owner's settings applies to anything the timer starts.

**What to try first, cheapest first:**

1. **Build only the reading half of `advance`** and point it at a system the owner already runs, with no agents. Does
   the status page stay true for a week?
2. **Drive the new pieces by hand.** Read the running version, compare contracts against it, and run the health
   check, including breaking staging on purpose.
3. **Run three tiny services in three repositories**, with one planted fault and one unlisted user, through the
   worked example. **Compare it with a baseline**: one strong agent working through the same pull requests, CI and
   pipeline with only a done-when file. The research's main finding is that such a baseline often wins, so V2 has to
   beat it to earn its weight.

## Where the two drafts disagreed, and how it was settled

| Question | Opus | Fable | Settled |
|---|---|---|---|
| One mechanism for Done, or items plus gates | Gates, chosen by step kind | Production as a place to prove items | Fable's, displayed as Opus's path |
| Check before or after merging | Before, everywhere | After, for direct merges | Before, except a solo repository releasing nothing (both moved) |
| What a module or component is | "Component", ownership only | "Module", kept | "Module" (Opus conceded) |
| Settings files | One `SYSTEM.md` | Two: owner's settings and system description | Two |
| Who writes the step file | Builder writes status and evidence | Planner and script only | Planner and script only |
| Release lock | One per change | Whole step, per module | One release per module across changes; building overlaps |
| What `needs` waits for | Names a step and a place | Always Done | Done, with a place only for cases like a published library |
| Script credentials | Script holds deploy tokens | Script read-only | Script triggers named pipeline jobs and lowers exposure; it runs where agents can't reach it |
| Second approval outside the chat | Optional | For steps that can't be undone | For destroying data only, with its conditions stated |
| Step kinds | Five phase kinds | Build, operation, watch | Build, operation, watch; breaking-ness found by a tool |
| Step-level production signals | Yes, with shadow comparison | Module-level health only | Both |
