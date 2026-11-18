# Orchestrate V2: a design for production systems across several repositories

Draft by Opus 5.5, 11 November 2026, from `workbench/orchestrate-v2/BRIEF.md`. Design only: nothing under `skills/`
or in `~/Workspace/thrum` was changed. Line numbers are against branch `orchestrate-1.6.4` as checked out today
(`agent_loop.py` is 7,243 lines).

## The design in one paragraph

Version 1 asks one question about a piece of work: has it been merged with its checks passing? Version 2 asks a
longer one: has it reached every user, been seen to be healthy, and had the old way of doing it removed? Everything
else follows from asking the longer question honestly. The owner's request becomes a **change**. A change is carried
out as a series of **steps**, and each step is one pull request in one repository that is safe to put into
production on its own, at any moment, alongside whatever else is running there. Every step travels along the same
**path to production**, a fixed list of **gates**, and each gate names who or what decides that the step has passed
it: the CI the project already has, the script, a reviewer, the monitoring system, or the owner. The script writes
each pass into the **record**, and each entry carries a **receipt**: the identifier of the CI run, deployment or
metrics query it came from, so that anyone can check the entry again later. Steps depend on each other by where
the other step has got to ("the payments step is in production"), not by whether it has been merged. Agents never
hold production credentials. Putting a change in front of more users needs the owner's permission. Putting it in
front of fewer users, by turning a flag off or rolling back, is always allowed, and the script does it by itself
when a health gate fails. For a small project with one repository and no deployments, the path has three gates
(checks, review, merge) and V2 costs less than V1 does.

## How to read this

Section 1 defines the terms, and each one is defined before it is used anywhere else. Sections 2 to 10 answer the
brief's ten points in its order. Each section ends with the alternatives I rejected. Where I make a claim about V1, I
give the file and line. Where I rely on outside practice, I cite it, and I say which parts nobody has tried with
agents.

---

## 1. The model

### The words, defined once

**Owner.** The person the system is built for. They only chat, with the lead. Unchanged from V1.

**System map.** One file, `SYSTEM.md`, that describes the whole system: its components, the contracts between
them, its environments, the commands the script uses to ask the outside world questions, and what the owner has
given standing permission for. It replaces V1's `ORCHESTRATE.md` and the module table in `ARCHITECTURE.md`. Only the
owner changes it, through the lead, as in V1 (`build/SKILL.md:182-183`).

**Component.** A part of the system that is built, tested and deployed as one unit, with one owner: a service, a
front end, a worker, a shared library, a database schema. A component lives in exactly one repository, and one
repository may hold several components. The system map lists for each component its repository, its path inside
that repository, its owning team, how it is deployed, and its health signals. A component is what V1's module was
for in one respect, ownership: each kind of state has exactly one component in charge of it
(`plan-module/SKILL.md:104-106`). It is not a unit of planning any more.

**Contract.** Something one component provides that another relies on: an HTTP or gRPC API, an event on a topic, a
database table another component reads, a shared library's public surface. The system map lists each contract, its
provider, its known consumers, its schema file, and the command that checks a version of it for compatibility.
V1 called these interfaces.

**Environment.** A place the system runs: `local`, `preview` (one per pull request, if the project has them),
`staging`, `production`. The system map lists them in order. A small project may have only `local`.

**Change.** One request from the owner, carried from their words to its end state. It owns: the brief (V1's project
brief, unchanged), the plan (which steps, in what order, across which components), the end condition (how anyone
will know the change is finished in production), and its status. "Make payments amounts exact" is a change. "Build
the first version of the engine" is also a change, a large one. A change replaces V1's project-and-module
hierarchy as the unit the owner follows.

**Step.** One pull request in one repository, touching one component (or one component plus its tests), built by
one builder session, and safe to deploy to production on its own. "Safe on its own" has a precise meaning: the
step works correctly alongside every version of every other component that can be running at the same time as it.
A step has items, exactly as a V1 milestone does. A step replaces V1's milestone. The difference that matters is
that a milestone only had to merge cleanly, and a step has to be deployable.

**Item.** One thing that must be true before a step passes its review gate. Unchanged from V1, including that the
planner writes items before building and the builder can't change them (`done-when.md:182-184`). V2 adds one way
to prove an item, the **production signal** (section 6).

**Exposure.** How many users a step's new behaviour reaches: none (the code is deployed but nothing calls it, or it
sits behind a flag that is off), some (a flag or canary at a percentage), or all. Exposure is the quantity the
owner's permission is about.

**Gate.** One point on the path to production that a step has to pass, with a named decider. The deciders are: the
project's CI, the script, a reviewer, the monitoring system (through a query the script runs), a human reviewer
from the team that owns the component, the owner, and time (an observation window). An agent's own report is never
a decider.

**Path to production.** The ordered list of gates for a component, declared once in the system map. Every step on
that component goes through the same path, minus the gates its kind lets it skip (section 5).

**Record.** The script's ledger of every gate a step has passed, with a receipt for each. Only the script writes it.
It replaces V1's per-module `ACCEPTED.json` files with one file per change.

**Receipt.** The identifier of the evidence a gate pass rests on, which an external system issued and the script
can fetch again: a commit SHA, a CI check-run ID, a pull request's merge commit, a deployment ID, a flag change's
audit-log ID, a metrics query with its time range and result, a review file's commit. The script's `audit` command
fetches every receipt again and reports any entry whose receipt doesn't hold up.

**The script.** Still a set of commands, not an agent. In V2 it also runs on a timer (section 2), because a change
now waits on deployments and observation windows that last hours or days.

That is five core concepts (system map, change, step, gate, record) and the words that sit inside them. The
statuses are not a separate concept: a step's status is the last gate it passed, the next gate, and who that gate
waits on.

### What replaces what

| V1 | V2 | Why |
|---|---|---|
| Project | System (described by the system map) | A production system outlives any one request. |
| Module (unit of planning and of ownership) | Component (ownership only) and change (planning) | In V1 the two jobs were joined. In a multi-repository system the components are fixed by the code and the teams, while what to plan comes from each request. Thrum's own status page lists every module as "(no row in the module table)", because the module table and the module folders drifted apart. |
| Milestone | Step | A step must be deployable alone, which a milestone never had to be. |
| Done-when file, item | Step file, item | Kept. The format gains a few fields (section 9). |
| Ready for Review (after merge) | In Review (before merge, on the pull request) | V1 merges first and verifies after (section 6). In production, merged usually means deployed. |
| Done (merged, checks passed, reviewed) | A step is Done when it has passed every gate on its path. A change is Done when every step is Done, including the clean-up steps, and its end condition holds in production. | The brief's "honest end state". |
| `ACCEPTED.json` per module | One record per change, every entry with a receipt | One view across repositories, and records that can be re-checked. |
| `ORCHESTRATE.md` and the module table | `SYSTEM.md` | One file about the system, not two that drift. |

### What state each concept owns

| Concept | Lives in | Written by | Holds |
|---|---|---|---|
| System map | `SYSTEM.md`, control repository | Planner drafts; owner approves every change to it | Components, contracts, environments, paths to production, the script's commands, standing permissions |
| Change | `changes/<id>/` in the control repository | Lead (brief), planner (plan) | `BRIEF.md`, `PLAN.md`, `steps.json`, `LOG.md` |
| Step | An entry in `steps.json` | Planner (what is asked), builder (status and evidence), reviewer (verdicts) | Component, kind, items, `needs`, flag, branch and pull request |
| Record | `changes/<id>/record.json` | Only the script | Each gate passed, when, with which receipt; the owner's decisions with their words; tokens used |
| Status page | `STATUS.md`, control repository | Only the script | Generated from the records and from live queries |

The **control repository** is where all of this lives. For a project with one repository, it is that repository,
in `docs/plans/` as in V1. For a system spread over several repositories, it is one repository chosen for the
purpose, which holds no product code (section 3).

---

## 2. Who does what

### The agents and the script

| Who | May | May not |
|---|---|---|
| **Lead** (the agent the owner chats with) | Talk with the owner; write the brief (the `interview-me` skill, kept); run the script's commands; relay the owner's decisions with their words; triage what the script can't (a builder that says it is blocked, a health failure to explain) | Write or judge code; approve anything for the owner without their words; edit a step file, a record or `SYSTEM.md` without the owner |
| **Planner** | Write a change's plan: the steps, their order and kinds, items, flags, the rollout plan, the end condition. Draft changes to `SYSTEM.md` for the owner to approve | Build; mark anything passed; touch a record |
| **Builder** | Build one step on a branch in one repository; run the project's tests and the step's checks; run the product locally or in a preview environment; open the pull request; answer review findings | Merge; deploy; change a flag outside local and preview; hold staging or production credentials; change an item; change CI configuration or delete tests without that step being marked for it (section 6) |
| **Reviewer** | Read the pull request and the plan; run the product from the pull request's commit, locally or in its preview environment; read production dashboards with read-only access when a step's items ask; return a structured verdict | Edit any file. In V2 the reviewer is read-only, and the script writes the verdict into the step file. The assessment proposed this (`ASSESSMENT.md:186-194`), and it removes the whole "did the reviewer change only its own fields" check (`agent_loop.py:1184`). |
| **The script** | Start every agent; read CI results, pull requests, deployments, flags and metrics through the system map's commands; merge, deploy, change flags and roll back, each only where the system map's gates and permissions allow; write the record and the status page; wake the lead | Decide anything an item or a permission doesn't already decide; increase exposure without permission |
| **Owner** | Approve the brief, approve changes to `SYSTEM.md`, grant standing permissions, approve each increase in exposure that isn't covered by a standing permission, approve anything that destroys data, accept or rescope a step that keeps failing | They never type a command. |
| **People on other teams** | Review and approve pull requests in the repositories their team owns, through the forge as usual | (Not under the set's control. Their approval is a gate the script waits on.) |

Only one new kind of participant appears, and it isn't an agent: the monitoring system, which the script queries.
I rejected a "watcher" agent that reads dashboards and says whether a rollout is healthy, because that would make
the most consequential decision in the whole path rest on an agent's word.

### The script now runs on a timer

V1's lead runs a lookup table from result to next command (`build/SKILL.md:281-295`), and the assessment called
that an LLM doing a scheduler's job (`ASSESSMENT.md:176-184`). V2 has to wait for things V1 never waited for: a CI
run of twenty minutes, a staging deploy, a canary that needs an hour at 5% of traffic, an observation window of a
week before old code is removed. A chat session can't usefully wait a week.

So the script gets one new command, `advance`. Each time it runs, it reads every open change, works out for each
step which gate is next, and does whatever it can do without a decision: starts a builder on a step whose `needs`
are met, starts a reviewer on a step whose CI is green, merges a step whose review passed and whose merge is
permitted, triggers a deploy that is permitted, moves a ramp to its next percentage when the health query passed
and the ramp is permitted, rolls back when a health query fails. It runs on a schedule: a scheduled task on the
owner's machine (Claude Code's scheduled tasks or `launchd`), or a scheduled CI workflow in the control repository
for a system that has to keep moving while the owner's machine is off. It is idempotent, and it holds one lock per
change.

`advance` wakes the lead (by starting a lead session with a short message, or by posting into the lead's chat where
the host allows it) only for: a decision that is the owner's, a builder that ended with `BLOCKED` or
`NEEDS_CONTEXT`, a health gate that failed, a step that has failed review enough times to need a planner or the
owner, and the daily report. Everything else happens without an LLM in the loop. The lead becomes what the owner
needs it to be, a person to talk to, rather than a dispatcher.

### How the owner is reached

As in V1, only through the lead, in the chat (`build/SKILL.md:359-360`). V2 changes what the lead brings them. The
owner's decisions are grouped by change and by moment, so one message carries one decision about one change:

> **Exact payment amounts (change 14).** The payments service now accepts and returns the new `amount_minor` field
> in production, and has for 24 hours with no rise in errors (dashboard link). Next is sending 5% of orders through
> the new field. If the charge success rate drops more than 0.5 points below the last week's, the script turns the
> flag off by itself and tells you. Go ahead with 5%, then 25%, 50% and 100% at one-hour intervals while it stays
> healthy?

The owner's yes is saved with their words, as in V1, and the report lists every decision saved in their name
(`README.md:481-485`). V1's honest weakness remains: the script can't tell the owner's decision from one a lead
invented. Section 6 says where V2 can do better for production deploys, for owners who want it.

### Rejected

- **Making the lead the scheduler, as V1 does.** It can't wait for days, it costs a long-lived context, and nothing
  in its table needs judgement. 
- **A long-running server for the script.** A timer that runs an idempotent command gets nearly everything a
  server would, and fails more plainly. If a scheduled run is missed, the next one catches up.

---

## 3. Several repositories

### Where plans and records live

All plans and records live in one **control repository**, and none in the product repositories. The product
repositories hold code, tests, contract files, CI and pull requests, as they always have.

```
control repository
  SYSTEM.md                     the system map
  GLOSSARY.md                   agreed names (kept from V1)
  STATUS.md                     the owner's page; only the script writes it
  changes/
    0014-exact-payment-amounts/
      BRIEF.md                  the owner's words and why (interview-me, unchanged)
      PLAN.md                   the steps in order, the rollout plan, the end condition; no status
      steps.json                each step's items (the done-when file, one per change)
      LOG.md                    dated events
      record.json               only the script writes it
  evidence/0014/…               reviews, captures, query results
  components/<name>.md          optional: a component's own design, where it needs more than a row
```

Why one place: the order of steps across repositories is a single graph, and a graph split over five repositories'
files is five chances to disagree. Status has to be one page. And a team that owns one of the repositories may not
want an agent's plans committed to it. The microservice designs from today kept everything in one repository
(`workbench/orchestration-review/microservices/unified-design.md`); the control repository is the same idea for
code that is already spread out.

For a single-repository project, the control repository is the product repository and the folder is `docs/plans`.
Nothing about the layout changes except that `changes/` replaces V1's module folders.

### How work spanning repositories is ordered

Each step has a `needs` list, as V1 milestones do (`plan-module/SKILL.md:113-117`). The change is what a need
names. In V1, a need is met when the other milestone is Done, which means merged and reviewed. In V2, a need names
a step and a gate:

```json
"needs": ["payments/expand-amount-minor@production"]
```

This reads: don't start building this step until the payments step that adds the new field has passed the
production gate. A consumer that starts sending a new field the day the provider's change is merged, but a week
before the provider is deployed, breaks production. Merge order is the wrong thing to wait on when components are
deployed separately. Zuul, the gating system OpenStack uses across hundreds of repositories, orders changes across
repositories with a `Depends-On` footer, but it orders merges, and its own users point out that a dependency blocks
nothing unless both projects gate on it
([Zuul gating docs](https://zuul-ci.org/docs/zuul/9.4.0/gating.html);
[zuul-discuss, 2022](https://lists.zuul-ci.org/archives/list/zuul-discuss@lists.zuul-ci.org/thread/UGWWG4WXRHXMKVCNIOYFSWVDROTKALWV/)).
V2 needs deployment order, which is why the gate is in the need.

Two smaller rules come with it.

- **A step never spans repositories.** If the work needs code in two repositories to change together, the plan is
  wrong: either one side expands first, or the two components are really one and the system map is wrong.
  Separately deployed components can't change atomically in production, so pretending they can in a pull request
  only hides the moment they disagree.
- **A shared library is a component whose "deploy" is publishing a version.** A step that changes it passes a
  `published` gate; consumers' steps need `lib/step@published` and bump the version in their own repository.

### How work spanning repositories is verified

Three checks, each in a different place:

1. **Each step, against what is deployed.** At its pull-request gate, each step that touches a contract runs the
   contract's compatibility command against the version of every other party to that contract that is currently
   deployed in each environment (section 4). This is how separately deployed components are kept compatible
   without being tested together on every change.
2. **Flows across components, in staging.** The system map lists the system's flows, such as "an order goes from
   cart to receipt", each with a command that runs it against an environment. When a step reaches staging, the
   script runs every flow that passes through its component. This is the "system module" idea from today's
   microservice designs, kept as a list in the system map rather than a module, because flows have no code of
   their own to build once they are written.
3. **The change's end condition, in production.** Usually a query: "no requests to the old field for seven days",
   "the new path's error rate is no worse than the old one's was".

### One view of status

`STATUS.md` in the control repository, written only by the script, as in V1 (`done-when.md:76-80`). It is built
from the records and from live queries at the time it is written (pull request states, CI, what is deployed where,
flag percentages). It opens with what waits on the owner, then each open change with each step's place on its
path, then recently finished changes. `advance` rewrites it whenever anything moves.

### Rejected

- **Plans in each product repository, with a script that gathers them.** It needs write access to every
  repository, including other teams', for files those teams didn't ask for, and every cross-repository `needs`
  becomes a reference that can go stale silently.
- **Converting the system to a monorepo first.** Often the right long-term answer, but not something an
  orchestration skill should require, and it doesn't remove separate deployment, which is where the hard part is.
- **Merge-level dependencies (Zuul-style `Depends-On`).** Covered above: the wrong event to wait on.

---

## 4. Backwards compatibility and data

### The rule every step must meet

A step must work alongside every version of every other component that can be running at the same time. In
practice that is: what is deployed in each environment now, and the version this step's own component is replacing
(because during a rolling deploy both run). The planner writes steps to meet this rule. The script checks it, so it
doesn't depend on the planner having got it right.

### How a breaking change is sequenced

Every breaking change to a contract or a schema is planned as **expand, migrate, contract**, the pattern Fowler
calls parallel change ([Fowler, 2014](https://www.martinfowler.com/bliki/ParallelChange.html)):

1. **Expand.** The provider supports both the old form and the new one. Nothing changes for current consumers. For
   a schema, the new column or table is added and written alongside the old one. The step also adds a counter of
   use of the old form, broken down by caller, which the contract step will need.
2. **Migrate.** Each consumer moves to the new form, one step per consumer, each behind a flag where the new form
   changes behaviour. For data, a backfill fills the new form for old rows, as a step of its own.
3. **Contract.** The provider removes the old form, once nothing uses it. For data, the old column is dropped later
   still, in its own step.

Each of the three is a step **kind** in `steps.json` (`expand`, `migrate`, `backfill`, `contract`, `drop`), next to
the ordinary kind `build`. The kind tells the script which gates apply (section 5) and which extra conditions a step
has to meet. Fowler's own warning is the reason the plan writes all three phases up front: a contract phase that
never happens leaves the system worse off than before. In V2, a change isn't Done until its contract steps are,
and the status page shows a change stuck after migrate as unfinished.

### How compatibility is verified

The system map names, for each contract, a compatibility command that takes two versions and exits 0 if the new
one is compatible with the old. The project already has or chooses its tool; the script only calls it:

| Contract | Typical tool | What it checks |
|---|---|---|
| HTTP API with consumers we know | Pact, with deployments recorded per environment | Each consumer's recorded expectations against the provider's new version, and the reverse; `can-i-deploy` asks the question for one environment ([Pact docs](https://docs.pact.io/can_i_deploy)) |
| gRPC / protobuf | `buf breaking` against the deployed version's schema | Wire and source compatibility at a chosen strictness ([Buf](https://buf.build/docs/breaking/)) |
| Events on a topic | The schema registry's compatibility mode (`BACKWARD_TRANSITIVE` for most event streams) | That consumers on any older schema can still read new events ([Confluent docs](https://docs.confluent.io/platform/current/schema-registry/fundamentals/schema-evolution.html)) |
| OpenAPI without consumer contracts | An OpenAPI diff tool | Removed fields, narrowed types, new required inputs |
| Database schema | A migration linter (such as Squawk for Postgres) plus the old version of the code's tests run against the new schema | That old code still works on the new schema while both run |

The question the script asks for each step that touches a contract is: "is this commit compatible with what is
deployed in every environment, on both sides of every contract it touches?" To ask that, it needs to know what is
deployed, which is the next point.

### What is deployed: read from the deploy system, never written by hand

The system map gives a command for each environment that prints the commit deployed for a component:
`deployed <component> <environment>`. It can read a GitHub deployment, an Argo CD application's revision, a
Kubernetes image tag, a Pact broker's recorded deployment, or a release file in a deploy repository. The script
calls it at every gate that needs it, and never trusts a cached answer older than that gate. Today's unified
microservice design kept `deploy/released.json`, a file the owner updated by hand
(`microservices/unified-design.md`, "Version skew" section); that is the kind of record that is right until the
one day it isn't, so V2 asks the deploy system each time. Pact recommends the same: record every deployment, to
every environment, so the compatibility question has a true answer
([PactFlow docs](https://docs.pactflow.io/docs/bi-directional-contract-testing/deploying)).

### When the contract step may go ahead

A `contract` step has two extra gates before its pull request may merge, both decided without an agent:

- **Every known consumer has moved.** The deployed commit of each consumer, in every environment, is at or after
  its migrate step's merge commit.
- **Nothing uses the old form.** The usage counter from the expand step reads zero for an observation window that
  the plan sets (seven days by default) in production. This catches the consumer nobody listed: a batch job, a
  partner's integration, an old mobile app.

The owner confirms a contract step, even with both gates met. Removing an old API path is reversible in code (a
redeploy brings it back) but not for a caller who broke in the meantime, and the owner may know of a caller the
metrics can't see, such as a yearly job. A `drop` step, one that destroys data, always needs the owner, can't be
covered by a standing permission, and has a gate that a backup of what will be destroyed exists and has been read
back.

### Data migrations that move data

A `backfill` step is code (a job) plus its run. It is reviewed like any step, then run in staging, then in
production with the owner's permission, in batches, with its own verification query as an item ("rows where the
new column disagrees with the old: 0"). The builder writes the job; the script runs it through the system map's
`run-job` command; the item's query is evaluated by the script.

### Rejected

- **Versioning the whole API (v1, v2) for every breaking change.** Right for public APIs with external callers;
  heavy between a system's own services, and it multiplies paths to keep alive. Stripe's approach of version-change
  modules is the gold standard for public APIs
  ([Stripe, "APIs as infrastructure"](https://stripe.com/blog/api-versioning)); the planner may choose it for a
  public contract, and the system map says which contracts are public.
- **Letting the planner judge compatibility.** The planner proposes the sequence; a tool checks it against what is
  deployed. A plan that is wrong about compatibility fails at the first gate rather than in production.
- **An owner-maintained file of what is released.** Covered above.

---

## 5. Delivery in small, low-risk increments

### The path to production

The system map declares a path per component, or one for all. A full one:

| # | Gate | Decided by | Receipt |
|---|---|---|---|
| 1 | **Checks**: the project's required CI checks pass on the pull request's head commit, and every item `check` passes when the script runs it in a clean checkout of that commit merged onto the target branch | CI, read through the forge's API; the script | Check-run IDs; the script's run log |
| 2 | **Compatible**: the compatibility command passes against what is deployed in every environment | The script, through the system map's commands | The command's output and the deployed commits it compared |
| 3 | **Reviewed**: a fresh reviewer passed every item that needs one, and, where the component's team requires it, a person from that team approved | Reviewer; human reviewer | Review file commit; the forge's approval ID |
| 4 | **Merged** | The script, when the system map permits it; otherwise the owner | Merge commit |
| 5 | **Staging**: deployed to staging, and the flows that pass through the component pass there | The deploy system; the script | Deployment ID; flow run log |
| 6 | **Production, dark**: deployed to production with the step's new behaviour off; the component's health signals stay within bounds for a short window (default 30 minutes) | Deploy system; monitoring, through the script's query; time | Deployment ID; query and result |
| 7 | **Released**: the step's flag (or canary weight) moves through the ramp in its plan, each move permitted, each held for its window with health within bounds | Owner or standing permission; monitoring; time | Flag audit IDs; query results |
| 8 | **Observed**: at full exposure for the observation window, health within bounds | Monitoring; time | Query result |

A step's kind decides which gates it passes through. An `expand` or `build` step with no user-visible change
passes 1 to 6 and is Done; there is nothing to release. A `migrate` step behind a flag passes all eight. A clean-up
step that removes a flag that is already at 100% passes 1 to 6. A `contract` step passes 1 to 6 with the extra gates
from section 4. A small project's path is 1, 3 and 4.

### Flags

A step whose new behaviour reaches users does so through a flag, named in `steps.json`, with a default of off.
The system map gives the flag commands (`flag-get`, `flag-set`), which can call OpenFeature-compatible tools such as
flagd, or a vendor's API ([OpenFeature](https://openfeature.dev/)). Where a component is deployed with a canary
tool such as Argo Rollouts or Flagger instead, the "flag" is the canary weight, and gate 7 reads the tool's own
analysis result rather than running the query itself
([Argo Rollouts analysis](https://argo-rollouts.readthedocs.io/en/stable/features/analysis/)).

Every flag the planner adds comes with the step that removes it, written in the same plan. Flags left on for ever
are the clean-up phase that never happens, in another form.

### Health within bounds

The system map gives each component its health signals: a few queries (error rate, latency at the 95th
percentile, saturation) with the bound each must stay within, usually relative to the same signal before the
deploy. A step can add its own, as production-signal items (section 6). The script runs them through the system
map's `query` command, against Prometheus, Datadog or whatever the project uses. This follows the SRE practice of
treating a canary as "a partial and time-limited deployment of a change … and its evaluation", with the evaluation
deciding whether to continue ([Google SRE workbook, ch. 16](https://sre.google/workbook/canarying-releases/)).

### Rollback, and where the owner's permission sits

One rule: **increasing exposure needs permission; reducing it never does.**

- Deploying to production, moving a flag up, starting a canary, running a backfill in production: each needs the
  owner's yes, or a standing permission in the system map that covers it.
- Turning a flag off, setting a canary's weight to zero, and redeploying the previous commit are always allowed.
  When any health query fails during gates 6 to 8, the script does the first of these that applies, at once, then
  wakes the lead. It doesn't ask first, because asking first is how a bad canary becomes a long outage.

Standing permissions are a table in the system map that only the owner changes:

```markdown
## Standing permissions
| Action | Where | Granted |
|---|---|---|
| Merge after gates 1–3 | all components | yes |
| Deploy | staging | yes |
| Deploy, dark | production | yes, except payments |
| Ramp a flag to 25% | production | yes, while health holds |
| Ramp a flag beyond 25% | production | ask |
| Run a backfill | production | ask |
| Destroy data | anywhere | ask (can't be granted) |
```

A new project starts with every production row set to "ask". The owner loosens it as trust builds, which is how
the brief's "unless they grant standing permission" becomes something the script can enforce.

Small increments come from two places. The step rule makes each pull request small by construction: one
component, one phase. And the ramp makes each exposure small. DORA's research associates small batches with both
higher throughput and lower change failure rate ([DORA, working in small batches](https://dora.dev/guides/dora-metrics/)),
which is the outside support for paying for more steps.

### How "done" is defined, and who records it

- A **step** is Done when the record has a pass, with a receipt, for every gate on its path. Only the script
  writes it.
- A **change** is Done when every step is Done, including every clean-up, contract and drop step, and its end
  condition passes in production. The script records it, and it moves to "recently finished" on the status page.
- A step that was rolled back is not Done; it is **Rolled back**, which counts as a failed round for the escalation
  steps kept from V1 (section 8), and the builder starts again with the failed query's result and the logs.

### Rejected

- **Done means merged, with deployment as the owner's job afterwards.** That was V1's position and today's
  microservice designs', with an `attended` item for the deploy. It was right for one repository on the owner's
  laptop. For a production system it means the set's record says Done for work nobody has seen running, which is
  the very thing the core guarantee exists to prevent.
- **An agent deciding whether a canary is healthy.** Covered in section 2.
- **Rollback needing the owner.** Slower, and turning exposure down is not the kind of irreversible decision the
  owner reserved; it is the reverse of one.

---

## 6. Verification

### What is checked, where, and by whom

| Where | What | Who decides |
|---|---|---|
| The builder's checkout | Everything, as the builder works. Not a gate: the builder's own results are information, not evidence | Nobody (the builder) |
| Preview environment (if the project has them) | The reviewer's inspections | Reviewer |
| CI on the pull request | The project's required checks; contract tests; compatibility against deployed versions | CI; the script reads the results |
| The script's clean checkout of the pull request merged onto the target branch | Every item `check`, as in V1 | The script |
| Staging | The flows through the component | The script runs them |
| Production | Health signals; production-signal items; end conditions | Monitoring, through the script's queries |

### The big change: verify before merging

V1 merges first and verifies after. The builder runs `land`, which runs the test command under a lock and merges
(`agent_loop.py:2606-2618`). Only then does `run` check the claim: it requires the builder's commit to be on the
main branch already (`agent_loop.py:2803`), and runs the item checks in a clean checkout of the main branch's tip
(`agent_loop.py:2814-2817`). The reviewer then judges a commit that is already on the main branch. That was a
sound trade for one repository with a small test command and nothing deployed from main. In a system where main
is deployed, a failed review means a failed change is already on its way to production.

V2 verifies on the pull request, before merging. The script runs the item checks on the pull request's head merged
onto the target branch, CI runs on the same commit, the reviewer judges that commit, and only after gates 1 to 3
does the script merge. If the target branch moves before the merge, the script re-runs gate 1 on the new merge
(or hands the merge to the repository's merge queue, which does the same thing). V1's README listed "merging
through pull requests" as left out until needed (`README.md:563`); in production it is needed, and every forge
already does it.

For a single-repository project with no forge, the same order holds with local branches: the script verifies the
builder's branch rebased onto main in a clean checkout, the reviewer reviews it, and the script fast-forwards main.

### The guarantee, once CI and real environments are involved

"Nothing depends on an agent saying it is finished" survives because every gate's decider is something no agent
in the set can write to:

- **CI results** are read by the script from the forge's API, for the exact commit, and only for the checks the
  branch protection names as required. A builder can't fake a green check. A builder can change what the check
  runs, though, by editing the workflow, the tests or a script a check calls; V1 has the same gap and says so
  (`README.md:455-457`). V2 narrows it: any step whose diff touches CI configuration, deletes or skips a test, or
  changes a file an item's check calls gets an extra reviewer item, "Do these changes weaken what the checks
  test?", added by the script, not the planner. The assessment proposed this scan (`ASSESSMENT.md:169-171`).
- **Deployments and flags** are read from the deploy system and the flag system, which hold their own audit logs.
- **Health** is a query the script runs. Its text is fixed in the system map or in an approved item, so an agent
  can't loosen the bound.
- **Reviews** come from fresh sessions started by the script, as in V1, and are read-only.
- **The record** carries a receipt for every entry. V1 protects its record by rules and by reading git's reflog,
  and says plainly what that misses (`README.md:461-469`). In V2, a forged entry would have to come with a forged
  CI run, deployment or flag change in someone else's system. `audit` re-fetches every receipt; `advance` audits
  the entries it relies on before it acts on them.
- **Agents never hold production credentials.** Deploy, flag and job commands run with credentials the script
  holds (or that CI holds, when the commands trigger CI workflows). Builder and reviewer sessions are started with
  an environment that excludes them, as V1 already strips Claude's API keys (`README.md:497-500`).

What it can't protect against, stated as V1 states its limits: a lead that invents an owner's decision. The
mitigation stays as in V1, the report listing every decision with its words. For owners who want a hard guarantee
on production, the system map can mark the production environment as **owner-signed**: the deploy then goes through
a forge environment whose required reviewer is the owner, and the lead sends them the one link to press. That is
the only point where the owner leaves the chat, and it is their choice
([GitHub environments](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments)).

### Production signals: a fourth way to prove an item

V1 has three proofs: Automated Check, Reviewer Inspection, Reviewer Question (`proofs.md:15-24`). V2 adds a
fourth: a **Production Signal**, a query with a bound and a window, evaluated by the script at a named gate.

```json
{
  "id": "S3.2",
  "statement": "Orders charged through amount_minor succeed as often as before",
  "signal": "charge_success_ratio{path=\"amount_minor\"} >= baseline(charge_success_ratio, 7d) - 0.005",
  "window": "1h",
  "at": "released"
}
```

It is the only way to prove "this works for real users", and it is decided by a machine reading a system no agent
writes to.

### Review by risk, not by kind of proof

V1 sends a milestone to a reviewer if any item is inspected or asked, or if it is the last of its module
(`agent_loop.py:1113-1117`); the assessment showed this is a side effect of how planners write items, and that on
Thrum every milestone ended up reviewed (`ASSESSMENT.md:157-171`). V2 gives each component a **risk** in the system
map (`low`, `normal`, `high`; payments and authentication are high) and each step kind a default. A fresh reviewer
judges every step on a high-risk component, every `contract`, `backfill` and `drop` step, every step the
sensitive-path scan flags, and every step with an inspected or asked item. Other steps pass on checks and CI. The
planner can raise a step's risk, not lower a component's.

### Rejected

- **Trusting CI alone, as Cursor ended up doing at scale.** Cursor removed its central judge and accepted a small
  error rate ([Cursor, Feb 2026](https://cursor.com/blog/self-driving-codebases)), on work that was objectively
  checkable and not, as far as its post says, deployed to paying users each hour. Payments are the opposite case.
- **A script-built sandbox in place of CI.** CI already exists, has the secrets and the services, and is what the
  teams trust. V2 reads it.

---

## 7. What it costs a small project

A small project is one repository, no deploy pipeline, one owner. What it does in V2:

- `SYSTEM.md` with one component, no contracts, one environment (`local`), the path `checks → reviewed → merged`,
  and the test command as its one required check. This is about the size of V1's `ORCHESTRATE.md`.
- One change per request: `BRIEF.md`, `PLAN.md`, `steps.json`. No `DESIGN.md` per module unless a step needs one
  (the plan holds the design for a small change). Thrum's planning files ran to over 11,000 words for a
  one-milestone module (`ASSESSMENT.md:119-121`); V2's single plan per change is meant to cut that.
- No plan review unless the change touches a contract or a high-risk component. Thrum spent 18 of its 24 recorded
  reviews on designs and 6 on milestones (commits titled "review of" on its `origin/main`, counted today; earlier reviews under other titles aren't in that count); a review of each module's
  design on every edit is the largest cost V1 has shown.
- No `advance` timer: with nothing to wait on but builders and reviewers, the lead can call `advance` itself after
  each result, which is V1's rhythm.
- No flags, no ramps, no health queries, no record receipts beyond commits and review files.
- The single-chat route (`README.md:354-355`) stays: interview, plan, build a step, have it reviewed, in one chat.

What a small project pays that V1 didn't: verification before merging, which means a builder waits for its review
before its work reaches main. With two or three builders on separate components this rarely matters; on one
component with steps that build on each other, the builder may start the next step on top of the unmerged branch
("stacked"), and the script re-verifies it once the first merges.

The rule from the brief, "a small project must not pay for machinery it doesn't need", is enforced by the system
map: each mechanism is switched on by a section of it (contracts, environments, flags, health). A section that
isn't there costs nothing, and the planner never adds one without the owner.

---

## 8. What V1 parts are kept, changed or dropped

| V1 part | V2 | Why |
|---|---|---|
| `interview-me`, project brief, owner's words verbatim | **Kept**, per change | The best-tested skill in the set (`README.md:549-556`). |
| `domain-language`, glossary | **Kept** | The owner couldn't follow the build without it (`README.md:198-206`). |
| Items fixed before building; builder can't change them; approved hash | **Kept** | The core idea, best-supported in the field (`ASSESSMENT.md:19-21`; TDFlow, OverclaimBench). |
| Only the script writes the record | **Kept, strengthened** with receipts and `audit` | V1's protection is detection by reflog, with named gaps (`README.md:461-469`). |
| Fresh reviewer who uses the product | **Kept**, now before merge, read-only, structured verdict | `ASSESSMENT.md:186-194`. |
| Review triggered by inspect/ask or last milestone | **Changed** to risk, step kind and a sensitive-path scan | `ASSESSMENT.md:157-174`. |
| Planner says what, builder decides how | **Kept** | `README.md:254-258`. |
| Few builders at once (2–4) | **Kept**, as a cap the script enforces across all repositories | Cohere's measurement (report, multi-agent section). |
| One builder per module, worktree per module | **Changed** to one builder per step, one worktree per step's repository; at most one open step per component unless the plan says two are independent | Components replace modules. |
| Module / milestone | **Replaced** by component and change / step | Section 1. |
| `land` (merge under one lock, test command first) | **Replaced** by the merged gate: CI and the merge queue where the forge has one; V1's lock for a local repository without one | Today's runtime design spent its effort on the lock's throughput; a merge queue is the established answer. |
| `Check:` line | **Changed** to "the required checks", read from the forge, or the local test command for a small project | Use the CI that exists (brief). |
| Escalation steps (same builder, new builder, planner rewrite or diagnosis, owner) | **Kept** as they are in 1.7, with "rolled back" counting as a failed round | They have been debugged on a real deadlock (`deadlock-review-fable.md`) and the counts are working (`agent_loop.py:1142-1153`). |
| Design review once per module, again on any edit | **Changed** to a plan review per change, only when it touches a contract, a high-risk component or the system map; again only if the step order, kinds or contracts change | Thrum: 18 design reviews to 6 milestone reviews. |
| `attended` items | **Kept**, and widened into owner decisions about exposure | Same mechanism, more uses. |
| Lead as dispatcher (`build/SKILL.md`, 5,553 words) | **Changed**: `advance` dispatches; the lead talks and triages | `ASSESSMENT.md:176-184`. |
| `STATUS.md` written by the script | **Kept**, in the control repository, across repositories | `done-when.md:76-80`. |
| Per-host launching, model and effort named on every launch, token use recorded | **Kept** | `README.md:303-305`. |
| Visible app sessions (`ORCHESTRATE_VISIBLE`) | **Kept as an optional adapter**, outside the core | Thrum uses it; it rests on parts of the apps that aren't public (`ASSESSMENT.md:210-213`). |
| Codex quota forecast | **Shrunk** to used-and-reset | `ASSESSMENT.md:204-206`. |
| Multi-lead claim refs, `taken` | **Dropped**; `advance` holds a lock per change | Never needed (`ASSESSMENT.md:214-215`). |
| `ORCHESTRATE.md` plus the `ARCHITECTURE.md` module table | **Merged** into `SYSTEM.md` | Thrum's tables drifted ("(no row in the module table)" on every row of its status page). |
| `adopt`, `migrate` | **Kept** in spirit: one command to land plan files; one to move a V1 project to V2 (modules become components; open milestones become steps of one change) | A V1 project must be able to upgrade. |

The script is the part that changes most. V1's is about 7,200 lines, most of it host handling, record keeping and
verification. V2 keeps the host handling, replaces the merge and record code, and adds the gate engine and the
calls to the system map's commands. The new outside-world code stays small because the script never talks to
Prometheus or Argo itself: it runs commands the system map names, the way V1 already runs any other agent host
through a `Host <name>:` line (`profile.md`, the file template).

---

## 9. Worked example: a breaking change to a payments API

### The system

Three repositories, three teams:

| Component | Repository | Team | Risk | Deploy |
|---|---|---|---|---|
| `payments` | `acme/payments` | Payments | high | Argo CD to Kubernetes, canary through Argo Rollouts |
| `orders` | `acme/orders` | Checkout | normal | Argo CD |
| `invoicing` | `acme/invoicing` | Finance | normal | Argo CD |

The contract: `payments` provides `POST /v1/charges` and `GET /v1/charges/{id}`, described by an OpenAPI file and
verified by Pact against both consumers, with deployments recorded in a Pact broker. Today the request and response
carry `amount`, a decimal number of dollars. `payments` stores it in a `numeric(12,2)` column, `charges.amount`.
The control repository is `acme/delivery`. Standing permissions are as in the table in section 5: payments needs
the owner even for a dark production deploy.

### The owner's request

> "We've had rounding complaints on refunds. Switch charges to integer minor units with an explicit currency, and
> get rid of the decimal amount once everything's moved."

### Talking, then planning (lead, planner)

The lead runs the interview. It reads the code first, finds both consumers and the column, and asks the owner only
what it can't look up: whether outside partners call `/v1/charges` directly (no, says the owner, "not that I know
of"), and how long the old field may live (a month is fine). It writes `changes/0021-exact-amounts/BRIEF.md` with
the request word for word and shows it to the owner, who approves.

The planner writes the plan. It is a review case, because it touches a contract and a high-risk component, so a
fresh reviewer reads it before anything is built, against the brief, and passes it after one round in which it
asked for the backfill to be its own step. The steps:

| Step | Repo | Kind | Needs | What |
|---|---|---|---|---|
| P1 | payments | expand | | Accept and return `amount_minor` (integer) and `currency` beside `amount`. Add column `charges.amount_minor bigint null`, write both on every new charge. Count requests that use `amount`, by caller. Publish the new OpenAPI and provider states. |
| P2 | payments | backfill | P1@production | Fill `amount_minor` for old charges in batches; item: rows where the two disagree = 0. |
| O1 | orders | migrate | P1@production | Send and read `amount_minor`, behind flag `orders.amount-minor`, off. Shadow-compare: compute both, count disagreements. |
| I1 | invoicing | migrate | P2@production | Read `amount_minor` (invoices read old charges, hence the backfill first), behind flag `invoicing.amount-minor`. |
| O2 | orders | build | O1@observed | Remove the flag and the old code path. |
| I2 | invoicing | build | I1@observed | Same. |
| P3 | payments | contract | O2@production, I2@production | Stop accepting and returning `amount`. Stop writing `charges.amount`. |
| P4 | payments | drop | P3@observed | Drop `charges.amount`, 30 days after P3, once a backup of the column is verified. |

The end condition: "`payments_legacy_amount_requests_total` is 0 for 7 days, and `charges.amount` no longer
exists in production."

`O1`'s items, as an example of the four proofs together:

- O1.1 *check*: `make test` covers both paths with the flag on and off.
- O1.2 *check*: the orders consumer pact, including the new interactions, verifies against payments' production
  version (`pact-broker can-i-deploy --pacticipant orders --version $SHA --to-environment production`).
- O1.3 *ask*: "Does every place that reads a charge's amount go through the flag, including the refund path?"
- O1.4 *signal* at `released`: shadow-compare disagreements = 0 over each ramp window.
- O1.5 *signal* at `released`: order checkout success ≥ last week's baseline − 0.5 points.

### P1 in payments

`advance` sees P1 has no needs and starts a builder on it in a worktree of `acme/payments`. The builder adds the
fields, the column, dual writes, the counter, and the tests, and opens a pull request. It ends with `DONE`, which
the script treats as "check now" and nothing more.

- **Checks.** CI runs: unit tests, the migration linter (adding a nullable column passes), provider verification
  of both consumers' pacts from the broker. The script runs P1's item checks on the pull request's head merged onto
  main. Receipts: check-run IDs.
- **Compatible.** The script asks `deployed orders production`, `deployed invoicing production` and the same for
  staging, and runs `can-i-deploy` for payments at the new commit against both environments. Both consumers still
  send only `amount`, which P1 still accepts: pass.
- **Reviewed.** Payments is high-risk, so a fresh reviewer runs the service in the preview environment, sends old-
  and new-shape requests, reads every changed line, and answers P1's ask: "If a request carries both fields and
  they disagree, what happens?" It finds no handling for that and fails P1.2 with one Must Fix. The builder is
  resumed with the finding (the first escalation step), adds a 422 for disagreeing fields, and the second review
  passes. CODEOWNERS for `acme/payments` also requires a person from the Payments team; `advance` waits, and the
  status page shows "P1 waiting on the Payments team's approval". A person approves in GitHub the next morning.
- **Merged** by the script, standing permission. **Staging**: Argo CD deploys; the script reads the deployment and
  runs the "cart to receipt" and "refund" flows against staging: pass.
- **Production, dark.** Payments needs the owner even for a dark deploy. The lead brings it to the chat with the
  staging results; the owner says "go". The script triggers the sync, Argo Rollouts runs its canary with its own
  analysis, the script records the rollout's result as the receipt, and holds 30 minutes on payments' health
  signals: pass. P1 is Done.

### P2, O1 and I1

P1 at production unblocks P2 and O1 together. `advance` starts two builders, one in each repository; the cap is
three.

O1 passes its gates to production dark (standing permission for orders). Then the release: the lead brings the
ramp to the owner in one message (the example in section 2), and the owner approves the whole ramp. The script sets
the flag to 5%. At 25%, O1.4 reads 3 disagreements in the hour: orders computed `amount_minor` with a float
multiply for one currency with three decimal places. The script turns the flag off at once (reducing exposure needs
nobody), records O1 as Rolled back with the query result as the receipt, and wakes the lead, which tells the owner
in two lines: what happened, that it is off, and that the builder has the failing charges. The same builder fixes
it from the query's evidence and a new test; the step goes round its gates again; the ramp runs to 100% and holds
for the observation window (three days, from the plan). O1 is Done.

P2 runs in staging, then asks the owner ("backfill 4.1 million charges in production, in batches of 10,000, about
40 minutes; the job stops if a batch errors"); the owner approves; the script runs it through `run-job`; the item
query reads 0 disagreements. P2 is Done, which unblocks I1.

I1 is built by an agent, but `acme/invoicing` belongs to the Finance team, whose CODEOWNERS rule requires one of
them to approve. The script waits on that gate for two days, and the status page and the daily report say so.
Once approved, I1 goes through the same ramp.

### Clean-up and contract

O2 and I2 remove the flags and the old code paths. They are ordinary steps that pass gates 1 to 6.

P3 needs both at production. Its contract gates: the script confirms the deployed commits of orders and invoicing
in staging and production are at or after O2's and I2's merges, and that the legacy-request counter has read 0 for
7 days. On day 5 it reads 2: a nightly reconciliation job in `orders`, in a different folder, that nobody had
listed, still sends `amount`. The script holds P3; `advance` wakes the lead, which sends it to the planner. The
planner adds O3 (move the job), and P3's `needs` gains `O3@production`. Seven clean days later, the gates pass and
the lead asks the owner to confirm the contract step, with the counter's graph. The owner confirms. P3 goes out
dark, which here means simply deployed, since there's nothing to ramp: old-shape requests now get a 400, and
nobody sends them.

P4 waits 30 days after P3 is observed, then asks the owner, with the backup's verification read-back, before
dropping the column. The owner approves. The end condition passes. The script records change 0021 as Done.

### What the owner saw

Eight messages over about six weeks: the brief, the dark deploy of payments, the orders ramp, the rollback notice,
the backfill, the invoicing ramp, the contract confirmation, and the column drop. Every one was a decision only
they could make or a failure they should know about. Everything else was in `STATUS.md` and the daily report.

---

## 10. Risks and unknowns

### What is untested

All of it, in this form. No version of the orchestrate set has run against a deployed system, CI, a flag system or
monitoring. V1 has one real project, an engine with no deployments (`README.md:316-320`). Every mechanism in sections
3 to 6 is established practice for teams of people (Pact, expand and contract, canaries with automated analysis,
merge queues); none has been measured with agents doing the building, and the combination is untested by anyone.

### What I am guessing

- **That planners can write good step sequences and health queries.** Sequencing a breaking change correctly is
  the expert part of the work. The compatibility gate catches a wrong sequence before production, but a planner
  that keeps writing wrong ones will cost many failed gates. Health queries are worse: a loose bound passes a
  broken change. I mitigate by having the system map hold the component's health signals, which the owner
  approves once, and letting steps only add to them.
- **That signals have enough traffic to mean anything.** A 5% ramp on a service with 200 requests an hour gives a
  query nothing to judge in an hour. The planner has to size windows to traffic, and for low-traffic services the
  honest answer may be "no canary, deploy and watch", which the system map should be able to say.
- **That `advance` on a timer is dependable on an owner's laptop.** For anything deployed, the timer probably
  belongs in the control repository's CI, which brings the question of where the script's credentials live.
- **That verification before merging doesn't slow builders too much.** V1 merged first so builders could build on
  each other quickly. Stacked branches are the answer I gave, and I haven't seen agents handle them well.
- **That the script stays small.** V1's script grew from 3,600 to 7,200 lines in a week (`ASSESSMENT.md:26`;
  `wc -l` today). V2's gate engine is new code with real money behind its mistakes. The design puts every outside
  system behind a project command for that reason, but the gate logic itself is still a lot to get right.
- **That one change per request is the right grain.** A long greenfield build, such as Thrum's engine, would be one
  change with dozens of steps. It should work, but the plan file may grow the way V1's did.

### What would hurt most if wrong

The rollback rule. If the script turns a flag off when it shouldn't (a noisy query), the cost is a delayed ramp. If
it fails to when it should (a query that can't see the failure), the cost is an outage. The second is the one to
test first.

### What to try first

1. **Build the smallest real system and run the worked example end to end.** Three tiny services in three
   repositories on a local Kubernetes (k3d), with Argo CD, a Pact broker, flagd and Prometheus, and real CI on
   GitHub. Plant one fault the shadow comparison should catch, and one unlisted consumer the counter should catch.
   Measure: did each gate stop what it should, how many owner messages, tokens per step and per gate.
2. **Before that, build only the three new pieces without agents**: `needs` on a gate, the deployed-versions
   command, and the compatibility gate. Drive them by hand on the same system. They are the novel part, and they
   can be wrong without any agent being involved.
3. **Run V2's small-project mode on a V1-sized project**, with Thrum's records as the baseline, to see whether a
   single plan per change and risk-based review cut the planning cost the assessment found, and whether verifying
   before merging costs builders time.
4. **Grade the reviewers.** Still undone from V1 (`ASSESSMENT.md:91-94`), and V2 leans on reviewers for every
   high-risk step.

---

## Alternatives rejected at the level of the whole design

- **Extend V1 with a few lines, as today's microservice designs did.** They are the right answer for microservices
  in one repository, where merging is the last step the set controls. Across repositories, with separate
  deployments, the unit of work and the meaning of Done both change, and every lightweight version I tried ended
  with Done meaning "merged" and production as someone else's problem.
- **An agent per repository, with the agents negotiating order between them.** Cognition and Cohere both found
  that agents coordinating with each other is where multi-agent systems lose (the report, multi-agent section). One
  graph in one place, executed by a script, needs no negotiation.
- **Model everything as tickets in an issue tracker.** Familiar to teams, but the tracker becomes the record, and a
  tracker's fields are writable by any agent with the token. Files in git plus receipts from systems the agents
  can't write to give the guarantee; a tracker can still mirror the status page for the teams.
- **Let the owner use the forge's UI for approvals by default.** Stronger guarantee, but it breaks "the owner only
  chats". Kept as an option per environment.

## Sources

- V1: `skills/orchestration/` (README, GLOSSARY, skills and references), `build/scripts/agent_loop.py`.
- Evidence: `workbench/orchestration-review/ASSESSMENT.md`, `reports/Multi agent delivery harnesses 2026.md`,
  `deadlock-review-fable.md`, `microservices/*.md`; Thrum's `origin/main` commit log and `docs/plans/STATUS.md`.
- Fowler, Parallel Change: https://www.martinfowler.com/bliki/ParallelChange.html
- Pact, can-i-deploy: https://docs.pact.io/can_i_deploy ; recording deployments:
  https://docs.pactflow.io/docs/bi-directional-contract-testing/deploying
- Buf breaking change detection: https://buf.build/docs/breaking/
- Confluent Schema Registry compatibility (cited from prior knowledge, not re-fetched today):
  https://docs.confluent.io/platform/current/schema-registry/fundamentals/schema-evolution.html
- Zuul project gating and cross-project dependencies: https://zuul-ci.org/docs/zuul/9.4.0/gating.html ; the
  limitation thread: https://lists.zuul-ci.org/archives/list/zuul-discuss@lists.zuul-ci.org/thread/UGWWG4WXRHXMKVCNIOYFSWVDROTKALWV/
- Google SRE workbook, Canarying releases: https://sre.google/workbook/canarying-releases/
- Argo Rollouts analysis (official docs page cited from prior knowledge; the search returned secondary guides):
  https://argo-rollouts.readthedocs.io/en/stable/features/analysis/
- OpenFeature: https://openfeature.dev/
- GitHub deployment environments and protection rules:
  https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments
- Stripe, APIs as infrastructure: https://stripe.com/blog/api-versioning
- DORA metrics and small batches: https://dora.dev/guides/dora-metrics/
- Cursor, self-driving codebases: https://cursor.com/blog/self-driving-codebases
