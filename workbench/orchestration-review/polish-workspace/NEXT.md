# Where this work stopped, and what is left

Written 10 November 2026, at the owner's request, so that another session can pick it up.

## What is done

- `origin/main` is at `4ace464`. The branch `orchestrate-polish` in `/Users/ryannel/Workspace/skills` is at the
  same commit.
- `98619f5`, orchestrate 1.6.0: the `interview-me` and `domain-language` skills, the four existing skills
  rewritten in the agreed vocabulary, and the test record.
- `4ace464`, orchestrate 1.6.1: model and effort for each kind of agent. A settings line such as
  `Claude planner: claude-fable-5-2 high` applies on that host only. `Reviewer: high` sets an effort on every
  host. The reference is the last section of `skills/orchestration/plan-module/references/profile.md`.
- All 273 tests in `tests/orchestration` pass, `check_skill.py` prints `ok` for all six skills, and
  `claude plugin validate .` passes.
- The test runs and what they changed are in [results.md](results.md). The two reviews are in
  [review.md](review.md).

## What is left

1. **Install on this machine. Done on 10 November, on the owner's go-ahead.** The three files below are in
   `git stash` in skill-factory as "per-role draft (other session, 10 Nov)", and orchestrate 1.6.1 is installed
   for Claude Code and Codex. What follows is the record of how. Plugins load from `/Users/ryannel/Workspace/skill-factory`, which is
   still at `6244f1b`, so the machine is running orchestrate 1.5.4. That checkout has uncommitted changes to
   three files, made by another session at 19:50 on 10 November:
   `skills/orchestration/build/scripts/agent_loop.py`,
   `skills/orchestration/plan-module/references/profile.md` and `tests/orchestration/test_agent_loop.py`. They
   are an earlier draft of the per-role setting (`Planner: claude claude-fable-5-2 high`), which 1.6.1 replaces.
   Nothing there was touched. To install:
   - set the three files aside, for example
     `git -C /Users/ryannel/Workspace/skill-factory stash push -m "per-role draft" -- <the three files>`;
   - `git -C /Users/ryannel/Workspace/skill-factory pull --ff-only`;
   - from that folder, `python3 install.py --plugins orchestrate`;
   - check that `orchestrate:interview-me` and `orchestrate:domain-language` appear in a new session.

   The owner has not said in so many words that the other session's draft may be set aside. Ask first.

2. **Another session is editing `skills/prompting-agents/` in this checkout.** `SKILL.md`, `references/kinds.md`,
   `references/writing-style.md`, a deleted `references/models.md`, a new `references/models/` folder and
   `freshness.json` are uncommitted and are not this work. They were left out of both commits. Leave them.

3. **Things the tests did not cover,** listed in [results.md](results.md): no run with a real person, only
   Claude Fable 5.2 as the agent under test, the two last-round lines not run again, and whether either
   description loads its skill without being named.

4. **Scratch folders.** The test runs' working folders are under
   `/private/tmp/claude-501/-Users-ryannel--claude-spares-spare-9ZHcrE/101c62dd-273c-4dbb-b8ea-4ac2a6b47ab8/scratchpad/`
   (`convo`, `convo2`, `convo3`, `blind*`, `skillcopy*`, `libs`). Everything worth keeping was copied into this
   folder. The six Codex threads from the test conversation that went on to build
   (`convo2/existing-project-new-feature`) were archived on 10 November.

5. **This file** is uncommitted. Delete it when the list above is done.
