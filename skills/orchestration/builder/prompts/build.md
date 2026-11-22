{goal}Build milestone {milestone} of module {module}, using the builder skill ({skill}).

The goal: every item of {milestone} in {done} has builder_result pass, with evidence from the item's target, and the work is merged, with {milestone}'s status left as in_progress. When you end with DONE, the script runs the checks on the merged work and sets the status itself.
{feedback}{earlier}
About this session:
- This worktree is yours for the milestone. Other builders work in their own, so keep your changes inside this one.
- A lead is running this build. Once the script's checks pass on your merged work, the script starts a reviewer in a new session to judge the milestone.
- The script is `python3 {loop}`.
- The project's agreed names are in {glossary}, if that file exists.
- Evidence files, such as captures and logs, go under {captures}/.
- {session}
{resources}{needs}{rules}{lead}
When the goal is met, end with DONE and the evidence. If you can't go on, write your handoff to {handoff}, in the working folder too, then end with `BLOCKED <reason>: <one sentence on what would unblock it>`, or with `NEEDS_CONTEXT: <the question>` when you are missing a fact or a choice, and the lead gets it answered. The skill lists the reasons.
