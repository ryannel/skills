# Orchestrate V2: a design for production systems in several repositories

Designer: Claude Fable 5.2, 11 November 2026. Written from `BRIEF.md` in this folder. Nothing under `skills/` or in
`~/Workspace/thrum` was changed. Line numbers for V1 are from the working tree of branch `orchestrate-1.6.4`
(`agent_loop.py` is 7,243 lines there). Thrum counts are from `origin/main` at `7af30c68`.

**Nothing in this design has been run.** Every part of it is a proposal. Where a part rests on something V1 showed,
or on published practice, the text says so. Where it is my guess, it says that too.

## The short version

V1 answers one question well: how do we know a piece of work is finished without believing the agent that built it?
Its answer is to write down what "finished" means before building, keep that out of the builder's hands, and have a
script and a new reviewer check it. V2 keeps that answer and asks the same question about more facts. In
production the facts are no longer only "the tests pass". They are also "it is merged", "it is running in
production", "every user is on it", "it is healthy", and "the old path is gone". V2 treats each of those the same
way V1 treats a test: it is written down beforehand, and the script reads it from a system the agents cannot write
to.

Five choices carry the design:

1. **Work is grouped by the change the owner asked for, and split into steps that are each released alone.** V1
   groups work by module. In production the hard part is the order of work across modules, so the plan follows the
   change.
2. **Production is one more place where an item is proved.** V1 items already name a place, such as a browser or a
   phone. V2 adds staging and production to that list. "Done" keeps one meaning: every item proved, in the place it
   names, by the script.
3. **One home repository holds every plan and the record.** The service repositories receive only pull requests
   with code in them. A builder cannot change what "finished" means, because that file is not in the repository it
   works in.
4. **Agents hold no production access.** A builder's only output is a pull request. A reviewer's only output is a
   verdict. Releases go through the project's own pipeline, and the owner's permission sits in front of it.
5. **A script moves the work forward, on a timer. The lead only talks.** A release that is watched for a day
   outlasts any chat, so the part that waits has to be code.

## 1. The model

### The terms, each defined before it is used

**Owner.** The person the work is for. As in V1.

**Module.** A part of the system that has its own code, its own tests and, usually, its own release: a service, a
web front end, a shared library. This is V1's module with three facts added: which repository and folder it lives
in, how it is released, and how to tell whether it is healthy. V1 defines a module as what "one builder can work on
without touching the other parts" (`GLOSSARY.md:72-74`), and that stays true.

**Home repository.** The one repository that holds the plans, the settings and the record for the whole system. In
a project with one repository, the home repository is that repository, and nothing new is created.

**Contract.** A file that says what one module provides to others: an OpenAPI file for an HTTP API, a `.proto`
file, an event schema, a database schema that another module reads. Each contract has one module that owns it and a
list of the modules that use it. This is V1's "interface" (`GLOSSARY.md:79-81`), required to be a file a tool can
compare.

**Change.** One thing the owner asked for, such as "charge amounts in whole pence, not decimals". A change has a
brief the owner approved, a plan, and a record. It replaces V1's project as the unit that is planned, because a
production system is never finished, and what the owner follows is each request.

**Step.** One small piece of a change that touches one module, is merged alone, is released alone and can be undone
alone. It replaces V1's milestone. A step does one of three kinds of work:

- a **build step**: a builder writes code and opens one pull request;
- an **operation step**: the script runs one command from the module's list of allowed operations, such as "run
  the backfill job" or "set this flag to 10%";
- a **watch step**: nobody does anything, and the script measures something for a stated time, such as "nobody
  has called the old endpoint for seven days".

**Item.** One thing that must be true before a step is Done. As in V1, the planner writes it before building, it
says how it is proved (an Automated Check, a Reviewer Inspection or a Reviewer Question), and it names where it is
proved.

**Target.** Where an item is proved. In V1 a target is a device or platform (`GLOSSARY.md:61-65`). V2 adds the
places a production system runs: the builder's machine, the module's CI, a preview, staging, and production. A
**preview** is a temporary copy of the system started for one pull request.

**How a step is undone.** One line on every step, written by the planner: "turn the flag off", "release the
previous version", or "it cannot be undone". A step that cannot be undone always goes to the owner.

**Things to remove later.** Anything a step adds that is meant to be temporary: a feature flag, a field kept for
old callers, code that writes to two places. The plan lists each one beside the step that will remove it.

**Record.** The file that says what is true about each step, which only the script writes. As in V1, with one
addition: every fact in it names where the script read it from.

**Standing permission.** A line in the settings where the owner has said "you may do this without asking me each
time". Without one, the script asks.

### What state each concept owns

| Concept | What it holds | Who writes it |
|---|---|---|
| Home repository | Settings, the module table, the glossary, every change, the status page | Planner and lead write plans; the script writes the record and the status page |
| Module | Its code, its contracts, its CI, its release pipeline | Builders, through pull requests |
| Change | The brief, the plan, the done-when file, the record, the reviews | Lead writes the brief; planner writes the plan and items; script writes the record |
| Step | Its items, how it is undone, which steps it needs, its things to remove later | Planner. Fixed once approved |
| Record | For each step: the pull request, the commit merged, the checks and where each result came from, the reviews, each release and what was measured, each permission the owner gave | The script only |

### What "done" means

A step is **Done** when every one of its items has been proved on the target it names, and the script has recorded
it. That is V1's rule (`done-when.md:258-272` in the references), unchanged.

What changes is which items a step has. For a module that is released to production, the script adds two items to
every build step, so the planner doesn't have to write them each time:

- the commit that was merged is running in production for every user;
- the module has been healthy for its observation period since then. The **observation period** is how long the
  module's settings say to watch after a release, such as 30 minutes.

So for such a module, a step is not Done at merge. It is Done when it is live and has been watched. A module that
has no release, such as a library or a small project with no pipeline, gets neither item, and its steps are Done at
merge exactly as in V1.

A change is **Finished** when every step is Done and nothing is left on its list of things to remove later. The
script refuses a plan in which something to remove later has no step that removes it. That one rule is how "the old
path is removed" becomes part of done, and it is aimed at a failure the pattern's own authors name: if the removal
never runs, "you can end up worse off than before" ([Parallel Change, Danilo Sato](https://martinfowler.com/bliki/ParallelChange.html)).

### A step's statuses

| Status | Means |
|---|---|
| Not Started | Nothing has happened yet |
| Waiting | A step it needs is not Done yet. The status page names it |
| Being Built | A builder is working on it, or an operation is running |
| Being Checked | The pull request is open. CI, the script's own checks and, where the plan asks, a reviewer are judging it |
| Approved | Everything passed. It is waiting to be merged or released, usually for the owner's permission |
| Being Released | It is merged and moving through environments. The status page says where, such as "production, 10% of users, healthy, since 14:00" |
| Done | Every item is proved |
| Undone | A release went wrong and the script undid it. The step goes back to a builder with what was measured |
| Blocked | Something it needs is missing. The status page says what |
| Needs the Owner | It waits for a decision or a permission |

There is no "Ready for Review". In V1 that status meant "the builder says it is finished, and nobody has verified
it" (`GLOSSARY.md:199`). In V2 a builder never says so. The pull request exists or it doesn't, and its checks have
passed or they haven't.

### What replaces what

| V1 | V2 | Why |
|---|---|---|
| Project | The system (long-lived) and a change (one request) | A production system has no end, and the owner follows requests |
| Module | Module, plus where it lives, how it is released and how its health is read | Same idea |
| Milestone, grouped under a module | Step, grouped under a change, naming its module | Order across modules is the hard part |
| Done-when item | Item, unchanged | The best-supported part of V1 |
| Target (device or platform) | Target (also CI, preview, staging, production) | Lets "done" keep one meaning |
| Ready for Review | Being Checked | Nothing rests on the builder's claim |
| Done (merged, checks pass) | Done (every item proved where it names); Finished for a change | Honest end state |
| `needs` between milestones | `needs` between steps: the needed step must be Done, which for a released module means live | One rule gives the release order |

## 2. Who does what

### The agents

There are still four kinds of agent and one script. No new kind of agent is added.

**The lead** is the agent the owner chats with. It finds out what the owner wants and writes the brief, as in V1's
`interview-me`. It tells the owner what is waiting on them and records their answers in their own words. It may
read everything. It may not write code, judge work, merge, release, or decide anything on the owner's list.
What changes from V1: it no longer keeps the build going. V1's lead reads each result and runs the next command,
and its skill is 5,553 words, most of it a table from results to commands. The assessment called this "an LLM doing
a scheduler's job" (`ASSESSMENT.md:176-182`). In V2 the script does that.

**A planner** writes a change's plan and items in the home repository. It may not touch code, the record, or the
settings' permission lines. It cannot ask the owner anything, which is why the brief comes first, as in V1.

**A builder** builds one build step. It works in a checkout of one module's repository, on a branch, and its whole
output is one pull request. It may not merge, release, run an operation, or write to the home repository. It
doesn't mark items as passed, which removes V1's builder fields and the checks on them
(`done-when.md:284-287`).

**A reviewer** is a new session that has seen none of the work. It reads the pull request, starts the product in a
preview and uses it. It writes nothing to any repository. It returns a verdict in a fixed form (each item: pass,
fail or could not judge; each finding: must fix or suggestion), and the script writes that down. This is the
assessment's finding 6 (`ASSESSMENT.md:184-194`), which V1 has not yet built. A reviewer also reads a plan before
building, but only for the changes listed in section 6.

### The script

The script is not an agent. It gains one command that replaces the lead's table, here called `advance`. Each time
it runs, it reads the record, each pull request's checks and each environment's state, moves every step that can
move, and stops. It is safe to run at any moment and any number of times, because it reads the real state each time
and stores no plan of its own. It:

- starts builders, reviewers and planners, as V1's script does, with at most two to four builders at once;
- opens and merges pull requests;
- runs Automated Checks itself, and reads CI results from the code host for the exact commit;
- asks the module's pipeline to release, when permission exists;
- reads which commit is running in each environment, and whether the module is healthy;
- undoes a release that fails its health checks;
- writes the record and the status page.

A timer on one machine runs `advance` every few minutes, so work continues when no chat is open. The lead also runs
it when the owner asks for something.

### How the owner is reached

The owner only chats. Three things make that work when a release takes hours or days:

1. **The status page** in the home repository opens with "Waiting on you", as V1's does. Every question there
   carries what the script knows, the choices, and what happens if nobody answers.
2. **A notification.** The settings name one command that sends the owner a short message, such as a post to a
   chat channel, saying that something is waiting and to open the chat. It is one-way. No decision is taken there.
3. **Nothing safe waits for the owner.** Undoing a failed release is the safe direction, so by default the script
   does it at once and tells the owner afterwards. The owner is asked before going forward, never before going
   back.

The lead records each answer with the script's `owner` commands, in the owner's words, as V1 does. V1's limit still
holds: the script cannot tell an owner's decision from one a lead invented, so the report lists every decision
recorded in the owner's name (`README.md:481-485`). Section 5 adds a second lock for the decisions that matter
most.

## 3. Several repositories

### Where things live

```
home repository
  ORCHESTRATE.md      settings: the modules, the permissions, how to notify the owner
  SYSTEM.md           the module table: each module, its repository, its contracts and who uses them
  GLOSSARY.md
  STATUS.md           the owner's page, written by the script
  changes/
    2026-11-minor-units/
      BRIEF.md        the owner's request, word for word, and what they approved
      PLAN.md         the steps in order, a short paragraph each
      DONE.json       each step's items, how it is undone, what it needs
      RECORD.json     written by the script only
      reviews/
  system/             the command that starts the whole system, and the tests of flows that cross modules

each module's repository
  the code, its own tests, its own CI, its own pipeline
  nothing of ours, except optionally one line in its README saying where the plans are
```

I chose one home repository over three other arrangements:

- **Plans in every repository, with an index.** Rejected. Nobody has one view, and the record would be written in
  several places by commits to repositories other people share. On Thrum, 381 file changes were plans and evidence
  against about 70 of code (`ASSESSMENT.md:58-59`). A team that owns a service will not accept that in their
  history.
- **An issue tracker or a database as the store.** Rejected. Files in git are the one part of every harness that
  nobody has removed (`Multi agent delivery harnesses 2026.md:400`), and a tracker can be edited by anyone with
  the page open. The script does link each step to its pull request.
- **One repository holding the others as submodules.** Rejected as a requirement. The script clones each module's
  repository into a working folder when a step needs it. The home repository names repositories; it doesn't
  contain them.

The home repository gives a property V1 doesn't have. V1 lets the builder edit the done-when file and then checks
that it changed only its own fields (`README.md:383-387`). In V2 the done-when file is in a repository the builder
has no checkout of and no permission to push to. With a code host that supports it, the home repository's main
branch accepts pushes from the script's own account only. V1 says its record is "protected by rules and by
detection, not by cryptography" (`README.md:461`). V2 can do better wherever the code host can enforce it, and falls
back to V1's detection on a laptop with no code host.

The `system/` folder is the idea all three microservice designs reached: how the modules run together needs an
owner (`microservices/unified-design.md:26-34`). In V2 the home repository is that owner. It holds the command
that starts every module on one machine with a chosen version of each, and the tests of flows that cross modules.
It is a module like any other, and steps can change it.

### How work that spans repositories is ordered

By one rule, which is V1's rule with "Done" meaning more: **a step starts only when every step it needs is Done.**
For a released module, Done means live and watched. So if the orders service must not send the new field until the
payments service accepts it in production, the orders step needs the payments step, and the script will not start
it earlier.

There is no merging of several repositories at once. GitHub has no way to do it
([GitHub's guidance on several repositories](https://wellarchitected.github.com/library/architecture/recommendations/implementing-polyrepo-engineering/)),
and it would not help if it had, because merging together is not releasing together. Each module rolls out on its
own, and for minutes or hours old and new copies run side by side. GitLab's engineering guide puts it as "Updating
GitLab is not atomic" and lists seven outages that came from forgetting it
([GitLab, multi-version compatibility](https://docs.gitlab.com/development/multi_version_compatibility/)). So every
step must be safe to release alone, with every other module at the version it is running now. Section 4 says how
the plan gets that property and how it is checked.

A second rule keeps releases small: **one step per module is in progress at a time.** A step holds its module from
the moment a builder starts until it is Done or Undone. Each release then carries one step, and if health drops,
there is one suspect. This is V1's "one builder per module" (`README.md:260-266`) carried through to the release.
A watch step holds nothing, so seven days of measuring don't stop other work on the module.

I rejected a faster rule, where a step may be built once the step it needs is merged, and merged once that step is
live. It saves waiting. It also leaves pull requests open against code that is not yet running anywhere, and adds
a second meaning of "needs" to explain. If trials show waiting is most of a change's time, this is the first rule
to revisit.

### One view of status

`STATUS.md` in the home repository, written by the script on every change it records, as V1's is. It opens with
what is waiting on the owner, then each change in progress with one line per step. Because the script reads pull
requests and environments each time it runs, the page says what is true even when a person merged or released
something by hand.

### Modules the owner's agents don't control

Another team's service is a module whose settings say `Ours: no`. A step there is a pull request the script opens
and then waits on, or, if even that isn't welcome, a request the owner makes of that team. The status page shows
it as waiting on that team. The script still reads that module's running version and, if it has access, its use of
the old path. Where it has no access, the owner tells the lead what the other team said, and the record marks that
fact "the owner said" (section 6).

## 4. Backwards compatibility and data

### The rule the planner follows

A change that would break a caller is never one step. It is planned as the three phases that current practice
calls expand, migrate and contract ([Parallel Change](https://martinfowler.com/bliki/ParallelChange.html); GitLab
requires the three to ship in different releases, [same guide as above](https://docs.gitlab.com/development/multi_version_compatibility/)).
In this design's plain terms:

1. **Add the new form beside the old.** The owning module accepts and returns both. This step also adds a count of
   how often the old form is used and by whom, because that count is the only proof that removal is safe when some
   callers are unknown.
2. **Move each user of the contract**, one step per module, each in its own repository. They can run in parallel,
   since each needs only step 1.
3. **Watch** until the count of old-form use has been zero for a stated time.
4. **Remove the old form.** The old form goes on the list of things to remove later in step 1, so the script won't
   accept a plan that lacks this step.

The microservice designs had the owner confirm, by hand, that nothing still used the old form
(`microservices/unified-design.md:116-119`). V2 measures it. The owner is still asked before a removal that can't
be undone.

### How the rule is checked without believing anyone

Three checks, all run by a tool, none by an agent's reading:

- **A comparison of the contract file.** Tools exist that compare two versions of a contract and exit non-zero on
  a breaking difference: [`buf breaking`](https://buf.build/docs/breaking/) for Protobuf, `oasdiff` for OpenAPI,
  and a schema registry's compatibility check for events. The module's settings name the tool. The script compares
  the pull request's contract against the version that is **live**, and refuses a breaking difference unless the
  step is a removal step whose needed steps are all Done. Comparing against live, and not only against the main
  branch, is the point: the main branch can be several releases ahead of production.
- **The users' own tests against the new provider.** The script starts a preview with the pull request's version
  of the changed module and the live version of every other module, and runs the flow tests in `system/`. This is
  the same question Pact's `can-i-deploy` asks, "has this version been verified against what is in that
  environment now" ([Pact, recording deployments](https://docs.pact.io/pact_broker/recording_deployments_and_releases)).
  A project that already uses Pact names `can-i-deploy` as the check. V2 doesn't require Pact; it requires that
  the live versions are an input.
- **The count of old-form use**, read from the metrics system, for the watch step.

### Events

Events differ in one way: a message written last week may be read next week. So the plan says which side moves
first, and the schema registry's mode enforces it. Under the default mode, `BACKWARD`, readers are upgraded before
writers ([Confluent, schema evolution](https://docs.confluent.io/platform/current/schema-registry/fundamentals/schema-evolution.html)).
An event step also carries an item that replays kept old messages through the new reader in a preview.

### Databases with live data

A schema change follows the same phases, inside the module that owns the data, with these additions:

- **The schema change that adds comes first and only adds.** Then releasing the previous version of the code is
  always possible, because old code ignores a new column.
- **Copying old data into the new shape is its own operation step.** It runs in batches, can be stopped and
  resumed, and has an item that proves the result, such as "no row has a new value that disagrees with its old
  one". Stripe's account of this pattern (write to both, switch reads, switch writes, remove) compares the two
  sources while both exist and raises an error when they differ
  ([Stripe, online migrations at scale](https://stripe.com/blog/online-migrations)).
- **Reading from the new shape and stopping writes to the old are separate steps**, each undone by releasing the
  previous version.
- **Dropping the old column or table is last, alone, and cannot be undone.** Its items include a backup taken and
  a restore tried in staging. The owner is asked every time.

The planner orders the steps so that everything before the last one can be undone. A design reviewer checks that
ordering (section 6), because it is the one place where a wrong plan loses data.

## 5. Delivery in small, low-risk increments

### From merge to production

Each module's settings say how it is released. Four lines carry it:

| Line | What it says | Examples |
|---|---|---|
| `Merge` | How code reaches the main branch | `pull request`, or `direct` for a repository with no CI, which is V1's `land` |
| `Release` | How a merged commit reaches each environment | `none`; `on merge` (the pipeline releases by itself); `command: gh workflow run release.yml` |
| `Running version` | A read-only command that prints the commit running in an environment | a request to the service's `/version` address |
| `Healthy` | A read-only command that exits 0 when the module is within its limits over the last N minutes | a query against the metrics system for error rate, latency and one business number |

The script uses the project's pipeline and doesn't replace it. If the platform already rolls out gradually and
judges the result, as Argo Rollouts does, where a failed analysis sets the new version's share of traffic back to
zero ([Argo Rollouts, analysis](https://argo-rollouts.readthedocs.io/en/stable/features/analysis/)), then the
script only reads the outcome. If the platform has nothing, the script does the plain version: release, run
`Healthy` on a timer for the observation period, and undo on failure. It doesn't compare a new version against the
old one statistically. A project that needs that should use a platform that does it.

### Feature flags

A flag separates releasing code from turning behaviour on. V2 uses flags and doesn't require them. A build step
may put its behaviour behind a flag; the flag then goes on the list of things to remove later, and widening it
(staff, 10%, everyone) is done by operation steps or as stages of the step's release. A small change whose way of
being undone is "release the previous version" needs no flag. The planner chooses, and says why in one line. The
rule is only that every step says how it is undone, and that the way is real: for a step that touches data or a
contract, an item proves the undo in staging before production.

### Step size

V1 sizes a milestone to "what one builder session can finish unaided, which for current models is hours of work"
(`plan-module/SKILL.md:178-181`), because each milestone has a fixed cost. Production practice pulls the other way.
DORA's guidance is that small batches counter the instability that AI-written code brings, and warns that AI tools
"tend to generate large changes" ([DORA, working in small batches](https://dora.dev/capabilities/working-in-small-batches/);
the page cites its reports and gives no figure). V2 holds both:

- **Before a module serves users**, steps are as large as a builder session, as in V1. Nothing is at risk.
- **Once it serves users**, a step is the smallest change that can be released and undone by itself, and whose
  effect on health can be told from another's.

To keep small steps cheap, the per-step cost has to fall. Section 6 says which steps skip a reviewer, and section 7
what a step costs.

### Where the owner's permission sits

The settings hold one table. The planner fills it from the brief, and only the owner changes it.

| Action | Default | Can the owner give standing permission? |
|---|---|---|
| Open a pull request, start a preview | Allowed | Not needed |
| Merge, where merging doesn't release | Allowed once the checks and any review pass | Not needed |
| Release to staging | Allowed | Not needed |
| Release to production, or widen a release there, for a step that can be undone | Ask each time | Yes, per module |
| Undo: turn a flag off, release the previous version | Allowed, and the owner is told at once | The owner can switch it to "ask" |
| Any step that cannot be undone | Ask each time | No. Always asked, with the items and the evidence |
| Run an operation in production | Ask each time | Yes, per named operation |
| Spend beyond the budget in the settings | Ask | Yes, by raising the budget |

Two things make the permissions more than words:

- **Agents have no credentials for production.** The builder's access is one repository, to push a branch. The
  script's own access to production is read-only: the running version and the health queries. A release happens
  in the project's pipeline, which holds the credentials. This follows the lesson of April 2026, when a coding
  agent on a staging task deleted a production database and its backups in one call because it could reach them;
  the analyses agree that rules in a prompt are advice and the control has to sit outside the model
  ([NHI Management Group](https://nhimg.org/articles/ai-coding-agents-need-external-authorization-not-prompt-rules/);
  [Mondoo](https://mondoo.com/blog/5-lessons-from-9-seconds-ai-agent-deleted-production-database); these are
  vendor write-ups, not an official account).
- **For anything that cannot be undone, the pipeline asks the owner too.** Code hosts can require a named person's
  approval before a job runs against an environment
  ([GitHub, controlling deployments](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/control-deployments)).
  With that set, a lead that invented an owner's "yes" still could not drop a table. This closes, for the worst
  cases, the gap V1 admits (`README.md:481-485`). It costs the owner one tap outside the chat, for those steps
  only. I think that is the right exception to "the owner only chats", and it is the owner's to refuse.

Operations are a closed list. The settings name each allowed operation and its command. A planner can put
"run `backfill-amounts`" in a plan; it cannot write a new command there.

### When a release goes wrong

If `Healthy` fails during the observation period, the script undoes the step in the way the step says, checks that
health returns, sets the step to Undone, and tells the owner. It then holds the module: nothing else is merged or
released there until it is healthy. The step goes back to a builder with what was measured. If the undo itself
fails, the script stops everything on that module and notifies the owner as urgent. It doesn't improvise.

The owner can say "stop" in the chat at any time, and the lead runs one command that halts every merge and release.

### Who records done

Only the script. It sets a step to Done when the last item is proved, and the record says, for each item, what was
run or read, when, against which commit, and from where.

## 6. Verification

### The guarantee, restated for production

V1's guarantee is "nothing in this process depends on an agent saying so" (`README.md:173-174`). It holds in V1
because the script re-runs every check in a clean copy (`agent_loop.py:2769-2783`). Once CI and real environments
are involved, the script can't re-run everything. So the guarantee becomes:

> Every fact in the record was read by the script from a system that no builder, reviewer or planner can write to,
> and the record names that system.

There are four possible sources, and the status page shows them in plain words:

| Source | Means |
|---|---|
| the script ran it | The script ran the command itself, in a clean copy or a preview |
| CI reported it | The script read the result for this exact commit from the code host |
| the environment reported it | The script read the running version, or a health query, from staging or production |
| the owner said it | The owner told the lead, and the lead recorded their words |

Nothing in the record has the source "an agent said it".

### What is checked, where, and by whom

| What | Where | Who | Source in the record |
|---|---|---|---|
| The module's own tests, lint and build | The module's CI | CI, on the pull request | CI reported it |
| That CI really ran: each check named in the settings exists and passed for this commit | The code host | The script | CI reported it |
| The step's Automated Checks | A clean copy, or a preview | The script | the script ran it |
| The contract comparison against the live version | A clean copy | The script | the script ran it |
| Flows across modules, with every other module at its live version | A preview | The script | the script ran it |
| Reviewer Inspections and Questions | A preview | A new reviewer | the reviewer's verdict, with the commit it judged |
| That the merged commit is running | Staging, then production | The script | the environment reported it |
| Health for the observation period | Production | The script | the environment reported it |
| The step's own production items, such as "old-form use is zero" | Production | The script | the environment reported it |
| Anything only a person can judge | Wherever they look | The owner | the owner said it |

### The ways a builder could still cheat, and what stops each

- **Weakening CI in its own pull request.** A builder can edit the workflow file or delete a test. Three guards:
  the list of required check names lives in the home repository, so a check that vanished is a failure; the step's
  own Automated Checks are in the home repository and run by the script; and the script scans every pull request
  for edits to CI files, deleted or skipped tests and changed check scripts, and sends any hit to a reviewer. The
  scan is the assessment's finding 4 (`ASSESSMENT.md:169-174`). V1 names this gap and leaves it open
  (`README.md:455-457`).
- **A release that isn't the reviewed commit.** The script compares the running commit with the merged one. Where
  the project signs what it builds, the script can also verify that the running artefact was built from that
  commit by the pipeline ([GitHub, artifact attestations](https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations)).
  That is optional.
- **A health check that always passes.** `Healthy` is in the settings, which builders can't change. The planner
  rule is that it must fail when the module is broken, and the first step of any module's life in V2 proves it by
  breaking a staging copy on purpose.

### When a reviewer is used

V1 sends a milestone to a reviewer when any item is an inspection or a question, or when it is the module's last
(`done-when.md:228-230`). On Thrum that meant every milestone (`ASSESSMENT.md:56-57`). With steps this small, a
reviewer on each would cost more than the building. So in V2 the planner decides per step, and the script
overrides it upward in three cases. A step is reviewed when:

- the planner marked it, because it is at the edge of what the builder can do;
- it has an item that is a Reviewer Inspection or Question;
- it touches a contract or stored data, or it cannot be undone;
- the scan above found something.

Everything else is Done on checks. Each change gets one review at the end, of the whole change running in
staging or production, by a reviewer who uses the product. That is the shape Anthropic kept: one pass at the end
(`Multi agent delivery harnesses 2026.md:173`).

A plan is reviewed before building only when the change crosses modules, touches a contract or stored data, or has
a step that cannot be undone. That review reads the brief and the plan and answers fixed questions: is every step
safe with every other module at its current version, can each be undone as it says, and does everything temporary
have a step that removes it? A change inside one module with only undoable steps has no plan review. This is the
largest cut to V1's cost. Of the 57 commits the script has made on Thrum's main branch under its present message
format, 18 are design reviews (6 asked for changes), 9 approve a plan, and 6 are milestone reviews (1 failed). The
reviews did find things, so the cut is a bet, and the first trial should record what a skipped plan review missed.

### When a step keeps failing

V1 has five stages after a failed review (`README.md:114-120`), and they are its own practice, with nothing
published behind them (`README.md:290-293`). V2 keeps the order and counts once: the same builder twice, a new
builder once, then a planner who reads every round and answers one of four things (the plan is wrong, the builder
is, the reviewer is, or the owner must decide), then the owner. A release that had to be undone counts as a failed
round. This is the shape the deadlock review recommended (`deadlock-review-fable.md:135-141`).

## 7. What it costs a small project

Take a command-line tool or a small web app in one repository with no pipeline.

| Part of V2 | What the small project does |
|---|---|
| Home repository | It is the project's repository. Plans sit in `docs/plans/`, as now |
| Module settings | One module. `Merge: direct`, `Release: none`. No `Healthy`, no `Running version` |
| Contracts | None listed, so no comparison runs |
| Preview, staging, production targets | Not listed, so no item can name them and the two added items never appear |
| Permissions table | The one line V1 has: may agents push |
| Steps | As large as a builder session. Done at merge, after the script re-runs the checks in a clean copy, exactly as V1 |
| Plan review | None, unless the planner asks. V1 requires one per module |
| Reviewer | Once at the end of the change, and on any step the planner marks |
| Timer | Not needed. The lead runs `advance` while the chat is open |
| Files per change | `BRIEF.md`, `PLAN.md`, `DONE.json`, and the script's record: three written by agents, against V1's four per module plus the project's four (`plan-module/SKILL.md:49-60`) |

So a small project pays for less than it does in V1: no design review by default, no builder-edited fields to
validate, no lead running a table. And as V1 already says, a job small enough for one chat should use none of this
(`README.md:243-245`). That stays the first line of the README.

Each production part switches on by a line in the settings, and each has a cost the owner can see:

| The owner adds | What switches on |
|---|---|
| A second repository | A separate home repository, and the script's own account |
| `Merge: pull request` | The script waits on CI and reads its results |
| A contract in `SYSTEM.md` | The comparison against the live version, and the planner's add, move, watch, remove rule |
| `Release` and `Running version` | The item "the merged commit is running", and release order between steps |
| `Healthy` | The observation period and automatic undo |
| A flag or operations command | Operation steps |

## 8. What is kept, changed and dropped from V1

### Kept

- **Items written before building, which the builder can't change.** The best-supported idea in the field
  (`ASSESSMENT.md:19-20`). Made stronger: the file is now out of the builder's reach.
- **The script re-runs checks and is the only writer of the record.** Extended to CI results and environments.
- **A new reviewer who uses the product.** Now in a preview.
- **The planner says what, the builder decides how** (`README.md:254-258`).
- **Files and git for all state.**
- **Two to four builders, one per module** (`README.md:260-266`).
- **The owner chats; the lead interviews first; the brief and glossary.** `interview-me` and `domain-language` are
  unchanged.
- **Both hosts, with model and effort named at every start.**
- **Taste-led work**: the owner picks from options, references, critique rounds. Unchanged, and outside this
  brief's subject.

### Changed

- **Milestones under modules become steps under changes.** Reason: order across repositories.
- **Done means proved where the item says, including production.** Reason: the brief's honest end state.
- **The lead stops driving.** `advance` on a timer replaces the lead's table. Reason: finding 5 of the assessment,
  and releases that outlast a chat.
- **The builder outputs a pull request and nothing else; the reviewer outputs a verdict and nothing else.**
  Reason: finding 6, and it removes the largest group of "invalid" results.
- **Review by risk, not by kind of proof.** Reason: finding 4, and Thrum's 18 design reviews.
- **Merging goes through pull requests and the project's CI**, where they exist. V1 lists this as left out
  (`README.md:563`). Its one lock around a merge and the test command (`agent_loop.py:2602-2620`) remains only for
  `Merge: direct`.
- **Protection of the record moves from detection toward enforcement**, where the code host allows it.
- **Fewer plan files.** One plan and one done-when file per change. V1's separate design file and log go: the
  plan's first paragraph is the design, and history is in the record and in git. Thrum's one-milestone module with
  over 11,000 words of plan (`ASSESSMENT.md:54-55`) is the case this answers.
- **The stages after a failed review** are counted once.

### Dropped

- **Ready for Review as a claim**, and the builder's `status` and `evidence` fields.
- **The lead's result table** (`build/SKILL.md`, most of its 5,553 words).
- **Design review of every module** before building.
- **Showing sessions inside the desktop apps** as part of the core. It rests on interfaces that aren't public
  (`README.md:516-519`). Keep it as an optional add-on, as the assessment suggested (`ASSESSMENT.md:210-213`).
- **The quota forecast**, reduced to "used, and when it resets" (`ASSESSMENT.md:205-206`).
- **Marks that let several leads share one project.** The script's own account and the timer's single machine
  replace them.

I expect the script to end up smaller than 7,243 lines in its agent-handling half and larger in a new half that
reads code hosts and environments. I have not estimated either.

## 9. Worked example

**The system.** Three services in three repositories. `payments` owns `POST /charges`, whose request and response
carry `amount` as a decimal number of pounds, stored in a decimal column. `orders` and `billing` both call it.
All three release to production through their own pipelines. A fourth repository, `shop-home`, is the home
repository. The owner has given standing permission to release undoable steps to production for `orders` and
`billing`, and not for `payments`.

**The request.** The owner tells the lead: "We had a rounding bug on a refund. I want amounts as whole pence
everywhere, and the decimal field gone."

**The conversation.** The lead reads `SYSTEM.md` and sees that `orders` and `billing` use the charges contract. It
asks what the owner can't look up: is anyone outside these three calling the API (the owner thinks not, and isn't
sure), and how long must the old field stay once nobody uses it (a week). It writes the brief with the request
word for word and shows it. The owner approves.

**The plan.** The script starts a planner. It writes ten steps, shown here in nine rows:

| Step | Module | Work | Needs | How it is undone | To remove later |
|---|---|---|---|---|---|
| 1. The API accepts and returns `amount_minor` beside `amount`, stores both, and counts old-form calls by caller | payments | build | | release the previous version | `amount` in the API (step 8); the old column (step 9) |
| 2. Every existing charge has `amount_minor` filled in | payments | operation: `backfill-amounts` | 1 | nothing to undo; the new column is unused | |
| 3. Orders sends and reads `amount_minor` | orders | build, behind flag `minor-units` | 1 | turn the flag off | the flag (step 7) |
| 4. Billing sends and reads `amount_minor` | billing | build, behind flag `minor-units` | 1 | turn the flag off | the flag (step 7) |
| 5. Payments reads from the new column | payments | build | 2 | release the previous version | |
| 6. Nobody has used the old form for seven days | payments | watch | 3, 4, 5 | nothing to undo | |
| 7. The flags are removed from orders and billing | orders, then billing (two steps) | build | 6 | release the previous version | |
| 8. `amount` is removed from the API, and payments stops writing the old column | payments | build | 6 | release the previous version (the column is still there) | |
| 9. The old column is dropped | payments | operation: `migrate` | 8 | **cannot be undone** | |

Some of step 1's items, as the planner writes them:

- "A request with only `amount` succeeds and the response carries both fields" (check, in a preview).
- "The contract differs from the live one only by additions" (check: `oasdiff`, against the live version).
- "The live versions of orders and billing complete a checkout against this version" (check: the flow tests in
  `system/`, in a preview).
- "After releasing the previous version over this one in staging, charges still succeed" (check, in staging).
  This proves the undo.
- "Would a charge written by the old version during the rollout be missing `amount_minor`, and if so, does step 2
  cover it?" (Reviewer Question).

Step 6 has one item: "the count of old-form calls is zero for seven days, for every caller" (check, in production).
Step 9's items include "a backup from today restores in staging" and "no code in payments reads the old column".

The script checks the plan: every thing to remove later has a removing step, no step needs a later one, and each
operation is on the settings' list. Because the change touches a contract and stored data and has a step that
cannot be undone, the script starts a plan reviewer. It finds one fault: the old column is declared `NOT NULL`, so
once step 8 stops writing it, every new charge would fail. The planner adds "the old column accepts empty values"
to step 1. The owner sees the plan on the status page and says "go".

**Step 1.** The script clones `payments` and starts a builder. The builder opens a pull request. The status is
Being Checked. The script reads the three CI checks named in the settings for that commit, runs the step's own
checks in a preview with live `orders` and live `billing`, and runs the contract comparison. All pass. The step
touches a contract and data, so a reviewer runs the preview, tries a refund of £0.10 three times, and passes it.
The step is Approved. There is no standing permission for `payments`, so the status page shows "Waiting on you:
release step 1 to production? It only adds. It is undone by releasing the previous version, which was tried in
staging." The owner gets a notification, opens the chat, and says yes. The script merges; the pipeline releases to
staging; the script reads the running commit and runs the staging item; the pipeline releases to production; the
script reads the running commit there and runs `Healthy` every minute for 30 minutes. Step 1 is Done. The record
shows each fact and its source.

Had the builder removed `amount` in this step, two checks would have refused it before any reviewer saw it: the
contract comparison, and live `orders` failing checkout in the preview.

**Steps 2, 3 and 4** now have what they need. The script asks the owner about the backfill, which is an operation
in production, then runs it and proves its item with a query. Two builders work on `orders` and `billing` at the
same time, each in its own repository. Their pull requests pass, need no reviewer (no contract of their own, flag
off by default, nothing the scan flags), and merge and release under standing permission. Each step's release then
widens its flag: staff, 10%, everyone, with `Healthy` between stages.

**A release goes wrong.** At 10% on `billing`, the rate of failed renewals rises above its limit. The script turns
the flag off, sees the rate recover, sets step 4 to Undone and tells the owner. A builder gets the measurements and
the logs query from the settings. It finds that yearly plans in euros were converted twice, fixes it, and adds a
test. The new pull request touches a test file, so the scan sends it to a reviewer, who passes it. The release
runs again and completes.

**Step 5** moves reads to the new column. **Step 6** starts. For seven days the status page says "Watching: old-form
calls, zero for 3 of 7 days". On day two the count is not zero: a caller named `finance-export` appears. Nobody
listed it. The step's item fails, the seven days start again, and the status page tells the owner who the caller
is. This is the unknown consumer the owner wasn't sure about. The owner asks for it to be moved; the planner adds
a step in that module's repository, which belongs to another team, so it is `Ours: no`: the script opens the pull
request and waits for them.

**Steps 7 and 8.** With seven clean days, the flags come out and `amount` leaves the API. Step 8's contract
comparison shows a breaking difference, and the script accepts it only because the step is the planned removal and
step 6 is Done. It is still undoable, since the column exists.

**Step 9.** The status page shows: "Waiting on you: drop the old column. This cannot be undone. A backup from this
morning restored in staging. Nothing has read the column for nine days." The owner says yes in the chat. The
pipeline's own approval for `payments` production then asks the owner once more, outside the chat. The operation
runs. The script reads the schema and confirms the column is gone.

**Finished.** Every step is Done and the list of things to remove later is empty. The script starts the end
review: a reviewer uses the shop in production with the test account from the settings and reads the whole change.
The report lists five decisions in the owner's name, what each stage cost, and that the change took 16 days, of
which about 14 were watching.

## 10. Risks and unknowns

### What is untested

All of it. More exactly:

| Part | Rests on | My confidence |
|---|---|---|
| Items fixed before building; script re-runs checks; reviewer uses the product | V1's runs and Thrum, plus measurements (`ASSESSMENT.md:68-70`) | High |
| A structured verdict from a read-only reviewer | The assessment's proposal; not built | Medium |
| `advance` replacing the lead's table | The assessment's inference; not built | Medium |
| The home repository, and builders with no access to it | Reasoning only | Medium. The mechanics of accounts and tokens on a laptop are the weak point |
| Production as a target, read by the script | Reasoning, and Pact's model of recorded deployments | Medium |
| Add, move, watch, remove as planned steps | Standard practice for people; untried with agent planners | Medium |
| Review by risk; plan review only for risky changes | A bet against Thrum's cost | Low to medium |
| One step per module at a time, each waiting for the last to be live | A guess at the right trade | Low. It may be too slow |
| Automatic undo on a failed health check | Standard on platforms that have it; the script's plain version is untested | Low |
| Steps on another team's module | Not thought through beyond "open a pull request and wait" | Low |

### What I am guessing

- **That small steps stay cheap enough.** Ten steps for one field is the honest shape of the work, and each has a
  fixed cost in tokens and waiting. V1 measured that fixed costs push toward bigger pieces. If a step with no
  reviewer still costs too much, the design is too heavy for ordinary changes and should be reserved for breaking
  ones.
- **That a planner can order a compatible change correctly.** The plan review exists because I doubt it. The
  worked example's `NOT NULL` fault is the kind I expect.
- **That `Healthy` can be written well.** A health command that is too loose passes bad releases; one that is too
  tight undoes good ones and trains the owner to ignore it. Nothing in this design helps a project that has no
  useful metrics. Such a project should use `Release` without `Healthy`, and every production release is then the
  owner's call.
- **That health can be pinned on one step.** Other people release too, and traffic changes. The script will
  sometimes undo a step that was innocent.
- **That the timer is acceptable.** An unattended process that starts agents and asks pipelines to release is a
  larger thing to trust than a script the lead runs. The budget lines, the closed list of operations, and "ask
  before going forward" are the limits on it.
- **That the owner will accept one approval outside the chat** for steps that cannot be undone.

### What this design doesn't cover

Secrets management beyond "agents get none for production". Mobile apps and other software whose old versions
stay in users' hands for months, where "nobody uses the old form" may never become true. Incidents that no step
caused. Costs of cloud resources that previews use. Several owners. Each needs its own design.

### What to try first

In order, cheapest first. Each is meant to be able to kill part of the design.

1. **Read-only, on a real system.** Build only the part of `advance` that reads: pull request checks by name, the
   running version, `Healthy`. Point it at any project the owner already runs and see whether the status page it
   writes is true for a week. This costs no agent time and tests the claim everything else rests on.
2. **The home repository on Thrum or a small project.** Move plans out of the builder's reach and make the builder
   output only a branch. See what breaks when the builder can't read its own acceptance file in its checkout
   (it will need a read-only copy).
3. **The reviewer's structured verdict**, on V1, where there are earlier reviews to compare with.
4. **A toy shop: three services, three repositories, and a second running copy standing in for production.** Run
   the worked example end to end, with a planted fault at each guard: a builder told to remove the field early, a
   release that breaks health, a caller nobody listed. Record tokens and waiting time per step and per stage.
5. **Plan review on and off**, on the same change, to see what the skipped review would have caught.
6. Only then a real production system, with every production permission set to "ask".

## Sources

Read for this design, beyond the files the brief names:

- [Parallel Change](https://martinfowler.com/bliki/ParallelChange.html), Danilo Sato, 2014: the three phases, and
  the risk of never finishing.
- [GitLab, multi-version compatibility](https://docs.gitlab.com/development/multi_version_compatibility/): old and
  new versions run together; phases in separate releases; named outages.
- [Stripe, online migrations at scale](https://stripe.com/blog/online-migrations): the four-step data migration.
  Read through a search summary and a third-party summary, not the post itself.
- [Pact, recording deployments and releases](https://docs.pact.io/pact_broker/recording_deployments_and_releases)
  and [can-i-deploy](https://docs.pact.io/pact_broker/can_i_deploy): checking a version against what is running.
- [Confluent, schema evolution](https://docs.confluent.io/platform/current/schema-registry/fundamentals/schema-evolution.html):
  compatibility modes and which side upgrades first. The first 100,000 characters of the page were read.
- [Buf, breaking change detection](https://buf.build/docs/breaking/). `oasdiff` is named from my own knowledge and
  was not looked up.
- [Argo Rollouts, analysis](https://argo-rollouts.readthedocs.io/en/stable/features/analysis/): a failed analysis
  aborts a rollout.
- [DORA, working in small batches](https://dora.dev/capabilities/working-in-small-batches/): small batches and AI.
  The page gives no figures.
- [GitHub, controlling deployments](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/control-deployments):
  required reviewers on an environment. Read through a search summary of older versions of the page.
- [GitHub, artifact attestations](https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations).
  Read through a search summary.
- [GitHub, implementing polyrepo engineering](https://wellarchitected.github.com/library/architecture/recommendations/implementing-polyrepo-engineering/):
  no built-in change across repositories. Read through a search summary.
- On the April 2026 database deletion: [NHI Management Group](https://nhimg.org/articles/ai-coding-agents-need-external-authorization-not-prompt-rules/)
  and [Mondoo](https://mondoo.com/blog/5-lessons-from-9-seconds-ai-agent-deleted-production-database). Vendor and
  community write-ups, read through a search summary; the sources disagree on the date.
