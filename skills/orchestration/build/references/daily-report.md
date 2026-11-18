# The daily report

This is for the lead, the agent the human chats with while it runs a build with the orchestrate set. Once a day,
and when you stop, write the human one screen in `<evidence>/build-reports/<date>.md`, and send it however the human
follows this session. `report --worktree <repo> --write` writes the factual half: what
is Done, each review's result, the planners' assumptions, what is Waiting or Blocked, the items that need the human,
the decisions saved in the human's name and the tokens each milestone used. Add the rest with links, and merge the
file with `adopt`. Until today's report is on the main branch, results carry a `report_due` field.

The human reads the report to catch what an unattended build would otherwise settle without them, so the whole
report covers:

- what is now Done, with links to the evidence;
- each review's result, linked. While the project's graded examples hold fewer than about ten reviews, flag every
  one, because the human's corrections are how the reviewer learns how strict to be;
- new Reviewer Inspection items, the ones a reviewer judges by running the product, so the human can adjust the
  milestone's quality bar;
- each reading of the human's words that a planner chose (the `Assumption:` lines, which a `PLANNED` result counts
  under `assumptions`);
- anything Blocked or Waiting, with its reason and what would move it on;
- every item that needs the human, in one list they can settle in one sitting, with the question for human
  feedback, or what to approve or connect and when to be at the machine;
- each glossary entry with a `Proposed:` line, so the human can agree the name or pick another. When they agree,
  remove the line and merge the glossary with `adopt`;
- every decision saved in the human's name since the last report, with the words saved, and a quote of any
  decision the script has no command for, such as a change to the project settings;
- how fast the work moved, from `flow`, and what you make of it when delivery has fallen behind the effort;
- how many builders ran, the Codex quota forecast, and the tokens each milestone used, which `cost` adds up.
