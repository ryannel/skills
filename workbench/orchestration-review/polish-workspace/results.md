# Test runs of `interview-me` and `domain-language`, 10 November 2026

This page records three rounds of test conversations, what they showed, and what was changed in the two skills
because of them.

## How a run works

Each test case is a request that a project owner might type, with a page of facts about that owner
(`owner.md`) that the agent under test never sees. The cases are in
[the intent-conversation evals](../../intent-conversation/evals/) and
[the domain-language evals](../../domain-language/evals/).

One run is a conversation between two headless Claude Code sessions.
[run_conversations.py](run_conversations.py) starts both and passes each message from one to the other.

- The agent under test ran on Claude Fable 5.2, the default for a headless session that day, with no installed
  plugin or skill visible to it (`--setting-sources project`). The run with the skill was told the path of a copy
  of the skill's folder. The run without it was told nothing else.
- The owner was played by Claude Sonnet 5.5, with no tools, from the case's `owner.md`.
- A run ended when the agent said it had finished and asked nothing, or after twelve owner replies. In the two
  cases that end in a brief, it ended when the owner approved the brief, so that no planner was started.

A grader then marked both runs of a case against checks written before any run. The grader was a fresh subagent
that saw the two runs as A and B in a random order ([make_blind.py](make_blind.py)) and was not told which had
the skill. Each case's `grades.json` holds every grade with its evidence. Each run's folder holds the
conversation (`transcript.md`), the files it left (`work/`) and its time and cost (`meta.json`).

After the runs, each session file of a run without the skill was searched for the skill's path and for any use
of the Skill tool. None had either.

## Grades

The number is checks passed out of checks in the case. The run without the skill was done once, in round 1, and
graded again beside each later round, which is why some cells show two or three numbers.

| Case | Skill | With, round 1 | With, round 2 | With, round 3 | Without |
|---|---|---|---|---|---|
| `clear-small-request` | `interview-me` | 5 of 5 | | | 5 of 5 |
| `vague-new-product` | `interview-me` | 10 of 13 | 11 of 13 | 12 of 13 | 1, 1 and 1 of 13 |
| `existing-project-new-feature` | `interview-me` | 9 of 10 | 10 of 10 | | 4 and 3 of 10 |
| `tangled-terms` | `domain-language` | 5 of 10 | 8 of 10 | 9 of 10 | 6, 5 and 5 of 10 |
| `new-name-mid-task` | `domain-language` | 6 of 6 | | | 4 of 6 |
| `small-tool` | `domain-language` | 4 of 5 | 4 of 5 | | 3 and 2 of 5 |

## What the runs showed

**`clear-small-request`.** Both agents built the flag with no questions and no brief. The skill does not make
an agent interview someone over a small, clear change, and that is all this case was for.

**`vague-new-product`.** Without the skill, the agent asked five questions in its first message, with example
answers, and built a whole app after the owner's second reply, with nothing agreed. It learned afterwards that
the look mattered most to the owner, and could not show the look to an owner who only sees the chat. While
testing, it stopped every process named `node server.js` on the machine. With the skill, the agent asked why
first, offered choices with a recommendation, wrote a brief that marks whose decision each one was, showed it in
the chat and built nothing. In round 1 it still missed the owner's two firmest requirements.

**`existing-project-new-feature`.** Without the skill, the agent wrote a brief before asking anything, invented
a reason for the feature, never mentioned that the code and the emails use other words than the owner, and told
the builder to keep the word the owner would have rejected. With the skill, the agent read the repository first,
found that customers had no way to prove an appointment was theirs, raised the three names, quoted the owner's
24-hour rule, and wrote the glossary entry.

**`tangled-terms`.** In round 1 the skill did no better than no skill. Both agents proposed tidy names of their
own, the owner accepted them, and the words the owner uses every day ("waiting for pickup", "overdue") never
came out. The agent with the skill also kept "stale", a word the owner did not understand.

**`new-name-mid-task`.** Both agents added a glossary entry for the new thing and reported it. The one with the
skill used the exact `Proposed:` line, recorded the new stored field in the entry, and chose a plain name
(`move_to_another_locker`) where the other coined one (`redrop`).

**`small-tool`.** This was written as a case an unaided agent would pass. It did not. Without the skill, the
agent wrote sixteen entries for a tool with four things in it, then built the tool. With the skill, the agent
wrote six entries, showed them in numbered steps, and stopped.

## What was changed in the skills, and why

Each change is one or two sentences in the skill, with the test that led to it given as the reason.

| After | Skill | Change | What the next round showed |
|---|---|---|---|
| Round 1 | `interview-me` | Ask what would make the result a failure even if it works, as a second open question beside "why", and don't answer it for the owner. In both brief cases the agent had filled this in itself. | Round 2: the owners named the wall with no signal, the look, and the rule that a moved appointment keeps its stylist, in their own words |
| Round 1 | `interview-me` | The brief template says to mark anything the owner didn't say, in every section. | Round 2: the items the agent filled in were marked |
| Round 1 | `domain-language` | Before proposing any name, ask the owner to say in their own words what the product does from start to finish. | Round 2: "overdue" and "pick up" came from the owner's telling |
| Round 1 | `domain-language` | Comments in the code are left alone and listed in the report. The agent had told the owner it would not touch the code and then reworded a comment. | Rounds 2 and 3: the comment was left and reported |
| Round 2 | `interview-me` | Ask the owner for a number or limit that the request turns on, and don't choose a default. The agent had left "how old is too old" open with its own default. | Round 3: "nothing should be up more than 6 weeks", quoted in the brief |
| Round 2 | `domain-language` | Ask what the owner calls a thing with no suggestion in the same message. The agent had asked and suggested together, and the owner took the suggestion. | Round 3: "waiting for pickup", the owner's own word |
| Round 3 | `domain-language` | Change the names in a document and keep every fact it states. The agent had cut two steps from an overview because the owner had no name for them. | Not run again |
| Round 3 | `interview-me` | In the brief template, what would make the result a failure moved from "Not part of this" to "How it will be judged". | Not run again |

## Checks that were wrong

- `small-tool`, check 03 said "at most one question". It counted a single request for approval that listed three
  assumptions as three questions. It now says the agent asks nothing before it writes the glossary. It was
  reworded after round 2, so the grades above use the old wording.
- `tangled-terms`, check 02 asks for entries named Drop-off and Pickup. The owner page gives those words, but
  the simulated owner said "puts it in a locker" and "pick it up", so no agent could pass it from the chat. It
  is left as written, and failed in every run.
- `vague-new-product`, check 10 asks for two of three things the owner would leave out. No agent asked what is
  left out, with or without the skill. It failed in every run, and the skill has no rule for it yet.

## What went wrong in the testing

**One conversation went on to plan and build its project.** In round 2 the owner approved the brief with one
correction ("Decision 5 is wrong… The rest looks fine"). The driver did not count that as an approval and
passed it to the agent. The agent did what the skills say: it merged the brief and the glossary with `adopt`,
started a planner, and when the simulated owner then said "Build it", ran the build as the lead. Before it was
stopped by hand, about 25 minutes later, it had started nine agent sessions that nobody had asked for: four on
Claude Opus 5.5 and five on Codex with GPT-6.1 Sol. All of it happened inside the run's scratch folder.

The driver now gives the agent a stand-in for `agent_loop.py` that refuses `plan`, `run` and `review`.

**That run is also the first time the whole set ran from a conversation.** The record is in
[round-2/end-to-end/](round-2/end-to-end/existing-project-new-feature/). The planner split the work into two
modules. A design review on Codex found that the private link could leak from the database, a planner revised
the design, and the second review passed. Codex built the first milestone of the first module and a reviewer on
Claude passed it. The second module, a page customers look at, produced three looks and stopped to wait for the
owner to choose one. The run was stopped during the second milestone, so it shows that the hand-over works and
does not show a finished product.

**The driver ended two round-2 conversations early.** The simulated owner's yes to one question was read as
approval of the brief. Those two are kept under [round-2/cut-short/](round-2/cut-short/) and were run again.

**The simulated owner did not always keep to its page.** It said "you decide" where the page says "I don't
mind", volunteered a word the page holds back until asked, and once approved a brief that contradicted the page.
A grader noted each case. This limits how much weight any one check can bear.

## What these runs can't show

- The owner was a model following a page. No conversation was run with a real person.
- Each case had one run without the skill and one to three with it. A difference of one or two checks is within
  what two runs of the same thing can differ by. The large differences (1 of 13 against 10 to 12, and 3 or 4 of
  10 against 9 or 10) are the ones to rely on.
- Only Claude Fable 5.2 was the agent under test. The skills were not run on Claude Opus 5.5, GPT-6 Astra or
  GPT-6.1 Sol as the agent the owner talks to.
- The checks grade the conversation and the brief. The better test is what a planner does with the brief, and
  what gets built. One run did that by accident, and none did it on purpose.
- Whether either description loads its skill without being named was not tested. Every run with the skill was
  told where the skill was.

## Time and cost

`total_cost_usd` is what a headless session reports. On a plan it is a measure of quota used, not a charge.

| | Conversations | Agent time | Reported cost |
|---|---|---|---|
| Round 1 | 12 | 22 minutes | $9.11 |
| Round 2, including the two cut short | 6 with a record | 5 minutes | $2.62 |
| Round 3 | 2 | 3 minutes | $1.98 |

The one long conversation was `vague-new-product` without the skill, at 12 minutes and $3.84, because it built
an app. The run that went on to plan and build is not in the table. Its nine sessions kept no cost. The owner
sessions and the twelve grader subagents are not counted either.
