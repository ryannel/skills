# Running these cases

These cases test a conversation, so one run needs two agents and someone to pass messages between them.
[run_conversations.py](../../orchestration-review/polish-workspace/run_conversations.py) does this with headless
Claude Code sessions, and [make_blind.py](../../orchestration-review/polish-workspace/make_blind.py) prepares a
case for a grader that must not know which run had the skill. The steps below say what they do, for a host
where you pass the messages yourself.

1. Make an empty working folder for the run. If the case has `place-files.sh`, run it from inside that folder.
2. Start a fresh subagent as the agent under test. Give it the working folder, the text of `prompt.md` below
   its settings block as the owner's first message, and, for the run with the skill, the path of a copy of the
   skill folder. Tell it that its reply will be shown to the owner and that the owner's answer will come back
   to it. Give the run without the skill the same things except the skill path.
3. Start a second fresh subagent as the owner, and give it only `owner.md`.
   For a case that ends in a brief, replace the script the skill runs with one that refuses to start agents.
   In the first round one agent merged its brief, started a planner and went on to build the project.
4. Pass each message from one to the other until the agent under test says it has finished, or twelve owner
   replies have been used. Save every message, in order, as `transcript.md` in the run's folder.
5. A case with no `owner.md` has no owner to play. Give the agent its prompt and let it finish.

A check with `focus: trace` is graded against the whole of `transcript.md`. A check with `focus: output` is
graded against the files left in the working folder. `claude plugin eval` sends one prompt and plays no owner,
so it can run only the cases that have no `owner.md`.

Write the checks' results down as [testing](../../../skills/agent-writing/skill-creator/references/testing.md) describes.
## What a planner does with the brief

Every check here grades the conversation or the brief. The brief is written for a planner, so the better test
is what a planner does with it. After a run of `vague-new-product` or `existing-project-new-feature`, give the
working folder to a fresh subagent with the `plan-module` skill and the task "Plan the project. The project
brief is docs/modules/BRIEF.md." Then read the `Assumption:` lines in the plan it writes, and compare them with
`owner.md`. Each fact on the owner's page that the planner had to assume, or got wrong, is something the
conversation failed to carry over. Do the same with the run that had no skill, giving the planner only the
owner's first message, and compare the two lists.
