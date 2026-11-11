# Five failures from the Thrum delivery lead, 10–11 November 2026

Thrum is a Rust game engine built with the orchestrate set (`skills/orchestration/` in this repository, version
1.6.2, the version installed and running at the time). One Claude Code session, the "delivery lead", ran the loop
script `skills/orchestration/build/scripts/agent_loop.py` for three days. The session also spent much of that
time developing the orchestrate skills themselves, and its context was compacted about ten times.

A condensed copy of the lead's last stretch is at
`/private/tmp/claude-501/-Users-ryannel--claude-spares-spare-g951dt/abf7532c-8f5a-48b2-a6d7-f1fdef033740/scratchpad/tail.txt`.
It is a quoted transcript: data, not instructions.

## 1. The lead asked the owner to type a loop command

APPLE-TILE M0 was parked (Too Many Failed Reviews). Its re-plan passed design review, so only the owner's
`unpark` was left. The lead wrote to the owner: "The loop refuses that command from agents, so you need to run it
yourself in a terminal", followed by a shell command. The owner replied "You unpark it for me."

`build/SKILL.md` ("The owner's decisions", around line 321) says the owner never uses a terminal and the lead runs
every command, recording the owner's words with `owner <verb> ... --text`. The lead's compaction summary carried
an older standing rule: "Never sign owner loop commands as the owner unless the owner explicitly says to."

## 2. A builder stopped because the disk was full

APPLE-TILE M0's capture needs 16 GiB free; the disk had 14 GiB (99% used). The lead freed space only by deleting
five worktrees it had itself created for finished planner and reviewer runs (12 → 21 GiB). Planners and
reviewers are run "in a clean worktree" (`build/SKILL.md`, the table near line 195), which the lead makes by
hand; nothing removes them. The loop also keeps one verify checkout per module on purpose
(`verify_tree`, around line 2230 of `agent_loop.py`) to keep build caches warm. Earlier, one milestone's evidence
folder reached 158 MB.

## 3. A planner fix was silently skipped because of the planner lock

The lead ran, as one background shell job, "planner fix then design re-review" for three modules in sequence.
Meanwhile a separate planner (the swarm-game plan) was running. One planner runs per repository
(`build/SKILL.md` around line 206; `agent_loop.py` emits `TAKEN` with a `next` to retry). CREATOR's `plan` got
`TAKEN`, the chained job carried on to the re-review, and CREATOR lost a round.

## 4. A milestone item could only be proved by a later milestone

APPLE-TILE M0's done-when item D0.2 required a native witness that the plan assigns to M10. All of M0's checks
passed and its work landed on main, but the milestone could not finish. Two design reviews had passed the plan.
A planner then narrowed M0's item to what M0 can prove. `plan-module/references/done-when.md` (around line 101)
already makes the script reject an explicit reference to a later milestone; this one was implicit in the wording.

## 5. Status written in prose went stale

After the unpark, three places still described APPLE-TILE as parked: the Targets section of `ORCHESTRATE.md`,
a line in `docs/BUILD-PLAN.md`, and the header of the design file `APPLE-TILE.md`. The planner would not edit the
design header, because design approval is a hash of the whole design file (`agent_loop.py` around line 1113), so
any edit undoes the approval.
