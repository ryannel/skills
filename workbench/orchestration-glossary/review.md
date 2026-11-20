# Glossary review: what to settle

Prepared on 2026-11-20 for the human's review of `skills/orchestration/GLOSSARY.md`. A subagent fetched the
sources on the same day, and anything it couldn't verify is marked.

## The main job, in the glossary's names

These steps use the glossary's names. Agreeing them agrees the names in them, and a name that reads wrong here is
one to change.

1. The human tells the **lead** what they want. The lead writes the **project brief**, and agrees names with the
   human into the **glossary**.
2. The lead runs the `plan` command. A **planner** writes the **module list**, and each **module**'s **design**,
   **plan file** and **done-when file**. Each **milestone** has **items**, each proved by an **Automated Check**, a
   **Reviewer Inspection** or a **Reviewer Question**, and a **quality bar**.
3. A **design reviewer** judges each design. It is **Design Approved**, or **Design Changes Requested**, and then
   the planner revises it.
4. The lead runs the `run` command. A **builder** builds the milestone in the module's **worktree**, proves it
   with **evidence** in the **working folder**, and **merges** it, running the **test command** first. Branches
   that arrive together merge as a **merge batch**.
5. The script runs its checks and sets the milestone **Ready for Review**, writing the **Ready for Review record**.
6. A **reviewer** writes a **review**. Its **findings** are each **Must Fix** or a **Suggestion**. A pass makes the
   milestone **Done** in the **record file**. A **failed review** leads to the next step of the **escalation**,
   and enough of them lead to a **Diagnosis**, which ends in a **Re-plan** or **Plan Kept**.
7. Through all of this, the lead keeps **watch** running, which wakes it at the **lead check-in** or on a
   **warning sign**. The **status page** shows the human where things stand, under **Needs you now** and
   **Choices made for you**.

## Where the field has a different term

Each line is a recommendation, worded so that "yes" accepts it. The stored names in files and commands stay as
they are; the new name goes in prose, with the stored name on its `Stored as:` line. Renaming a stored name would
need a `migrate` step.

1. **Reviewer Inspection → Reviewer Demonstration.** In systems engineering (NASA Systems Engineering Handbook
   §5.3), *Demonstration* means running the product and observing that it does what is required, and *Inspection*
   means examining it, or its documents, without running it. Our names use Inspection for running the product, which
   is the opposite of the standard. Use Demonstration for running the product, and call Reviewer Question a
   **Reviewer Inspection**? Moving the word to the other proof may confuse readers who learned the old names, so
   the simpler choice is to rename only the first proof to Demonstration and keep Reviewer Question.
2. **Hold limit → Lease.** A lock with a time limit, after which it is taken away from its holder, is a *lease*
   (Kleppmann, "How to do distributed locking"; Kubernetes' Lease, with `leaseDurationSeconds`). The glossary
   currently lists "lease" under Avoid. Call it the **lease duration**, and drop "lease" from Avoid?
3. **Builders count → WIP limit.** The Kanban Guide calls the number of items started and not finished
   *work in progress*, and a cap on it a *WIP limit*. Our count caps builders, and so caps milestones In Progress.
   Call it the **WIP limit**, with "the most builders running at once" as its definition?
4. **Main-branch check → post-merge check.** Trunk-based development (trunkbaseddevelopment.com) describes a
   second run of CI after a commit lands on the main branch, for slower tests. Call it a **post-merge check**? The
   automatic bisection is our own addition. No source found describes it.
5. **Item → acceptance criterion, done-when file → acceptance criteria.** Agile practice calls the conditions a
   piece of work must meet *acceptance criteria* (Atlassian), and an acceptance criterion paired with its own
   pass/fail check an *acceptance test* (Agile Alliance). Scrum's Definition of Done is the bar for all work, not
   one milestone, so it doesn't match. The glossary currently avoids "criterion" and "acceptance file". Keep
   "done-when", which is plain and is already in every skill, but put "acceptance criteria" in its first line? Or
   rename? This one is a real trade-off.
6. **Must Fix / Suggestion → blocking / non-blocking.** Conventional Comments marks review comments *(blocking)*
   or *(non-blocking)*. "Blocked" is already a milestone status here, so "blocking" would read as something to do
   with it. Recommend keeping Must Fix and Suggestion, and naming the field's terms in their entries.
7. **Diagnosis → root cause analysis.** Google's SRE book uses root cause in postmortems. A postmortem covers one
   incident, and our Diagnosis reads many failed reviews, so this is a near match. Recommend keeping Diagnosis,
   with root cause analysis in its first line.
8. **Ready for Review → In Review; Not Started → To Do.** Jira's defaults are To Do, In Progress, In Review and
   Done. Linear's are Backlog, Todo, In Progress and Done, and Linear's page couldn't be fetched to confirm them.
   Neither tool has Blocked or Waiting as a default status. Ours differ on purpose: Ready for Review means not yet
   judged, which "In Review" doesn't say. Recommend keeping ours.
9. **Evidence → artifacts.** CI systems (GitHub Actions) call files a run produces, such as test results and
   screenshots, *artifacts*. Ours are kept as proof, outside the run, so the meaning is narrower. Recommend keeping
   Evidence.

These already match the field, and now have a `Source:` line: Lead (Anthropic's lead agent), Worktree (git), Merge
batch (Bors' batching with bisection) and Flow (the Kanban Guide's flow metrics). Handoff now has a `Not:` line,
because in the OpenAI Agents SDK a handoff passes a live conversation to another agent, which isn't what ours does.

## Still marked Proposed

29 entries, the design statuses and 7 result names. The steps above cover most of them. The rest are the delivery figures: Delivery
history, Dashboard, Usage ledger, Weighted tokens, How full a session is, Stopped turn, Saved check output, Reused
check, What changed and Migrating a branch.

## Open question

Design Approved now has two causes: a DESIGN OK review, or the two-round limit approving the planner's revision.
One status or two? This waits on the work on the limit.
