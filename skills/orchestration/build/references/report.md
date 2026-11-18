# The report

This is for the lead, the agent the human chats with while it runs a build with the orchestrate set. Write the
human a report when they ask how things are going, and when you stop.

The human reads it to catch what an unattended build would otherwise settle without them, and to decide whether the
build is heading where they want. So it is short enough to read in one sitting, and it starts with what needs them.

## The facts

`report --worktree <repo>` prints the facts as markdown, read from the records on the main branch, this machine's
usage and the runs going now. By default it covers the time since the last report that is at least an hour old, or
the last 24 hours when there is none. When the human asks about a stretch of time, such as "since yesterday
morning", pass `--since` with hours or a time. When they want a file to open rather than a message, `--write`
saves it under the repository's git folder, where no commit picks it up, and prints the path.

Its parts are what needs the human now, the decisions recorded in their name, what became Done, each review's
verdict, the planner turns with the task each was given, definitions changed through `adopt`, what is under way and
next, what has slowed down, the flow numbers, the choices made for the human, and the cost.

## What you add

The facts don't say what they mean, and that is your part. Put it at the top, in a few sentences: how close the
brief is to delivered, whether the build is moving as fast as it could, and what you are doing about anything that
isn't. A human who reads only your sentences should know whether to look further.

Then go through the parts that need the human, and make each easy to settle:

- Every item that needs them goes in one list they can answer in one sitting, with the question, or what to approve
  or connect and when to be at the machine.
- Ask them to check the decisions recorded in their name. The script can't tell who ran a `human` command, so a
  decision there that they didn't make is the thing to look for. Quote any decision the script has no command for,
  such as a change to the project settings, so it is on the same list.
- Point at each review while the project's graded examples hold fewer than about ten, which the report flags,
  because the human's corrections are how reviewers learn how strict to be. Name any new Reviewer Inspection items
  too, the ones a reviewer judges by running the product, so the human can adjust that milestone's quality bar.
- Name each choice made for them, from a planner's `Assumption:` lines or your own reading of their words, so they
  can overturn it while that is still cheap. Overturning one is a task for a planner.
- Name each glossary entry with a `Proposed:` line, so they can agree the name or pick another. When they agree,
  remove the line and merge the glossary with `adopt`.

Read "What has slowed down" and the flow numbers against the number of builders, and say what you make of them
when delivery has fallen behind the effort. Leave out what nobody needs to act on, because a long report hides the
one line that matters.

Send it the way the human follows this session. A report when you stop also says what is left and what would move
it on.
