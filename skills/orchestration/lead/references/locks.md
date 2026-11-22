# Locks and main-branch checks

Read this when the project settings, `ORCHESTRATE.md`, have `Exclusive resources`, `Shared resources` or `Main-branch
check` lines. A project without them never meets anything here.

## Locks

A lock lets runs share something the machine has only so much of. An exclusive resource, such as a simulator, is
used by one run at a time. A shared resource, such as a GPU that takes three renders side by side, is used by up to
the number the settings give it. Builders take a lock with the script's `lock` command, and an item's check can
name one, which the script takes just for that check. `lock gpu.alone` waits until nobody else is using the GPU and
keeps everyone else out. Use it only for a run that needs the whole device, because it keeps every other run waiting.

A lock keeps out only runs that take the same lock. So it limits how many runs share a device, and it doesn't make
the machine quiet. A timing taken while other builders work is noisy whatever lock it holds.

A command that holds a lock longer than the settings' `Lock hold limit`, 30 minutes unless they say otherwise, is
stopped, so one stuck run can't keep everyone else waiting. The test command is the exception: it keeps its own limit
of an hour, because a run stopped part way would fail every merge and look like a broken main branch.

`locks --worktree <repo>` shows who holds each lock now and who is queued behind them. `flow` reports, for each
lock, how long it was held, how long work queued for it, and how many holds ended in a failed command. A lock that is
busy most of the day, with hours queued against it, is a limit that more builders make worse. Its failed holds cost
the most, because nobody else could use the time they took. The fixes sit around the builders, not in them: fewer
builders on that resource, a cheaper proof, or a check that runs once on the main branch instead of once per
milestone. They go to a planner or to the user, as [reading delivery](../stages/4-build.md#reading-delivery) says.

## Main-branch checks

Some checks are too slow to run before every merge, and the project settings list them as `Main-branch check`
lines. One run of such a check, on the main branch's tip, covers everything merged since the last run, and the items
that depend on it pass from that shared result. The other modules carry on meanwhile, which is the point of running
the check after the merge.

An item's check that asks about a merged commit no run covers yet starts a run at once, whatever the interval. `watch`
also starts each check that is due, meaning its interval has passed and the main branch has moved since its last run,
so the interval spaces out the runs nobody is waiting for. `main-check --worktree <repo>` lists each check with its
latest result, what is running and whether it is due (`MAIN_CHECKS`), and `main-check <name> --start` starts one now
(`STARTED`, or `ALREADY_RUNNING` when one is in flight). Each run keeps a log, `runner.log`, where each finished
attempt shows as `RAN`.

A failure is tried again once, and one that holds is traced back through the commits since the last pass to the first
one that fails. Until a later run passes, every milestone merged after that commit fails the check too, so act on it
when `watch` names it as a warning sign. The failure names its commit and the modules it changed. Start a planner with
`plan --kind fix`, naming the commit, so it plans the fix before that module's unfinished milestones, or revert the
commit if the fix would take long. If it names no module, give the same task without one, because the lead doesn't
read or judge code.

A revert is `git revert <commit>` on the main branch, merged as any other commit, so the history the records name
stays. It takes work away from a module, so tell that module's builder in `run --message` what was reverted and why,
if its run is going. If the reverted work was part of a milestone that is Done, run `human rereview` on it, because
its review judged work that is no longer there. Then run `main-check <name> --start`, so a run on the new tip shows
whether the revert fixed it.

A run that exits 75 couldn't judge its commit, perhaps because a busy machine spoiled a capture. It is tried up to
three times, and if it still can't judge, it fails nothing and blames no commit. It shows as `unjudged`, and the check
runs again once its interval has passed. While an item waits for a check that hasn't judged yet, its builder's run
waits too, without using a turn. If runs keep coming back unjudged, the check itself needs to hold up under load,
which is work for the module that owns it.
