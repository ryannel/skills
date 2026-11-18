# Critique of `draft-opus.md`, by the author of `draft-fable.md`

Claude Fable 5.2, 11 November 2026. I read the Opus draft in full and checked the V1 claims that its argument rests
on against `agent_loop.py` and the skills in the working tree of `orchestrate-1.6.4`. Nothing was changed except
this file.

The two drafts agree on most of the shape: a change made of steps, one repository for plans and the record, a
script on a timer in place of the lead's table, a read-only reviewer, review by risk, add / move / remove for
breaking changes, the running version read from the deploy system, a counter of old-form use, and automatic undo.
That agreement is weak evidence, since both of us read the same brief and the same three microservice designs.

## 1. Where the Opus draft is better, and what I would adopt

**`needs` names a step and a gate** (`"payments/expand-amount-minor@production"`, lines 233-235). This is better
than mine. I had one meaning of "needs" (the other step is Done) and rejected a second meaning as too much to
explain. Naming the gate in the need gives every case with one syntax: `O2` needs `O1@observed`, `P3` needs
`O2@production`, a library's users need `lib@published`. I would adopt it as written.

**Verify before merging, argued from V1's code.** Opus shows that V1 merges first and verifies after, and it is
right: `claim_problems` refuses a claim until the builder's `HEAD` is already on the main branch
(`agent_loop.py:2803`) and only then runs the checks in a clean copy of the tip (`:2814-2817`). My draft does the
same thing for pull requests but never says that this reverses V1, and for a repository with no CI I kept V1's
`land` unchanged. Opus's version for that case (verify the rebased branch in a clean copy, then fast-forward) is
the better default. See section 3 for the one place I still differ.

**"Increasing exposure needs permission; reducing it never does"** (line 428). One sentence does the work of my
eight-row table, and "exposure" is a better name for what the owner is deciding than my per-action list.

**Receipts.** Storing the identifier of the CI run, deployment or flag change beside each record entry is stronger
than my "source" label, which says what kind of system a fact came from but not which run. I would keep my four
plain source names for the status page and add the identifier to the record. Section 2 says where `audit` is
oversold.

**The gate table with a decider for each gate** (lines 389-398). It makes "who or what decides" visible in one
place. My verification table says the same things less clearly.

**People on other teams as a gate.** Opus's worked example has a code owner from the Payments team approving in
GitHub and the status page showing the wait. My draft gave other teams three sentences and admitted it.

**A way for a V1 project to move to V2** (line 634). My draft has none. Thrum would need one.

**Smaller things:** a risk level per component; a `published` gate for libraries; the shadow comparison in `O1`;
the warning that a 5% ramp on a quiet service measures nothing; the sample message to the owner; the trial that
drives the three new pieces by hand before any agent is involved; naming which failure would hurt most.

## 2. Where it is wrong, weaker or unsafe

### 2.1 The script holds production credentials on the same machine, as the same user, as the builders

Opus: "Deploy, flag and job commands run with credentials the script holds", and builders "are started with an
environment that excludes them, as V1 already strips Claude's API keys (`README.md:497-500`)."

The V1 claim is narrower than it reads. `clean_env` removes only variables starting `ANTHROPIC_` or `CLAUDE`, and
only for Claude sessions (`agent_loop.py:3266-3271`). A Codex session gets the lead's whole environment
(`agent_loop.py:3346`). And V1 says every session "runs inside the lead's process, with the lead's sandbox and
operating-system permissions" (`README.md:443-445`).

*Scenario.* The owner's laptop has `~/.kube/config` with a production context, `gh` signed in, and a flag
vendor's token in a dotfile, because `advance` needs them. A builder on step `O1` is told to make the flow test
pass. It runs `kubectl` or the flag command line directly, which work, because it is the same user with the same
home folder. Filtering environment variables doesn't touch files on disk. This is the April 2026 database
deletion again: a staging task with production in reach.

My draft says the script has read-only access and the pipeline holds the write credentials. That is the right
rule, but my draft is inconsistent about it: my script also "turns the flag off" and "runs an operation", which
need write access. The fix for both drafts is the same: every write to staging or production is a trigger of a
pipeline job, made with a token that can only trigger named jobs, and the pipeline holds the real credentials.
Opus mentions this as an alternative ("or that CI holds"); it should be the only way.

### 2.2 The builder writes to the step file, which lives in the control repository

The state table (line 121) says the step is written by "Planner (what is asked), builder (status and evidence),
reviewer (verdicts)". But the reviewer is declared read-only (line 140), and the step file is in the control
repository beside `record.json`.

*Scenario.* For a builder in `acme/orders` to write status and evidence, it needs a checkout of, and push access
to, `acme/delivery`. It now can edit `steps.json` items, `SYSTEM.md` health bounds and standing permissions, and
`record.json`. V2 is back to V1's "check that the builder changed only its own fields"
(`agent_loop.py:1182`), now across two repositories, and the claim "every gate's decider is something no agent in
the set can write to" no longer holds for the item text or the health queries. Drop the builder's fields: a pull
request is the builder's whole output.

### 2.3 "Redeploy the previous commit" is always allowed, with nothing proving it is safe

Opus lets the script roll back by itself on any failed health query (lines 432-434), and no step carries a
statement of how it is undone or an item that tries the undo.

*Scenario.* `O1` is at 25%. Orders placed through the new path are saved in the orders database with only
`amount_minor` set, because the builder saw no reason to keep filling the old column for new rows. A health query
fails and the script turns the flag off. The old path now reads those orders, finds no `amount`, and fails every
refund and receipt for them. Turning exposure down made things worse, with nobody asked, because data written
under the new behaviour was never shown to be readable by the old. The same applies to "redeploy the previous
commit" after any step whose deploy ran a schema change the previous code doesn't fit. My draft
requires each step to say how it is undone and, for steps touching data or a contract, to try that undo in
staging first. I would keep that.

### 2.4 The step kind is declared by the planner, and the kind decides which gates run

`contract` steps get the two extra gates (every known consumer moved; the counter at zero) and the owner's
confirmation. A `build` step doesn't.

*Scenario.* A planner writes "tidy the charges handler" as kind `build`, and the builder's tidy-up removes
`amount` from the response. Gate 2 asks Pact's `can-i-deploy`. Both listed consumers have migrated, so Pact
passes: no recorded consumer expects `amount`. The step merges and deploys dark. The unlisted nightly job in the
worked example breaks that night. The counter gate that exists to catch exactly this never ran, because the kind
said `build`. The kind has to be worked out from the diff of the contract file by a tool, not declared. My draft
uses a contract diff for this, but it has the same hole for a project whose only check is Pact, so this is a fix
for both.

### 2.5 `audit` promises more than a receipt can give

"A forged entry would have to come with a forged CI run" is true. "`audit` re-fetches every receipt" will often
fail for honest entries.

*Scenario.* Six weeks after `P1`, `audit` runs before `P4`. GitHub has expired the run logs, the metrics system
keeps 15 days of data so the health query for `P1`'s window returns nothing, and the flag vendor's audit log is
on a plan that keeps 30 days. `audit` reports most of the change's record as not holding up, and `advance` is
written to audit "the entries it relies on before it acts on them", so `P4` stops. Also, a check-run identifier
proves a run with that name passed, not what it ran. The record should store the result that was read, and treat
the identifier as a pointer that may go stale.

### 2.6 Two changes on one component

`advance` "holds one lock per change", and the limit is "at most one open step per component unless the plan
says two are independent". A plan belongs to one change.

*Scenario.* Change 21's `P1` is in its 30-minute dark window on payments. Change 22's step on payments, planned
separately, passes its gates and deploys. Health drops. Which step is rolled back? Redeploying "the previous
commit" removes change 22's step and leaves the faulty one, or the reverse. The hold has to be on the component
across all changes, from merge until the window closes.

### 2.7 A health gate that is polled by a laptop

The standing permissions example grants "Ramp a flag to 25%, production, yes, while health holds", and `advance`
runs as a scheduled task on the owner's machine.

*Scenario.* The flag goes to 25% at 18:00 and the owner closes the laptop. Nothing evaluates the health query
until morning. "The script turns the flag off by itself" is true only while the script is running. My draft has
the same fault. Exposure should rise without the owner present only where something that is always on (the
rollout tool's own analysis, or a timer in CI) can lower it.

### 2.8 Smaller errors

- `done-when.md:182-184` is cited for "the builder can't change items"; those lines are the end of the JSON
  example. `done-when.md:76-80` is cited for the status page; those lines are the module table. The claims are
  true of V1; the line numbers are wrong.
- Thrum's "(no row in the module table)" is used twice as evidence that two files drift. It may only show that
  Thrum hasn't written the table since moving to the new layout. It doesn't carry the weight put on it.
- The `signal` field uses `baseline(charge_success_ratio, 7d) - 0.005`. That is a small language the script would
  have to implement, which contradicts "the script never talks to Prometheus".
- A timer in the control repository's CI has to start builder agents there. That needs an agent sign-in in CI,
  which on Claude means an API key and metered billing, not the owner's plan.
- When a rollback happens at night, `advance` "wakes the lead". Nobody is in that chat. There is no way to reach
  the owner outside it.

## 3. Where the designs disagree, and which side I now hold

**Verify before merge, or V1's merge then verify.** Opus's side, with one exception. Checks before the merge,
always: it costs nothing extra and I concede my `Merge: direct` mode was wrong to keep `land` as it is. A
reviewer before the merge wherever a merge can reach users or other people share the branch. For a solo
repository with nothing released from main, I would let the reviewer judge after the merge, as V1 does, because
Opus's own answer to the waiting cost is stacked branches, and Opus says it has not seen agents handle them.

**Gates as a concept, or production as one more target for items.** I hold mine, and take one thing from Opus.
Opus has two mechanisms: items (with a fourth kind of proof and an `at` field) and a separate fixed path of
gates whose passes are decided outside the items, with step kinds choosing which gates apply. That is where
2.4 comes from. With production as a target, "running for everyone" and "healthy for the window" are items the
script adds, and there is one rule for Done. What I take is the names: an ordered list of places per module is
needed anyway for `needs` to point at and for the status line, and Opus's gate table is the clearest way to show
who decides each. So: one mechanism, shown as a path.

**The seven-day counter.** We agree on having it. I now hold Opus's fuller version: the counter, plus a check
that every listed consumer's running version is past its migrate step, plus the owner confirming removal. I
would add that the window is set from the longest known cycle of the callers (a month where there is monthly
billing), not a default of seven days, and that the plan must say the counter cannot see callers that don't
call: readers of a table, and old messages in a queue.

**`SYSTEM.md` replacing `ORCHESTRATE.md`.** I hold mine: two files. Opus puts the components, contracts,
commands, health bounds and the standing permissions in one file that the planner drafts and "only the owner
changes". *Scenario:* a planner adds a consumer to a contract and, in the same diff, the permissions table gains
a row or a health bound loosens; the owner approves "add finance-export as a consumer". What the owner alone
controls should be in a short file that planners never draft. Also, every V1 skill and the script find a project
by `ORCHESTRATE.md`; renaming it buys nothing.

**Credentials.** I hold mine, corrected as in 2.1: the script reads, the pipeline writes, and the script's only
write is to trigger a named pipeline job.

**The owner approving outside the chat.** Opus makes it optional per environment. I made it required for steps
that cannot be undone. I hold mine, narrowed to exactly Opus's `drop` kind: it is the one case where a lead that
invented a "yes" does damage nothing can repair.

**Who writes the step file.** Mine: nobody but the planner and the script (2.2).

**Escalation after failed reviews.** Opus keeps V1's counts as they are; I collapsed them. I move to Opus's
side. They were debugged on a real deadlock two days ago, and I had no evidence for changing them.

**The lock.** Mine: per module across changes (2.6).

## 4. What both designs miss

1. **A baseline.** Neither says how to tell whether any of this beats one strong agent working through the
   team's existing pull requests, CI and pipeline with a done-when file. The research's main finding is that such
   a baseline often wins. The first trial should include it.
2. **Abandoning a change halfway.** If the owner cancels after the expand step, the new field, the dual writes and
   the flags are live. Neither design has a path that plans their removal; both would leave the change open for
   ever.
3. **Untrusted text reaching agents.** A builder fixing an undone step is handed production logs. Pull request
   comments from other teams reach builders too. Either can carry instructions. Neither design treats them as
   data.
4. **Personal data.** Opus's reviewer reads production dashboards and mine uses production with a test account.
   Logs and query results with customer data would enter a model's context and the evidence folder in git.
5. **Wrong data that has already been written.** Turning a flag off stops new damage. Rows written wrongly at
   25% stay wrong. Neither design has a repair step or asks for one in the plan.
6. **Flaky CI and unrelated health failures.** A required check that fails one run in ten, or a health dip from
   someone else's release, counts as a failed round in both designs and can push a sound step up the escalation
   stages. Neither has a retry rule or a way for the owner to say "that wasn't us".
7. **Infrastructure, configuration and secrets as changes.** A new queue, an environment variable, a rotated key:
   these break production as often as code, and neither design says whether they are steps.
8. **More than one owner.** Both assume one person decides everything. A system owned by several teams has an
   on-call person, release freezes and approvers per service.
9. **Unattended spending.** A timer that starts builders with nobody watching needs a cap per day as well as per
   step. Opus doesn't mention one; mine names a budget line and doesn't design it.
10. **Clients that are never all upgraded.** Mobile apps and partners' integrations. Both designs' removal step
    assumes old-form use reaches zero.
