{goal}Build milestone {milestone} of module {module}, using the builder skill ({skill}).

The goal: every item of {milestone} in {done} has builder_result pass, with evidence from the item's target, and the work is merged, with {milestone}'s status left as in_progress. When you end with DONE, the script runs the checks on the merged work and sets the status itself.
{feedback}{earlier}
About this session:
- This worktree is yours for the milestone. Other builders are working in their own, so keep your changes inside this one.
- A lead is running this build. Once the script's checks pass on your merged work, a reviewer in a new session judges the milestone.
- The script is `python3 {loop}`.
- The project's agreed names are in {glossary}, if that file exists. Use them in what you write, as the skill says.
- Evidence files, such as captures and logs, go under {captures}/. That folder is the repository's working folder, shared by every worktree on this computer and ignored by git, so leave them uncommitted.
- {session}
{resources}{needs}{rules}{lead}
When the goal is met, end with DONE and the evidence. If you can't go on, write your handoff to {handoff}, which is in the working folder too. Then end with `BLOCKED <reason>: <one sentence on what would unblock it>`, or with `NEEDS_CONTEXT: <the fact you need>` when what you are missing is a fact. The skill lists the reasons.
