# The `domain-language` skill: what it is built from

Written 10 November 2026. The published skill is `skills/orchestration/domain-language/`.

## What the skill is for

A project's domain language is the set of names its owner and its agents agree to use. The skill tells an agent
how to agree those names with the owner, keep them in one file (the glossary), and keep to them, so that the plan,
the code and the chat use the same word for the same thing.

## The two sources

**This project's own vocabulary work.** On 10 November 2026 the owner of the orchestrate set said there were "a
ton of terms floating around" and that they no longer knew what the terms meant. Over about three hours the names
were gone through one by one. The result is [the agreed vocabulary](../orchestration-review/vocabulary.md) and the
orchestration README. The owner's corrections during that work are the skill's main source, as `skill-creator`
advises: each one is something an agent got wrong without help.

| What the owner said or did | Rule in the skill |
|---|---|
| "Let's always go with more explicit and easier to understand terms. We seem to have gone for shorter is better but that's not the case" | Choose the explicit, familiar name, even when it is longer |
| Chose "Ready for Review" over "claimed", "In Progress" over "taken", and proposed "Needs Human Feedback" | A name people know from the tools they use beats a new one. The owner's own word wins |
| "We've probably swung a little too hard here ... Blocked is fine" | Leave a good short name alone |
| "If parked is only used for too many errors then we should have a status specifically for that" | One name means one thing, and a status that covers two causes is split |
| Rejected a table of labels, then asked to be walked through the process in steps, and noticed "my modules have disappeared" | Show the names in use, as numbered steps. A step you can't write without a new word shows a missing entry |
| The names in question ("the loop", "the ladder", "parked") had all been made up by agents | A label an agent made up is one of the kinds of clash to look for |
| Existing records used `claimed`, `attended` and `needs` | A stored name stays, the entry records it under `Stored as`, and prose gives it once |
| The owner follows the work in a chat and does not open files | Put the names in the message itself |

**Other skill libraries.** A research agent checked the same fourteen libraries as for `interview-me`, searched
GitHub for others, and wrote [references/01-library-survey.md](references/01-library-survey.md). It also read Eric
Evans's own summary of ubiquitous language and a published summary of event storming. Only two of the fourteen
keep a real glossary: mattpocock/skills (`domain-modeling`, file `GLOSSARY.md`) and EveryInc's compound-engineering
plugin (`CONCEPTS.md`). Two smaller finds, from CodeAlive-AI and citypaul, supplied ideas.

## What was taken from the libraries

| Rule in the skill | Source | Evidence behind it |
|---|---|---|
| The file is called `GLOSSARY.md` | mattpocock, which renamed it from `CONTEXT.md` in version 1.3.0 | Its notes say the name should say what the file is. The rename cost its users an upgrade path, so the name is worth getting right at the start |
| An entry is a name, one or two sentences on what the thing is, and the names to avoid | mattpocock; compound-engineering; nearly every format | Agreement. mattpocock cut its template down to these three in May 2026 |
| A `Not:` line naming the neighbour it is confused with | CodeAlive-AI `ubiquitous-language` | An idea from a little-used skill, with no evidence. Kept because the owner's question "why are milestones claimed rather than done?" was exactly this confusion |
| The glossary holds names and nothing else | mattpocock; compound-engineering | A reported failure, and mattpocock's most-reported one (issue #130): the file was rewritten after every answer and used as a plan, with files passing 1,000 lines |
| Remove and merge entries | compound-engineering, pull request #1540 | Measured on one real project: 380 lines added and 11 removed over 25 commits, and entries grew from 35 to 76 |
| Only names particular to the project | Both, and every other format that mentions it | Agreement |
| Code shows which names are in use, and doesn't decide which is right | CodeAlive-AI; citypaul; mattpocock | Agreement |
| Say so at once when the owner's word disagrees with the glossary | mattpocock; compound-engineering, pull request #1487 | compound-engineering closed a gap where the clash was left until the write-up |
| A later session must be able to find the file without the skill | mattpocock; compound-engineering; CodeAlive-AI | A reported failure: mattpocock's issues #556 and #1376 show the skill, and a pointer file, not being loaded, on current models |
| A check that fails on an avoided name, for a name that must stay out | gstack; OpenSpec; citypaul | gstack records the incident: a renamed product's old name reached the README |
| Leave records of the past as written when a name changes | The practice in mattpocock, OpenSpec and gstack | Seen in three repositories, stated as a rule in none |
| One glossary, split only when two parts really need one word for two things | mattpocock; CodeAlive-AI; Evans | Agreement |

## What is ours

The survey lists what no library covers. The skill fills these from the first source above:

- **Prefer the plain name.** Every library's rule for choosing is about precision. None prefers the owner's word,
  or a longer ordinary phrase over a short invented one.
- **`Stored as`.** mattpocock and compound-engineering keep code names out of the glossary. CodeAlive-AI ties each
  term to one identifier. Neither covers a name that is fixed in saved data beside a clearer one used in prose.
- **Marking an entry the owner hasn't agreed.** mattpocock's notes warn that an unchecked entry written by an
  agent is read as fact by later sessions. compound-engineering writes entries without asking. Neither marks
  single entries.
- **A new name while the owner is away.** citypaul stops and asks. CodeAlive-AI adds the name silently. The skill
  takes the middle path: add it marked as proposed, report it, and carry on. This matters for a long unattended
  build.
- **Steps and statuses as well as objects,** and a test for "agreed enough to plan": the main flow can be written
  as steps with no word that lacks an entry. Evans's "describe scenarios out loud" is the nearest published form.

## What was left out, and why

- **Decision records** (mattpocock writes them beside the glossary). A different job. In this set, decisions go
  in the brief.
- **One identifier per term, and a lookup before naming every variable** (CodeAlive-AI). With a model that follows
  instructions closely, that is a glossary search before each local variable.
- **A hard stop on every new term** (citypaul). It would halt an unattended build each time a helper needs a name.
- **A fixed list of banned words** such as "Manager" and "Service" (CodeAlive-AI). One author's taste.
- **Relationships between terms, and example dialogues** (compound-engineering; the old mattpocock template).
  mattpocock removed both.
- **Event storming as the conversation.** No library runs it, and the steps in "show the names in use" do the
  useful part: ask what happens before asking what things are called.
- **Several glossary files for several areas.** One file until a real project shows the need.

## How the skill fits the set

- In an orchestrate project the glossary is `GLOSSARY.md` in the plans folder, because the script's `adopt`
  command merges files from there. Every agent looks for it by that path, so an existing project needs no change
  to its settings. Anywhere else it is `GLOSSARY.md` at the root, as in mattpocock.
- An entry is written as soon as its name is agreed. mattpocock does the same, and that is where its glossary
  turned into a running plan. The rule that the file holds names and nothing else is the guard, and the risk is
  accepted.
- The skill's description no longer covers "a new name is about to be introduced". A builder that needs one
  name follows the line in its own skill.
- `plan-module`, `build-milestone`, `review-milestone` and `build` each carry their own line about the glossary,
  so none depends on this skill being loaded.

## How it has been checked

- `check_skill.py` passes.
- A reviewer in a new session read it with the other orchestration skills. See
  [the review record](../orchestration-review/polish-workspace/review.md).
- It has been run on three test cases, in [evals/](evals/), with checks written before any run:
  `tangled-terms` (a small project full of made-up names, and an owner who has their own words),
  `new-name-mid-task` (the owner is away and a new thing needs a name) and `small-tool` (does it avoid an
  interview for five entries?). Each was also run with no skill and graded blind.
  [The results](../orchestration-review/polish-workspace/results.md) give every grade. In the first round the
  skill did no better than no skill on `tangled-terms`, because the agent proposed its own names and the owner
  accepted them. The rule to ask for the owner's telling first was added because of that run.

## Limits

- No library shows, by test or measurement, that later agents keep to a glossary, or that their work is better
  when they do. mattpocock's own notes doubt that it helps the agent and say the gain may be for the people. The
  skill is kept because this project's owner could not follow the build without agreed names.
- The first source is one conversation with one owner.
- Our own test runs used a simulated owner and one to three runs of each case.
- The research agent did not read three of CodeAlive-AI's reference files, and used Martin Fowler's two pages only
  for a date and one example.
