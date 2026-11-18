# One idea for the four microservice frictions

Status: design only. Nothing under `skills/` has been changed. Line numbers are against branch `orchestrate-1.6.4`
at `fea7c17`.

## The question

A microservice system kept in one repository, one module per service, fits the orchestrate set except at four
points:

1. One `Check` command runs under one merge lock, so a full system check (start the services, run the end-to-end
   tests) is slow and makes every builder's merge wait.
2. Starting a worktree is prose in `ORCHESTRATE.md`, so parallel builders standing up whole stacks collide on
   ports, containers and volumes.
3. Done means merged, not deployed. Services are released separately, so an interface or schema change needs
   expand, migrate and contract steps and a compatibility check, and nothing prompts either.
4. Behaviour that spans services, such as an order going from cart to receipt, has no module, so nobody writes its
   items.

The brief: find the single smallest idea that resolves most of the four together, judged by how many it resolves,
what it costs a project that isn't microservices, how many new words and settings it adds, and whether it keeps the
core guarantee (nothing depends on an agent saying it is finished; the main branch never receives untested work).

## The answer in one sentence

How the services run together is a kind of state too, so, by the set's own rule, it gets exactly one module in
charge of it.

The rule already exists. `plan-module/SKILL.md:104-105` says: "Draw the lines between modules around state, so that
each kind of state has exactly one module in charge of it." In a microservice system there is a piece of state that
no service owns: the running system itself. That is how the services are started together, which versions of each
run against each other, the contracts between them, and the flows that cross them. Every one of the four frictions
is a symptom of that state having no owner. Give it a module, and each friction becomes ordinary work for that
module, expressed with fields the set already has.

No new setting, no new field, no new status, no script change, and no new glossary entry. The module is a module
like any other. In the example below it is called `SYSTEM`, but the planner names it.

## Why it works, point by point

### 4. Flows that cross services

This is the direct case. The flow "an order goes from cart to receipt" becomes a milestone of the system module.
Its items are the flow's observable results, proved by a `check` that runs the end-to-end test, and its `needs`
lists the service milestones it exercises (`"ORDERS:M2"`, `"PAYMENTS:M1"`). The script already refuses to start a
milestone until everything in its `needs` is Done (`plan-module/SKILL.md:113-117`; `needs_of` at
`agent_loop.py:1108`). The module's builder writes the end-to-end tests, which is real code with a real owner.

The current item rule, "depends only on this module and on what exists when its milestone ends"
(`done-when.md:344-345`), still holds: with `needs` set, the services exist when the flow milestone starts.

### 2. Parallel stacks colliding

The system module owns the command that starts the whole system (a compose file and a small wrapper, say
`./stack up`). Making that command safe to run in several worktrees at once becomes one of its milestones, with an
Automated Check, instead of a sentence of prose nobody verifies. The usual mechanism, which the design names and the
builder implements:

- every container, network and volume is named from the checkout's path (Docker Compose's project name), so two
  worktrees never share one;
- no host port is fixed: each service publishes on port 0 and `./stack url orders` prints where it landed;
- seed data loads into the stack's own volumes.

This covers the script's own clean checkouts as well. The claim checks run in a per-module checkout at
`<git common dir>/orchestrate/verify/<MODULE>` (`verify_tree`, `agent_loop.py:2550-2563`), so two modules' checks
running at once get two stacks. If the machine can hold only one stack at a time, the flow items say
`"lock": "stack"`, an existing field that makes the script take that lock around the check
(`agent_loop.py:2762-2766`), and `stack` goes on the `Exclusive resources` line.

`ORCHESTRATE.md`'s "Starting from a clean clone" section (`profile.md:48-50`), which already asks "how two worktrees
avoid sharing a port or a database", then names the system module's command instead of describing it.

### 1. A slow check serialising merges

Today there are two places a check runs, and only one of them is under the merge lock:

- `land` runs the `Check:` line inside `held("integrate", ...)` (`agent_loop.py:2590-2609`), on every merge.
- The claim verification runs the `Check:` line and the milestone's item checks in the module's own clean checkout
  of the main branch, outside the merge lock (`check_failures`, `agent_loop.py:2757-2771`, called at
  `agent_loop.py:2805`), once per milestone.

With a system module, the slow suite has an owner and a natural home in the second place: each flow is an item
check of the system module, run when that flow's milestone is claimed. The `Check:` line keeps what must hold for
every merge and is fast: each service's own tests, plus the contract tests the system module owns (below), which
check every pair of services against each other without starting anything. The lock still serialises merges, but
what it holds is now a fast command, which is the trade the README already makes deliberately for two or three
builders (`README.md:260-266`).

This keeps the guarantee as it is today. The main branch still receives only work that passed the `Check:` line.
Item checks already run after the merge, on the merged tip (`claim_problems`, `agent_loop.py:2774-2811`), and a
milestone is Done only when they pass and the script records it. Nothing here moves a decision to an agent.

What it gives up, stated plainly: a later merge to a service can break a flow that is already Done, and nothing
re-runs that flow's check on every merge, because the claim verification runs only the claimed milestone's items
(`agent_loop.py:2760`). Two things narrow this. The contract tests in the `Check:` line catch any break in what one
service sends another, which is most cross-service regressions. And the system module's last milestone is always
reviewed (`needs_review`, `agent_loop.py:1101-1105`) and can carry an item that runs every flow. A project that wants
every flow on every merge can still put a short smoke run of them in its `Check:` line; that is its choice of speed
against coverage, made in the one line it already has.

### 3. Version skew between separately released services

Two parts.

The compatibility check. The system module owns the contracts between services (from the interfaces in
`ARCHITECTURE.md`) and a record of what is released, such as `deploy/released.json` mapping each service to the
commit running in production. The contract test then runs both ways: each service at this commit against every
other service at its released commit. It is fast, so it belongs in the `Check:` line. A provider that drops a field
a released consumer still reads fails the merge, before it reaches the main branch. That is version skew caught by
the existing gate, mechanically, with no agent's word involved.

The prompt to change in steps. Interfaces between modules already change only through a planner
(`plan-module/SKILL.md:108-109`). One added paragraph there tells the planner that an interface between services
released separately changes in steps, each its own milestone ordered by `needs`: the provider accepts and returns
both forms; each consumer moves to the new form; the provider drops the old form. The compatibility check makes the
last step impossible to merge early. And because the record of what is released is updated only when the owner
deploys (deploying is on the `Owner decides` line, `profile.md:62`), the last step's milestone carries an
`attended` item, the existing field for something only a person can do (`done-when.md:196-198`): "deploy ORDERS at
M5 or later and record it in `deploy/released.json`".

So "Done means merged, not deployed" stays true, and becomes safe: the one step that depends on deployment waits
on the owner through the mechanism that already exists for owner actions, and appears on `STATUS.md` with the other
things waiting on the owner (`done-when.md:65-66`).

What it doesn't do: the script never deploys, and doesn't know what is deployed except through the file the owner
updates. Database migrations inside one service follow the same steps but are that service's own work; the
paragraph names them so the planner splits them the same way.

## Scorecard

| Point | Resolved? | By |
|---|---|---|
| 4. Cross-service flows | Fully | Flow milestones in the system module, with `needs` |
| 2. Stacks colliding | Fully | The module owns the start command and proves it runs in parallel; `lock` as a fallback |
| 3. Version skew | Mostly | Contract tests against released versions in `Check:`; planner paragraph on steps; `attended` for the deploy |
| 1. Slow check | Mostly | Slow suite moves to item checks off the merge lock; `Check:` stays fast. Done flows can regress until the next flow claim, narrowed by contract tests |

Cost to a project that isn't microservices: nothing. It reads one conditional paragraph it skips ("when the parts
run as separate programs"). New words: none. New settings: none. Script and test changes: none.

## The exact changes

All are prose. Each follows the authoring spec (`.agents/skills/orchestration-skill/SKILL.md`): plain sentences,
the reason with the rule, the set's names.

### `plan-module/SKILL.md`, after line 106 (the state rule)

> When the parts run as separate programs that call each other, such as services each with its own process and
> database, how they run together is state too, and needs a module in charge of it. That module owns the command
> that starts every part on one machine, the contracts between the parts, the record of which version of each is
> released, and the flows that cross more than one part, such as an order going from cart to receipt. Without it,
> nobody writes a cross-part flow's items, and every builder invents its own way to start the system.
>
> Its first milestone is the start command, proved to run in two worktrees at once without sharing a port, a
> container or a volume, because builders run in parallel and so do the script's checks. Each later milestone is a
> flow, whose `needs` names the milestones in the other modules that the flow uses. Put the slow suite, the one
> that starts everything, in those milestones' checks, which run once per milestone outside the merge lock, and keep
> the `Check:` line to each part's own tests and the contract tests, which run on every merge under the lock.

### `plan-module/SKILL.md`, after line 109 (interface changes)

> When the parts are released separately, a released copy of one part keeps calling another for a while after the
> new code is merged. So an interface between them changes in steps, each its own milestone ordered by `needs`:
> the providing part accepts and returns both the old and the new form; each part that uses it moves to the new
> form; then the providing part drops the old form. A change to a database's shape goes the same way inside its
> part. The last step can't be Done until the parts that used the old form are released, which only the owner
> does, so give it an `attended` item naming the release.

### `plan-module/references/profile.md`, the "Starting from a clean clone" placeholder (lines 48-50)

Add to the placeholder: "If a module owns the command that starts the whole system, name that command here rather
than describing the steps."

### `plan-module/references/profile.md`, "Lines that need care" (after line 74)

> `Check` runs under the merge lock on every merge, so each builder waits for the others' runs of it. Keep it to
> what must hold for every merge. A slow suite, such as end-to-end tests that start every service, goes in item
> checks, which the script runs once per milestone in its own checkout, outside the lock.

### `plan-module/references/done-when.md`, "What makes a good item" (after line 348)

> An item can depend on several modules when its milestone lists them in `needs`, as a flow across services does.
> It still depends only on what exists when its milestone ends, because those milestones are Done before it starts.

### `README.md`, "One builder works on each module" (line 266, after "two or three builders.")

> A project with a slow suite, such as one that starts several services, keeps that suite in item checks, which run
> outside the lock, and keeps the test command fast.

### Not changed

`agent_loop.py`, `build-milestone`, `review-milestone`, `GLOSSARY.md`, the done-when format, and the tests. A
builder in a service module already reads the clean-clone section and the `Exclusive resources` line
(`build-milestone/SKILL.md:126-127`).

One caution from the authoring spec: "Add a line only for a failure that has been seen". No microservice project
has run on the set yet. The paragraphs above are written from the assessment, not from a seen failure, so either
trial them on a small three-service project first or mark them in the domain README as untested guidance.

## Worked example: three services

The owner wants a shop: `ORDERS` takes orders, `PAYMENTS` charges cards, `NOTIFY` sends receipts. Each has its own
process and database.

Module table in `ARCHITECTURE.md`:

```markdown
| # | Module | What it's for | Needs |
|---|---|---|---|
| 1 | SYSTEM | All three services start together on one machine, and a customer's order goes from cart to receipt | |
| 2 | ORDERS | A customer places an order and sees its status | SYSTEM |
| 3 | PAYMENTS | An order is charged once, and refunded on cancel | SYSTEM |
| 4 | NOTIFY | A customer gets a receipt and status emails | SYSTEM |
```

`ORCHESTRATE.md`:

```markdown
- **Check:** make test && ./stack contracts --against released
...
## Starting from a clean clone
`./stack up` starts every service with seed data, named from this checkout's path, on free ports;
`./stack url <service>` prints where each one is. `./stack down` removes it. Owned by SYSTEM.
```

The milestones:

- `SYSTEM:M1` "All three services start on one machine, and two copies run side by side." Items: `./stack up`
  twice from two checkouts leaves both healthy (check); the contract harness passes on stub services (check).
- `ORDERS:M1`, `PAYMENTS:M1`, `NOTIFY:M1` each need `SYSTEM:M1` and build their service. Three builders run at
  once, each with its own stack. Their merges wait only for `make test` and the contract tests, a minute or two.
- `SYSTEM:M2` "A customer's order goes from cart to receipt." Needs `ORDERS:M2`, `PAYMENTS:M1`, `NOTIFY:M1`:

```json
{
  "id": "M2",
  "name": "A customer's order goes from cart to receipt",
  "needs": ["ORDERS:M2", "PAYMENTS:M1", "NOTIFY:M1"],
  "bar": "As clear as Stripe's test-mode checkout: every step visible in one trace",
  "items": [
    {
      "id": "M2.1",
      "statement": "A cart of two items becomes a paid order and a receipt email within 10 seconds",
      "check": "./stack e2e checkout",
      "lock": "stack",
      "target": "local-stack",
      "status": "open",
      "evidence": ""
    }
  ]
}
```

  The fifteen-minute end-to-end run happens once, when the SYSTEM builder claims M2, in the script's own checkout,
  while the service builders keep merging.

Later the owner wants amounts in minor units. `PAYMENTS` returns `amount`; it should return `amount_minor`. The
planner settles the interface change in three milestones:

1. `PAYMENTS:M4` returns both `amount` and `amount_minor`.
2. `ORDERS:M5` reads `amount_minor`. Needs `PAYMENTS:M4`.
3. `PAYMENTS:M5` drops `amount`. Needs `ORDERS:M5`, and has an `attended` item: "deploy ORDERS at M5 or later and
   record its commit in `deploy/released.json`".

If a builder tried to drop `amount` early, `./stack contracts --against released` in the `Check:` line would fail
the merge, because the released ORDERS still reads it. `STATUS.md` shows `PAYMENTS:M5` waiting on the owner's
deploy. Nothing in this sequence needs a word the set doesn't already have.

## The runners-up, and why they lost

**A module's own paths and its own check.** Each module row gains the paths it owns and a check; `land` runs the
checks of the modules a merge touches and of the modules that need them. Resolves point 1 partly. It doesn't help
2, 3 or 4, and in a microservice system the end-to-end flows use every service, so most merges would run them
anyway. It adds a column, a field, and script logic mapping a diff to modules, and a path list that is wrong skips
tests silently, which weakens the guarantee. One point, real machinery, a new way to merge untested work.

**Deployment as a target.** A `staging` row in the Targets table, with items proved on it. Resolves part of 3 and
part of 2 (one namespace per worktree). But deploying is on the `Owner decides` line and spends money, so builders
deploying on every milestone contradicts the owner's control, and making Done mean deployed would need the script
to deploy. It also leaves 1 and 4 alone. The system module gets the useful part, the record of what is released,
without anyone deploying.

**Numbered slots on a lock.** `Exclusive resources: stack x3`, with `lock` handing out a slot number for ports.
Resolves 2 only, needs a script change, and is unneeded when the stack names everything from the checkout's path
and uses free ports. Keep it in reserve for a resource that really can't be duplicated, such as one shared cloud
account.

**Testing several merges together.** A merge queue that batches builders' rebased commits and tests them at once.
Resolves 1 only, is a large change to `land`, and makes a failure harder to pin on one builder.

**A second check that runs after the merge.** A slow `Check after:` line, run outside the lock, reverting on
failure. Resolves 1, but the main branch would hold untested work until it ran, which breaks the core guarantee.

## Verdict

One idea does cover most of the four. Treating the running system as state, owned by one module, resolves 2 and 4
fully and 3 and 1 mostly, using only fields the set already has (`needs`, item `check`, `lock`, `attended`, the
`Check:` line, the clean-clone section), at no cost to a project that isn't microservices. It leaves two honest
gaps: a flow already Done can regress between flow claims unless the contract tests catch it, and the set never
knows what is deployed except through the file the owner updates. Neither gap is new machinery's to close; both are
choices the project makes in its `Check:` line and its release habit.
