# The `interview-me` skill: what it is built from

Written 10 November 2026. The published skill is `skills/orchestration/interview-me/`.

## What the skill is for

Before this skill, the orchestrate set went straight from the owner's first message to a planner. A planner is a
new session that can't ask the owner anything, so anything unclear in the request became a guess. `interview-me`
tells the agent the owner chats with how to find out what the owner wants first, and to write it down as the
**project brief**, which the owner approves and the planner reads.

## What was read

A research agent read fourteen public skill libraries, shallow-cloned on 10 November 2026, and wrote
[references/01-library-survey.md](references/01-library-survey.md). It records the licence and the commit of each
library, the files read, what each skill makes the agent do, and what evidence each library gives. The three the
owner named were read most closely: obra/superpowers, mattpocock/skills and multica-ai/andrej-karpathy-skills.
The end of the survey lists the few files in them that were skipped. The
others were github/spec-kit, BMAD-METHOD, get-shit-done (and its successor gsd-core), EveryInc's
compound-engineering plugin, OpenSpec, gstack, addyosmani/agent-skills, anthropics/skills, Anthropic's official
plugins, pm-skills and wshobson/agents.

The numbers below are the maintainers' own. Nothing was run again here.

## What was taken, and from where

| Rule in the skill | Source | Evidence behind it |
|---|---|---|
| Ask only when the answer would change what gets built and only the owner can give it. Otherwise decide, and state the decision as a proposal | superpowers `brainstorming` v7.0.2 | A reported failure and a measurement. A version that always asked had a user on Opus 5.5 reporting questions about why they wanted a fix they had just asked for (issue #2530). With the filter and three other rules added together, filler questions fell from 41 to 23 in blind-graded test conversations |
| Ask why first, as an open question with no example answers and no guess in it | superpowers v7.0.2, pull request #2644 | Measured. A draft that offered choices first got a pick and lost the reason: good in 1 run of 9. In the released version the reason came out before any approach in 33 of 33 conversations, against 28 of 33 before |
| Then lay out named choices with what each costs and a recommendation | superpowers; mattpocock; spec-kit; OpenSpec | Measured in superpowers: on a real conflict, a bare "which one?" in 8 of 8 runs before, choices with a recommendation in 8 of 8 after |
| Word a yes-or-no question so that "yes" accepts the recommendation | mattpocock `grilling`, issue #706 | A reported failure: agreeing sometimes meant answering "no" |
| Read the repository before the first message, and never ask for a fact | superpowers v7.0.1; mattpocock; six others | A reported failure in mattpocock: a looser line let the agent answer the owner's decisions itself, so the skill now separates facts from decisions |
| One question in a message | Eight of the libraries | No measurement. mattpocock moved to rounds of independent questions, and its own notes say many users switch back. The skill allows a round when the owner asks for one |
| No process questions | superpowers v7.0.2 | Part of the measured filter above |
| Settle what it runs on | superpowers v7.0.0, issue #2482 | A seen failure: an iOS app was designed, the platform never asked, and a web app built |
| Nothing is planned before the owner approves the brief | superpowers v7.0.1 | Measured in one test scenario: the written design was skipped without asking in 24 of 24 runs before a rule to write it, and 3 of 24 after. Building before approval was counted separately: 4 times, then none |
| A weak yes approves nothing in particular | superpowers v6.4.1, issue #2258; OpenSpec; Compound Engineering; BMAD | A seen failure: "that scope is ok" was taken as permission to start building |
| The playback includes only what would change the build if wrong, and effects, not mechanisms | Compound Engineering `ce-brainstorm` | Tested on Claude and Codex with a simulated person: a word limit did not change the length of Claude's message, and a rule about its content is listed as what worked |
| Keep the owner's words apart from the agent's decisions | Seven libraries | Agreement, no measurement |
| Quote numbers, orders, limits and "never" in the owner's words, and number the decisions | mattpocock's notes; BMAD and get-shit-done number decisions, and Compound Engineering labels whose each one was | A reported failure: mattpocock calls the softening of precise answers by later documents its most serious open complaint |
| Fit the conversation to the work, and let the owner skip it | superpowers, Compound Engineering, BMAD, pm-skills | Agreement |
| A request that is several projects: agree which one this brief covers | Compound Engineering; superpowers | No measurement |
| What talk can't settle goes to options the owner chooses from | superpowers, mattpocock and three others build a throwaway | In orchestrate the planner already starts subjective work with options, so the brief only records that |

## What is ours

The survey's last part lists what no library covers. Four of those gaps are things an orchestrate planner needs,
so the skill fills them from this project's own experience, and they have no outside evidence:

- **How the result will be judged, and which judgements only the owner can make.** A planner has to write items
  that can be proved, and mark the ones that need human feedback.
- **How the owner wants to work:** which hosts, whether agents may push, what they want to decide themselves. The
  planner writes these into the project settings.
- **The request kept word for word.** The set already passed the owner's words to the planner unchanged, after a
  test run where a narrower reading dropped the letter `Ø`.
- **"I don't know", "I don't mind" and "you decide" recorded differently.** Each tells the planner something
  different about what it may change.

The reason the skill gives for itself, the two test runs, is also ours.

## What was left out, and why

- **Fixed lists and counts of questions** (spec-kit's five, conductor's six, gstack's six forcing questions). A
  current model reads a count as a quota. The skill gives a map of what the brief must cover, in superpowers'
  words "territory, not a script".
- **Pressure and hard gates.** The one stop the evidence supports is stated once, with its exception inside it.
- **Pushing the owner hard** (gstack "to the point of discomfort", mattpocock "relentlessly"). No evidence it
  helps.
- **A fresh reading of the brief by a second agent** (superpowers' builder check). The evidence is mixed:
  superpowers removed an earlier review loop that doubled the time with no gain. The lead in this set also
  starts no helper agents of its own.
- **Multiple choice through the host's question tool** (Compound Engineering's default). superpowers found that
  options steer, and the owner here follows the work in a chat.
- **A numeric score for clarity** (get-shit-done). An invented number.
- **User stories and a fixed specification template** (mattpocock `to-spec`, spec-kit). The planner writes the
  design. The brief stays about a page.
- **A rule for the owner who agrees with everything.** mattpocock names this as the main way a session fails, and
  nobody has a tested answer. The brief's marking of whose decision each one was is the partial guard.

## How the skill fits the set

- The brief is `BRIEF.md` in the plans folder. That place was chosen because the script's `adopt` command already
  merges any file in that folder, which was confirmed on a throwaway repository. No change to the script was
  needed. Every agent finds the brief by that path, so an existing project needs no change to its settings.
- When the owner says to skip the conversation, there is no brief, and the planner lists what it assumed.
- A small change needs no brief at all. The skill says so first, and its description sends small changes to
  `build-milestone`.
- `plan-module` now tells a planner how to read the three kinds of decision in a brief.
- `build`, the lead's skill, points to this conversation before the first `plan`.
- The skill carries its own short rules for names, and does not rely on `domain-language` being loaded, because
  mattpocock reports that naming a second skill in prose does not reliably load it, even on current models.

## How it has been checked

- `check_skill.py` passes.
- A reviewer in a new session read it with the other orchestration skills. Its findings and what was done about
  them are in [the review record](../orchestration-review/polish-workspace/review.md).
- It has been run on three test cases, in [evals/](evals/), each with the owner's first message, a page that
  tells a second agent how to play the owner, and checks written before any run: `clear-small-request` (does it
  over-ask?), `vague-new-product` (does it draw out the reason, the platform and the 6-week rule, and stop before
  planning?) and `existing-project-new-feature` (does it read before asking and raise the clash of names?). Each
  was also run with no skill and graded blind. [The results](../orchestration-review/polish-workspace/results.md)
  give every grade, the three lines the runs added to the skill, and what the runs can't show.

## Limits

- Our own test runs used a simulated owner and one or two runs of each case. No conversation has been run with
  a real person.
- Every measurement cited grades the conversation. None shows that what was built afterwards was closer to what
  the person wanted.
- Nearly all the numbers come from tests on Claude models. Compound Engineering's test also ran on Codex. None
  of the libraries reports results for GPT-6 Astra or GPT-6.1 Sol by name.
- The research agent did not read superpowers' separate test repository, or every neighbouring skill. The end of
  its notes lists what was skipped.
