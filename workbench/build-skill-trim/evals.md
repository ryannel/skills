# Build skill trim: comparison runs

Old copy: the build `SKILL.md` before the trim, 7,185 words. New copy: the trimmed one, 5,606 words, plus
`references/older-projects.md`. Each request goes to a fresh subagent with one copy only, told to say exactly
which commands it would run and what it would tell the owner. Nothing is run against a real repository.

The checks were written before any run.

## 1. Human Feedback

The owner said "build it with one Codex builder". `run` printed
`{"result":"BLOCKED","reason":"needs_human_feedback","module":"CREATOR","milestone":"M2","next":{"ask":"Does the
brush preview at docs/evidence/CREATOR/M2-brush.png match the reference look?", ...}}`. You showed the owner the
picture and they replied "yeah that's right, ship it". What do you do now?

- [ ] Saves the reply with `owner feedback`, with the question in `--asked` and the owner's words in `--said`.
- [ ] Doesn't pass the reply through `run --message`.
- [ ] Runs the command itself, and gives the owner no command to type.

## 2. Review host

The settings say `Review host: same`, and the owner said "two builders, one Codex and one Claude". The Codex builder
on WATER M3 printed `{"result":"READY_FOR_REVIEW","review":true,"commit":"a1b2c3d","next":{"command":"... review
--module WATER --milestone M3 --commit a1b2c3d --worktree /repo/.wt/WATER"}}`. What do you run?

- [ ] Runs the review on Claude, naming `--host claude`.
- [ ] Keeps the Codex builder busy on another milestone that can start.

## 3. A failed review and the builders count

WATER M3's review printed `{"result":"REVIEWED","verdict":"FAIL","ladder":"replan","rounds":4,"fails":4,
"next":{"command":"... plan --worktree /repo --task \"Rewrite WATER M3 ...\""}}`. Meanwhile the owner, who asked
for two builders, says "start the UI module too". `run --module UI` printed `{"result":"REFUSED","running":2,
"next":{"ask":"Two builders are running, the number in Builders:. Start a third?"}}`. What do you do?

- [ ] Runs the `plan` command from `next` and doesn't start a builder on WATER M3.
- [ ] Puts the question to the owner before starting UI, and passes their words in `--more-builders` only on a yes.
- [ ] Doesn't start a third builder on its own.

## 4. An older project

The first `ready --worktree /repo` printed `{"result":"REFUSED","problems":["docs/plans has CORE-PLAN.md in the old
flat layout; run migrate"]}`. One module, CORE, has a worktree at /repo/.wt/CORE with three commits of its own.
What do you do?

- [ ] Runs `migrate --worktree /repo`.
- [ ] Runs `migrate --branch --worktree /repo/.wt/CORE` for the worktree, not a rebase by hand.
- [ ] Starts a planner afterwards to bring the plans into the current shape.
