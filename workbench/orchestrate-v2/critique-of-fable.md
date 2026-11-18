# Critique of `draft-fable.md`, by the author of `draft-opus.md`

Opus 5.5, 11 November 2026. I read Fable's draft in full and checked its claims about V1 where they bear weight.
Line numbers are against branch `orchestrate-1.6.4` as checked out today.

The two designs agree on more than I expected: a change replaces the project as what the owner follows, steps that
are each deployable alone replace milestones, one repository holds the plans and the record, `advance` on a timer
replaces the lead's table, the reviewer is read-only, review is triggered by risk, expand/migrate/contract is
planned up front and measured before removal, agents hold no production credentials, and going back never needs
permission while going forward does. So the critique is mostly about mechanisms and about where each design's
claims hold or don't.

## 1. Where Fable's draft is better, and what I would adopt

**Every step says how it is undone, and the undo is proved.** Fable puts one line on every step ("turn the flag
off", "release the previous version", "cannot be undone"), and for a step that touches data or a contract, an item
proves the undo in staging before production (`draft-fable.md:76-77`, `:395-396`, `:664-665`). My draft had the
rule "reducing exposure is always allowed", but never required anyone to show that the way back works. A rollback
nobody has tried is a guess. **Adopt.**

**A list of things to remove later, enforced by the script.** Each temporary thing (a flag, a field kept for old
callers, a dual write) is listed beside the step that removes it, and the script refuses a plan where one has no
removing step (`:79-80`, `:114-117`). My draft made the same point as a rule for the planner. Fable's version is a
check the script runs, which is what the set's principles ask for. **Adopt.**

**Three kinds of step: build, operation and watch.** A watch step ("nobody has called the old endpoint for seven
days") holds nothing, so a week of watching doesn't block other work on the module (`:65-66`, `:281`). Operations
come from a closed list in the settings, so a planner can name `backfill-amounts` but can't write a new command
into a plan (`:445-446`). My draft had five phase kinds (expand, migrate, backfill, contract, drop) and a `run-job`
command with no limit on what it runs. Fable's kinds are fewer and more general. The compatibility phase is
already captured by Fable's rule that a breaking contract diff is accepted only for a planned removal step whose
needs are Done (`:332-334`). **Adopt the three kinds and the closed list. Drop my five phase kinds.**

**The health check must be shown to fail.** The first step in any module's life breaks a staging copy on purpose
to prove `Healthy` notices (`:511-513`). That is the cheapest guard I have seen against a health query that always
passes, which I named as my most dangerous unknown and didn't guard against. **Adopt.**

**After an undo, the module is held.** Nothing else is merged or released on that module until it is healthy, and
an undo that fails stops everything there and raises an urgent notice (`:450-453`). My draft rolled back and moved
on. That leaves the bad commit on main for the next release to redeploy (see section 4). **Adopt.**

**The owner is notified outside the chat, one way only.** One command posts "something is waiting, open the chat"
(`:201-203`). My draft woke the lead and assumed the owner was watching that chat. For decisions that wait days,
this is what makes "the owner only chats" workable. **Adopt.**

**A review of the whole change at the end, in production.** This is the one pass that Anthropic kept
(`:526-529`). My draft reviewed steps and had no end-of-change review. **Adopt.**

**Events.** For events, Fable says which side upgrades first, and adds an item that replays old messages through
the new reader (`:343-348`). Mine only named the registry mode. **Adopt.**

**Keep the word "module", and use named statuses.** V1's owner already knows "module", and Fable keeps its
definition (`GLOSSARY.md:72-74`) and adds three facts to it. My "component" renames something the owner had just
learned. Fable's status list (Being Checked, Approved, Being Released, Undone, Needs the Owner; `:121-132`) reads
better on the owner's page than my "last gate passed, next gate, who it waits on". **Concede both.** The gate list
can stay underneath as the script's model.

**The first trial is read-only.** Fable starts by building only the reading half of `advance` and pointing it at a
project the owner already runs, to see whether the status page stays true for a week (`:773-775`). That costs no
agent time and tests the assumption everything else rests on. My first trial was a toy three-repository system.
Fable's is cheaper and comes first. **Adopt.**

**It says what it doesn't cover.** Mobile apps and other clients whose old versions stay in users' hands for
months, incidents that no step caused, the cost of previews, and several owners (`:765-767`). My draft missed
long-lived clients entirely.

## 2. Where it is wrong, weaker or unsafe

### 2.1 Builders can't reach the home repository: true on a host that enforces it, false on the owner's laptop

Fable claims a property V1 lacks: the done-when file is "in a repository the builder has no checkout of and no
permission to push to", with the main branch accepting pushes from the script's account only (`:250-255`). V1's own
README says every session the script starts "runs inside the lead's process, with the lead's sandbox and
operating-system permissions" (`README.md:443-444`).

**Failure scenario.** The script runs on the owner's Mac. `gh` is signed in as the script's bot account, because
the script has to push the record. A builder session runs as the same OS user. It runs
`gh api -X PUT repos/acme/home/contents/changes/…/DONE.json`, or clones the home repository and pushes with the
same credential helper. Branch protection lets the push through, because it comes from the script's account.

So the property holds only if the script's credentials are unreachable from agent sessions: a separate OS user, a
container, or the script running in CI. Fable does rate "the mechanics of accounts and tokens on a laptop" as its
weak point (`:736`), but its sections 3 and 6 present the property as a fact. My draft makes the same mistake with
"agents never hold production credentials". Both claims need to say where the agents run.

### 2.2 The second approval outside the chat can be pressed by an agent

Fable makes a pipeline approval by the owner, outside the chat, the lock on steps that can't be undone (`:438-443`),
and says a lead that invented a yes "still could not drop a table".

**Failure scenario.** On a small team the owner's own `gh` login is on the machine, often because the owner set
the project up from it. GitHub lets a required reviewer approve a pending deployment through the API (the
`pending_deployments` endpoint). An agent with that token approves the deployment as the owner. The lock is real
only when:

- the owner's credentials are absent from every machine that runs agents;
- the deploy is triggered by a different account, with "prevent self-review" set.

The design should state both conditions. Without them, the second approval adds ceremony and no protection.

### 2.3 A money-path consumer step gets no reviewer, and the fault is first found by real users

In the worked example, orders and billing's steps "need no reviewer (no contract of their own, flag off by
default, nothing the scan flags)" (`:694-696`). Billing then converts yearly euro plans twice, and the fault is
first seen at 10% of production traffic, as failed renewals (`:698-702`).

The review rule (`:521-525`) triggers on contracts a step owns or changes, not on contracts it consumes. A consumer
that changes how it reads money is exactly the risky step. Two things would have caught this earlier:

- **Risk set per module, not by contract ownership.** My draft marks payments as high-risk; billing handles money
  too, so the owner would mark it high as well.
- **A shadow comparison before any exposure.** The step computes both the old and new amount and counts
  disagreements while the flag is still at 0%. My draft has this as an item (O1.4). It catches a double conversion
  before any user sees it.

Fable's `Healthy` is a module-level pass/fail command (`:380`). It has no room for that kind of step-specific
signal before exposure.

### 2.4 One step per module until it is live and watched: idle time, and less independence than claimed

"A step holds its module from the moment a builder starts until it is Done or Undone" (`:278-281`). Done includes
production plus the observation period. Payments has no standing permission in Fable's example.

**Failure scenario.** Step 1 is Approved at 23:00. The owner answers at 09:00. Production plus a 30-minute window
takes until 10:00. For eleven hours nothing can be built on payments. Worse, a second change that also touches
payments, unrelated to this one, waits behind it too. The "one suspect" argument (`:279-280`) is about releases,
not about building or reviewing.

I'd keep one step per module **in release** at a time, and let the next step be built and reviewed meanwhile, then
re-checked once the earlier one is live. Fable lists the rule as "Low. It may be too slow" (`:740`), so we agree
it is a guess. I think the guess is wrong for the building half.

### 2.5 A step proved in staging after it has merged

Some of step 1's items are proved "in staging" (`:664-665`), and staging comes after merge. Fable's own `Release`
line allows `on merge`, where the pipeline releases by itself (`:378`).

**Failure scenario.** The pipeline promotes staging to production in ten minutes. The script's staging item (the
undo test) runs while production is already deploying. If it fails, the step is already merged and live.

The design needs one of three rules:

- with `on merge`, staging items are a merge gate run in a preview, not in staging;
- the pipeline must pause between staging and production for the script;
- `on merge` modules can't have staging items.

My draft has the same weakness at its gate 5. Fable's undo item makes it bite harder, because it is the item that
justifies going to production at all.

### 2.6 Small projects keep V1's merge-then-verify, without saying it is a choice

For `Merge: direct`, steps are "Done at merge, after the script re-runs the checks in a clean copy, exactly as V1"
(`:558`). That is V1's order: the builder's commit must already be on main (`agent_loop.py:2803`), and checks then
run on main's tip (`agent_loop.py:2814-2817`). I now think this is right for a project where nothing deploys from
main (section 3). But the draft should say so and give the reason, because on the pull-request path it verifies
first. A reader will otherwise assume one model.

### 2.7 Smaller points

- "Production access is read-only" (`:431`) contradicts "the script undoes a release" (`:190`, `:450`). Turning a
  flag off or triggering a redeploy is a write. Name the narrow write scopes the script holds.
- Dropping `LOG.md` and `DESIGN.md` (`:609-611`) removes the builder's channel for proposing an interface change.
  In V1 the builder writes the proposal in the log (`build-milestone/SKILL.md:133-134`). In V2 the builder can't
  write to the home repository at all, so a builder that finds the plan wrong can only end `BLOCKED`. That is
  probably acceptable, but it should be stated.
- `done-when.md:258-272` is cited as "V1's rule" for Done (`:101`). Those lines describe the record file; the Done
  rule follows a few lines later. The other V1 citations I checked hold:
  - `done-when.md:228-230` (when a reviewer is needed)
  - `agent_loop.py:2769-2783` (`check_failures`) and `:2602-2620` (`land`)
  - `README.md:383-387`, `:455-457`, `:481-485`
  - `deadlock-review-fable.md:135-141`
  - the Thrum counts: 18 design reviews, 6 of them asking for changes; 9 plan authorisations; 6 milestone reviews,
    1 failed. I got the same numbers from its log.

## 3. Where we disagree on a real decision, and where I now stand

| Decision | Fable | My draft | Where I now stand |
|---|---|---|---|
| Merge order | Verify before merging on the pull-request path; V1's merge-then-verify for `Merge: direct` | Verify before merging everywhere | **Changed to Fable's split, with the rule stated.** Verify first wherever merging to main can release. Where nothing deploys from main, merge-then-verify lets the next step build on the last without stacked branches, which I admitted agents handle badly. V1's failed reviews on main were fixed forward without harm on Thrum. |
| Step throughput | One step per module from build start until Done (live and watched) | One open step per component unless the plan marks two as independent; `needs` may name any gate | **Hold, refined.** One step per module in release at a time; building and review of the next may overlap (2.4). |
| Meaning of `needs` | One meaning: the needed step is Done, which for a released module means live | `needs` names a step and a gate (`@production`, `@published`) | **Mostly concede.** The default should be Fable's single meaning, because it is one thing for the owner to learn. Keep a gate suffix only for a library's `published` and for staging-only integration, and add it only when a trial shows a need. |
| Plan review | Only when the change crosses modules, touches a contract or data, or has a step that can't be undone; fixed questions; one end-of-change review | Only when the change touches a contract, a high-risk component or the system map | **Agree.** Take Fable's fixed questions and its end-of-change review. Its `NOT NULL` example (`:674-676`) is the right kind of fault for a plan review to find. |
| Credentials | Agents have none; the script is read-only in production; releases go through the pipeline | Agents have none; the script holds deploy and flag tokens | **Between the two.** The script holds narrow write scopes: flag off and down, trigger a pipeline, run a listed operation. Increases in exposure go through the pipeline's own approval. Both designs must add that agent sessions run where they can't read the script's tokens (2.1), which in practice means the script runs in CI or under a separate OS user. |
| Second approval outside the chat | On by default for steps that can't be undone | Optional per environment | **Changed to Fable's default, for data destruction only**, with the two conditions from 2.2 made explicit. Without those conditions, say plainly that it protects nothing. |
| Record protection | Branch protection where the code host can enforce it; every fact names its source | Every entry carries a receipt that `audit` fetches again | **Both.** Branch protection prevents writes; receipts catch a forged entry after the fact, including one made with the script's own account (2.1). Fable's "the owner said it" source belongs in the receipt list. |
| Step kinds | build, operation, watch | expand, migrate, backfill, contract, drop | **Concede** (section 1). |
| Shadow comparison and step-level production signals | Not present; module-level `Healthy` | A production-signal proof kind, with shadow comparison before exposure | **Hold.** It caught, in my example, the class of fault that reached users in Fable's. |

## 4. What both designs miss

**Changes in flight that conflict with each other.** Both designs check a step against what is **live**. Two
changes can each be compatible with live and incompatible with each other.

- Change A expands `charges` with `amount_minor`.
- Change B, planned the same week, is a contract step that removes an old field. A's migrate step in orders still
  reads that field on a code path B's planner didn't see.
- Both pass the comparison against live.
- B's removal is gated by the old-use counter, but if A's code reading the field is merged and not yet exposed, the
  counter reads zero.

The compatibility gate needs to consider other open changes' merged-but-unreleased steps, or plans must be
serialised per contract.

**The bad commit stays on main after a rollback.** Rolling back production or turning a flag off doesn't remove
the commit from main.

- Fable holds the module, so nothing else releases there. But a person on that team merges a fix to something else
  and their pipeline releases main, bad commit included. Human merges are outside the hold.
- My draft has no hold at all.

Either the script opens a revert pull request when it rolls back an unflagged step, or a `release-blocked` marker
must reach the module's pipeline, not just the script.

**Health when production is already unwell.** Both compare against a recent baseline. If an unrelated incident
started an hour before, the baseline is bad and the step may pass, or a healthy step is undone during someone
else's outage. Neither design reads an error-budget or incident state before increasing exposure. "Don't widen
during an open incident or with the budget spent" is a single rule and established SRE practice.

**Approvals bound to what was approved.** The owner says yes to releasing step 1. A review cycle then changes the
pull request. Neither design says that a permission binds to a commit, and a yes given for one diff must lapse if
the diff changes.

**Production data reaching the model.** Reviewers read production dashboards and logs (mine), and builders get
"the logs query" after an undo (Fable, `:700`). Logs carry customer data, and sending them to a hosted model may
breach the system's own privacy duties. Neither design says what an agent may read from production, or that
evidence must be scrubbed before it is committed to the home repository.

**The script itself as the riskiest code.** Both designs move more authority into `advance` than V1's script ever
had, and both propose trials of the agents. Neither proposes testing the gate engine directly with injected faults
(a check-run API that times out, a deploy record that lags, a metrics backend returning empty), where an empty
answer read as zero errors would widen a broken release.

**An owner who is away.** Questions pile up on the status page, and steps holding modules (Fable) or waiting for
approval (both) sit indefinitely. Neither design says what a question does after a day or a week without an
answer: expire, re-ask, or be held by default.

**Moving a V1 project across.** Thrum is mid-build on V1. My draft gave a migration sentence; Fable gives none.
Neither says what happens to open milestones, their counts and their recorded reviews.
