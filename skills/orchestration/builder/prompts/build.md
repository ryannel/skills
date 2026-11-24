{goal}Build work package {work_package} of module {module}, using the builder skill ({skill}).

Finish the work package by merging the work with {work_package}'s status left as in_progress. Every item of {work_package} in {done} must have builder_result pass with evidence from the item's target. When you end with DONE, the script runs the checks on the merged work and sets the status itself: Done, or Ready for Review when the work package needs a reviewer.
{feedback}{earlier}
About this session:
- This worktree is yours for the work package. Other builders work in their own, so keep your changes inside this one.
- A lead is running this build.
- Start each commit's subject with `{module} {work_package}: `, because that is one way the script tells whose commit broke a check on the main branch.
- The script is `python3 {loop}`.
- The module's plan files are in {module_dir}/, and the project's agreed names are in {glossary}, if that file exists.
- Evidence files, such as captures and logs, go under {captures}/.
- {session}
{resources}{needs}{rules}{lead}
When the work is merged and proved, end with DONE and the evidence. If you can't go on, write your handoff to {handoff}, in the working folder too, then end with `BLOCKED <reason>: <one sentence on what would unblock it>`, or with `NEEDS_CONTEXT: <the question>` when you are missing a fact or a choice, and the lead gets it answered. The skill lists the reasons.
