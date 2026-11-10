# Iteration 1: grading statements

Written on 9 November 2026 before any run finished. Arm `a` is `plan-module` at `2ad09f8` (orchestrate 1.5.3). Arm
`b` is the working tree on branch `orchestrate-polish`. The statements come from the tasks, not from the skill's
rules.

## Case `props` (taste-led), two runs per arm

Prompt, as typed:

> we're making a small low-poly sailing game in godot 4 (saltwind). need the plan for the harbour props set, 12ish
> props: crates, barrels, bollards, a dock crane, a lantern with a looping creak sound, fishing nets, that kind of
> thing. should feel hand-made like A Short Hike, not asset-store. max 1.5k tris each, everything on a single 512
> atlas. repo is just the empty godot project. plan it so agents can build it

1. The owner chooses a visual direction from alternatives before the full set is produced.
2. The lantern's creak sound is sent to a person to judge, not left to an agent reviewer.
3. The triangle limit (1,500 per prop) and the single 512 atlas are each proved by a command, not by inspection.
4. Every look or style item names something concrete to compare against (the owner's pick, references, or a named
   shipped example), not adjectives alone.
5. The first milestone can start without the owner answering anything, apart from items marked for the owner.

## Case `logsift` (measurable), one run per arm

Prompt, as typed:

> need a plan for logsift, a rust cli that tails multiple log files, merges them by timestamp, filters with a small
> query language (level>=warn AND svc=api) and outputs ndjson. must handle 5GB files without loading them, and
> rotation (file renamed + recreated mid-tail). repo is just cargo init. one module is fine i think

1. The memory bound on a 5 GB file is proved by a command that a load-the-whole-file implementation would fail.
2. Rotation (rename and recreate mid-tail) is proved by a command that an implementation ignoring rotation would
   fail.
3. Items say what will be observed and don't script the builder's steps.

## Measured by script, both cases

Words across the plan files, number of milestones, number of items, median words per item (statement plus proofs),
and how many items carry an `ask`.
