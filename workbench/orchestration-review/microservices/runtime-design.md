# Microservices in one repository: the merge lock and running several copies

Status: design, not built. Nothing under `skills/` has been changed. Line numbers are for `agent_loop.py` at
commit `fea7c17` (orchestrate 1.7.0) unless another file is named. The working copy has uncommitted edits to `review_once` and `cmd_review` that shift lines after 4800 by up to 14; none touch the code cited here.

Two friction points, from the assessment of a microservice system kept in one repository with one module per
service:

1. Every merge runs the project's whole test command under one lock, so a 15-minute end-to-end test command lets
   only four merges happen an hour, for every builder together.
2. Several checkouts each start a full set of services, and they collide on ports, container names, volumes and
   the machine's memory.

The design in one paragraph: the script adds one environment variable to one run of the test command, and no
settings line. When `land` runs the test command before a merge, it sets `ORCHESTRATE_CHANGED_SINCE` to the commit
of the main branch it has just rebased onto, so a project whose tests are slow can test only what that merge can
affect. The run after the merge, which already exists and holds no lock, keeps testing everything. A project whose
test command ignores the variable sees no change. The second friction point needs no script change: it is fixed by
saying, in the project settings template, how each copy should name the services it starts, and the reason.

## Terms used here

- **Test command**: the `Check:` line of `ORCHESTRATE.md` (the glossary's name; the script calls it the profile's
  Check).
- **Merge lock**: the lock the script calls `integrate`, a file `orchestrate-integrate.lock` in git's common
  folder (`held`, 2042-2048), shared by every worktree of the repository but not by other repositories.
- **Merge-time run**: the run of the test command inside `land`, under the merge lock.
- **Run after the merge**: the run of the test command that the `run` command does in a clean copy of the main
  branch before it records a milestone as Ready for Review or Done.
- **Clean copy**: a checkout the script keeps for each module at `<git common dir>/orchestrate/verify/<MODULE>`
  (`verify_tree`, 2550-2563).
- **Stack**: one running set of a project's services, such as the containers `docker compose up` starts.

## What happens today

These are the facts the design rests on.

1. `land` holds the merge lock across the whole merge: fetch, rebase, the test command, and the push or
   fast-forward (`land`, 2590-2634; the lock is taken at 2594, the test command runs at 2609-2612 with a one-hour
   timeout). The test command runs in the builder's own worktree (`cmd_land` passes the worktree, 5751).
2. The script's own record commits go through the same lock. `loop_write` (2636-2664) commits a claim, an
   acceptance, a review or `STATUS.md` in a clean copy and calls `land` without the test command (2659). So a
   record commit for one module waits for another builder's merge-time run to finish.
3. The test command runs a second time after the merge. When a builder has every item passing, `run` calls
   `claim_problems` (4616), which makes the module's clean copy at the main branch's tip (2802) and calls
   `check_failures` (2805). That runs the test command and then every Automated Check (2757-2771), holding no merge
   lock. An Automated Check that names a `lock` runs under that lock (2763-2764); the test command never does.
   If anything fails, the claim isn't recorded and the builder is sent the failure (4616-4665).
4. So each milestone already runs the full test command at least twice: once at merge time under the lock, and
   once after the merge without it. The builder's `check` command is a third, optional run (`cmd_check`,
   5688-5713, which runs each item's check and then the test command in the builder's tree).
5. Commands the script runs inherit its environment. `run_proc` takes an `env` argument (2017-2018), and `land`
   and `check_failures` pass none (2609, 2766-2768).
6. Several copies can run the product at the same time: each builder's worktree; each module's clean copy, where
   the run after the merge runs the test command and the reviewer later runs the product (`cmd_review` uses the
   same clean copy, 4820); and the planner's clean copy (5269). Runs after the merge for different modules happen
   at the same time whenever two builders finish together. So the collisions in friction point 2 already hit the
   script's own runs, not only the builders.
7. `lock NAME -- COMMAND` (`cmd_lock`, 5630-5645) holds one named lock for every worktree of the repository. A
   lock is one-at-a-time; there is no "at most three".
8. `land --no-check` exists (usage at 181, flag at 7110, used at 5751) and skips the test command. No skill
   mentions it, but any builder can run it, so "main never receives untested work" is a convention today rather
   than something the script enforces.
9. The README defends the single lock as "a deliberate trade for two or three builders" (README.md:262-266), and
   cites Cohere's measurement that results got worse beyond two to four builders (README.md:263-264). Eight
   builders at once is outside what the set recommends, and the design below doesn't try to make it the norm.

## Friction point 1: the test command under one merge lock

### The limit no lock design can remove

If every commit the main branch receives must have passed the full test command as that exact tree, and the full
test command takes T minutes, then at most 60/T merges happen an hour, however the locking is arranged. With T = 15
that is four an hour. Three builders who each merge about once an hour, plus re-merges after a failed run, already
come close, and the record commits wait in the same queue (fact 2). There are only three ways past that limit:
make the run before the merge shorter, test several merges together, or stop testing before the merge.

### Chosen: let the project narrow the merge-time run, and keep the full run after the merge

The script change: in `land`, after a successful rebase and before the test command runs, read the commit the
branch now sits on, and run the test command with that commit in `ORCHESTRATE_CHANGED_SINCE`:

```python
# land(), between the rebase (2603-2606) and the test command (2608-2611)
since = git(tree, "rev-parse", base).stdout.strip()
code, out, err = run_proc(prof["check"], tree, 3600, shell=True,
                          env={**os.environ, "ORCHESTRATE_CHANGED_SINCE": since})
```

Then `git diff --name-only "$ORCHESTRATE_CHANGED_SINCE" HEAD`, run by the test command, lists exactly the files
this merge brings to the main branch. If the builder merged earlier in the same milestone, those commits are
already on the main branch and aren't in the list. On the retry after a rejected push (the loop at 2595), the
variable is read again after the new rebase.

Nothing else sets the variable. The run after the merge (`check_failures`), the `check` command, and the record
commits are unchanged. So:

- The merge-time run can be short. A project whose test command reads the variable tests the services the merge
  changed and every service that calls them, and nothing else.
- The run after the merge still tests everything, and it holds no lock, so its 15 minutes delay only that
  milestone's acceptance, not anyone's merge.
- A test command that ignores the variable runs in full at merge time, as it does today.

Why this keeps the guarantee the README cares about. Its two reasons for the lock are that no untested work
reaches the main branch, and that a rebase can break something the builder never touched. The merge-time run
still happens under the lock, on the exact tree the main branch will become, after the rebase. What it narrows is
which tests run. Narrowing is safe when the tests left out can't be affected by the files the merge changes, and
every earlier merge was tested the same way on the tree it produced. If both hold, each tree the main branch
receives would pass the full test command. The project owns the first condition, because only the project knows
which service calls which. The run after the merge checks it every time.

Who decides what a change can affect. Build tools such as Nx, Turborepo and Bazel can list what a change affects,
but from the import graph. Services that call each other over the network don't import each other, so a change to
one service's API wouldn't pull in its callers' tests. The module table in `ARCHITECTURE.md` already has a `Needs`
column naming what each module uses from the others, and that is the map a narrowed test command should follow:
for each changed service, also test every service whose row names it. Contract tests between services are the
cheap way to make those callers' tests short.

What a mistake costs. If the project's narrowing leaves out a test it needed, the broken commit reaches the main
branch, and the run after the merge for that milestone fails and sends the builder the failure. Until it is fixed,
the run after the merge for other modules fails on the same test too. Today the same thing happens when a test
passes in the builder's worktree and fails in the clean copy, so the path exists; it would just be more likely.

### Rejected

**A test command per module plus a smaller full test command.** This needs a setting per module (a column in the
module table, or eight `Check` lines), and `land` would have to know the module. It doesn't: `cmd_land` takes only
a worktree (5736-5751), and an ordinary fix with no plan is merged the same way (build-milestone/SKILL.md:80-81).
It also tests by module rather than by what changed, so a change to service A runs A's tests and not those of
service B that calls it, which is the rebase case the README warns about. The environment variable lets a project
do the same narrowing, by changed files, across modules, in its own code.

**The script choosing tests by changed paths.** The script would need a map from paths to tests and from each
service to its callers. That is a build system, and every project already has one. The variable hands the project
the one fact it can't get for itself in every place: the commit the merge is measured from. Inside `land` a test
command could find it with `git merge-base HEAD main`, but the branch name and remote vary (`base_ref`, 717-719),
and in a clean copy at the tip there is no branch to compare against at all.

**A merge queue that batches merges.** One holder would collect the waiting branches, stack them, run the full
test command once and move the main branch to the top. It is the only option that raises the 60/T limit with the
full test command still before every merge. It is also the most new machinery: a queue of waiting branches, a
holder running other builders' work, and, when a batch fails, testing parts of the batch again to find whose
change broke it, which is more full runs exactly when things are going wrong. `land` would stop answering LANDED or
FAILED for one builder's own work (5752-5755) and start waiting on others. The README already lists merging
through pull requests as left out until needed (README.md:563). Revisit only if lock waits are measured after
narrowing and are still long.

**Testing outside the lock, then merging only if the main branch hasn't moved.** This shortens how long the lock is
held, but under the guarantee each tree still has to be tested as itself. When two builders race, the loser has
to rebase and run everything again, so waiting turns into repeated test runs and the 60/T limit stays. Its one real
gain, record commits not waiting behind a test run, shrinks anyway once the merge-time run is short.

**Running the cross-service tests only after the merge.** The main branch would receive commits that never passed
the test command, and every builder that rebases onto one inherits failures it didn't cause, which is the harm the
README's lock exists to prevent. The run after the merge stays a safety net, not the gate.

**A separate lock for record commits.** Record commits change only the record file and `STATUS.md`, so they could
skip the queue. It would need a second lock and a rule for rebasing a tested branch over record-only commits
without testing it again. Leave it out unless record commits are seen waiting for minutes after narrowing.

## Friction point 2: several copies running at once

### Chosen: each copy names what it starts after its own checkout, written into the project's own commands

No script change. The fix belongs in the project's own start and test commands, because those are what every copy
runs: a builder by hand, `land` and the run after the merge through the test command, a reviewer through the
target's Run command, and the owner at their own desk. A name derived from the checkout's path is different in
every one of those places with nothing to set up. A variable the script exported would reach only the commands the
script runs.

The rules a project with services needs, and the reason for each:

1. Every name a stack takes on the machine comes from the checkout's path: the compose project name, and so its
   containers, networks and volumes, plus database names and queue or topic prefixes on anything shared. The clean
   copies are all called `verify/<MODULE>`, so two repositories with an `API` module on the same machine would
   collide on the folder name alone. The full path doesn't. For example:

   ```sh
   # scripts/stack-name: one name per checkout, safe as a compose project name
   top=$(git rev-parse --show-toplevel)
   printf '%s-%s\n' "$(basename "$top" | tr 'A-Z' 'a-z' | tr -cd 'a-z0-9')" \
                    "$(printf %s "$top" | cksum | cut -d' ' -f1)"
   ```

   `cksum` is in POSIX, unlike `sha1sum` (Linux) and `shasum` (macOS).

2. Ports are assigned by the system, not fixed. In compose, `ports: ["5432"]` publishes on a free host port, and
   `docker compose port db 5432` says which. Port offsets per copy were considered and rejected: they need
   something to hand out the offsets, and they still collide with other repositories.

3. A test run and a running product in the same checkout use different names, such as `<name>-test` and
   `<name>-run`. `land` runs the test command in the builder's own worktree (fact 1) while the builder's stack may
   be running there. A test command that ends by removing its stack would otherwise remove the builder's.

4. The test command starts its own stack and removes it when it ends, failed or not (`trap 'docker compose down -v'
   EXIT`). A module's clean copy is deleted when the module finishes (`drop_tree`, 2566-2576), and anything still
   running for it would be left behind.

5. Anything that can't be named per copy goes on the `Exclusive resources` line, and builders run it under
   `agent_loop.py lock <name> --`, as they already do for a simulator (build-milestone/SKILL.md:127-128). That
   covers a shared cloud account, and a machine that can hold only a few stacks: name one resource, `services`,
   and builders start a stack under it.

A milestone's own end-to-end scenario can already be an Automated Check with `"lock": "services"` (done-when.md:194;
taken at 2763), and the planner's existing rule moves a test into the test command once it has caught something
twice (plan-module/SKILL.md:211-213).

### Rejected

**The script setting `COMPOSE_PROJECT_NAME`.** Docker Compose reads it directly, which is tempting. But every
project that uses compose would get different container and volume names the day it upgrades, which breaks the
rule that a project without microservices sees no change, and the name wouldn't reach commands run outside the
script.

**The script exporting a copy number or port offset.** Needs a counter shared by every checkout and released when
a copy stops, which is a new concept with its own failure cases (a crashed copy that never releases its number).
System-assigned ports make it unnecessary.

**A "Setup" or "Teardown" settings line the script runs.** The "Starting from a clean clone" section is prose on
purpose: agents read it and the script doesn't. Making the script start stacks would make it own their lifetime
too. Leave it out until a leaked stack is actually seen.

## The exact changes

### `build/scripts/agent_loop.py`

1. `land` (2590-2634): after the rebase succeeds, set `ORCHESTRATE_CHANGED_SINCE` to `rev-parse` of `base`, and
   pass it in `env` to the `run_proc` that runs the test command (2609). About three lines. Its docstring (2591-2592)
   gains half a sentence.
2. Usage text for `land` (181-183): "runs the profile's Check, with ORCHESTRATE_CHANGED_SINCE set to the commit it
   rebased onto, so a Check can test only what the merge brings; the run that verifies a claim always runs it in
   full".
3. Unchanged on purpose: `check_failures` (2757), `claim_problems` (2774), `cmd_check` (5688), `loop_write`
   (2636), `profile` (489) and every settings line. No new command, flag or setting.

### `tests/orchestration/test_agent_loop.py`

Beside the existing `land(wt, prof, check=True)` test (around line 1621), one test whose test command writes
`$ORCHESTRATE_CHANGED_SINCE` to a file outside the tree: after `land` it equals the main branch's commit before the
merge; after `check_failures` in a clean copy the file says the variable was unset.

### `plan-module/references/profile.md`

1. The `Check` line (29) stays as it is, so the script reads it the same way.
2. The "Starting from a clean clone" placeholder (48-50) ends with: "If it starts services, how each copy names
   them, as [Several copies running at once](#several-copies-running-at-once) says".
3. A new paragraph in "Lines that need care", after the `Integrate` paragraph (71-74). Draft:

   > The script runs the test command twice for each milestone. The `land` command runs it before a merge, under
   > the lock that lets one merge happen at a time. The `run` command runs it again after the merge, in a clean
   > copy of the main branch, holding no lock. If the run before the merge takes more than a few minutes, every
   > builder waits for it in turn. So on that run only, the script sets the environment variable
   > `ORCHESTRATE_CHANGED_SINCE` to the commit of the main branch the work was rebased onto, and
   > `git diff --name-only "$ORCHESTRATE_CHANGED_SINCE" HEAD` lists the files the merge brings. A test command may
   > use it to test only what those files can affect, and tests everything when it isn't set. What a change can
   > affect includes each module that uses the changed one, as the `Needs` column of the module table says, because
   > services that call each other over the network don't show up in a build tool's list of what a change affects.
   > The run after the merge always tests everything, so a mistake in the narrowing is caught there, but only once
   > the change is on the main branch.

4. A new section, "Several copies running at once", holding the five rules above with their reasons and the
   `stack-name` example.

### `build-milestone/SKILL.md`

1. "Merging" (76-78) gains: "Some projects' test commands test only what your merge changes during `land`, and the
   `run` command tests everything after it. If that later run fails on a service you didn't touch, check first
   whether your change caused it, because your merge is the newest thing on the main branch."
2. The `Exclusive resources` paragraph (127-128) gains: "Start the project's services with its own commands, from
   the 'Starting from a clean clone' section, which name them after this worktree, so they don't collide with
   another builder's or the script's clean copy."

### `plan-module/SKILL.md`

"Targets and checks" (193-213) gains one paragraph: when the product is several services and the full test command
takes more than a few minutes, write the test command to read `ORCHESTRATE_CHANGED_SINCE` and the clean-clone
section to name each copy's services, as the project settings reference describes, and make both part of the first
milestone that starts a service, each proved by an Automated Check, so they exist before the second builder does.

### `README.md`

"One builder works on each module, and only a few builders run" (260-266) gains two sentences after "a deliberate
trade for two or three builders": a project whose full tests are slow can have the test command test only what a
merge changes, because the `run` command tests everything again after the merge, holding no lock; the project
settings reference says how. "Left out for now" (557-566) gains "a merge queue that tests several merges together:
narrowing the test command before a merge was enough for the case we looked at".

### `GLOSSARY.md`

The "Test command" entry (151-154) gains: "The `land` command may let it test only what the merge changes; the
`run` command always runs all of it." No new term. `ORCHESTRATE_CHANGED_SINCE` is a stored name and appears only
where a project's test command reads it.

## What a project with no microservices sees

Its test command runs once more in an environment with one extra variable it doesn't read. Same lock, same order,
same results, same output, no settings line to add or change, and `agent_loop.py profile` prints the same thing.
The new prose is in sections it can skip: one paragraph and one section in the settings reference, two sentences
in the builder skill, one paragraph in the planner skill.

## Unsure, or left open

- **No failure has been seen yet.** The domain's rule is to add a line only for a failure that has been seen
  (`.agents/skills/orchestration-skill/SKILL.md`, "Add a line only for a failure that has been seen"). This comes
  from an assessment, not a run. The script change is small enough to build now, but the README and skill lines
  should wait for a run on a real service repository, or at least a test fixture with two services and a compose
  file.
- **Build tools that hash the environment.** If a project's build cache keys on every environment variable, the
  merge-time run would miss the cache that other runs filled. I don't know of a common tool that does this by
  default, and I haven't checked.
- **How much narrowing saves.** A change to a library every service uses affects everything, and that merge-time
  run is as long as today's. The saving depends on how often merges touch shared code, which nothing here
  measures.
- **A broken main branch after a narrowing mistake.** Every module's run after the merge fails on it until someone
  fixes it, and the failure message (2768-2769, sent to the builder at 4665) doesn't say that the test command also fails at the commit before
  this milestone's work. Telling the two apart would need another full run. Left as is.
- **Machine capacity for the script's own runs.** Builders can take the `services` lock, but the test command run
  by the script after the merge can't, because the project's files don't know where `agent_loop.py` is installed.
  Several modules finishing together each start a full stack. The smallest fix, if this is seen, is for the
  script to export its own path (say `ORCHESTRATE_LOOP`) to the commands it runs, so a test command can call
  `lock`. I left it out because it isn't needed for correctness, only for memory.
- **Record commits waiting.** Fact 2 still holds: a claim or review record waits for any merge-time run in progress.
  Narrowing shortens the wait; it doesn't remove it.
- **`land --no-check`** (fact 8) lets any builder skip the test command. It is outside this design, but it
  matters more once the test command is slow, because skipping becomes tempting. Worth deciding whether only the
  script's own record commits should be able to skip it.
- **Eight builders.** Even with both changes, eight builders at once goes against the README's own evidence
  (README.md:263-264). The `Builders` line is the owner's lever, and eight service modules built three at a time
  is what the set is designed for.
