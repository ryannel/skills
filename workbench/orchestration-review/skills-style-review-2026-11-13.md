# Sentence-by-sentence review of the orchestrate skills

13 November 2026. A review only: nothing in the set was changed.

## What I read, and against what

The standard is the `prompting-agents` skill and its `references/writing-style.md`, with the set's own authoring
spec and glossary.

I read these in full for this review: the builder's, reviewer's and planner's skills, `interview-me`,
`domain-language`, `proofs.md`, `profile.md`, `graded-examples.md`, `older-projects.md`, the three agent files and
the 19 saved prompts. For the lead's skill and `done-when.md` I re-read the parts changed today (lines 226 to 292,
and lines 94 to 139, 236 to 284 and 350 to 407) and relied on my full read from earlier today for the rest.

Not read: the script's other strings, meaning the `why`, `ask` and `problems` texts in results and the nudges it
sends, beyond the 19 saved prompts.

## Where it stands

| Habit from the skill | Does it hold? |
|---|---|
| No capitals for emphasis, no "be thorough", no pressure | Yes, everywhere |
| A boundary says what to do and why | Yes, with two exceptions (the lead's skill line 59, and an example in `profile.md`) |
| No invented steps, no reminders to do the obvious | Yes |
| No stories of past failures | Two story lines and two asides about Anthropic are left |
| Put the main thing first | Mostly. Two paragraphs bury the usual case |
| Define a term once, then keep to that word | No. This is the weakest habit: four pairs of words for one thing, one word for two things, and seven terms used before or without a definition |
| Make it clear whose job each action is | Mostly. Three sentences don't say |
| Write whole sentences, not squeezed ones | Mostly in the skills. The messages a resumed builder gets are still squeezed into labels |
| One example, then the plain statement | Two places stack examples |

About 70 findings in about 32,000 words. About 15 of them are in sentences I wrote today, and they are marked
"mine".

## Findings that run across files

### Two words for one thing

1. **Round and review.** The glossary's name for one review of a milestone is Round. The reviewer's skill uses
   both in one section (lines 140 to 156: "earlier reviews", "an earlier round", "four rounds", "round after
   round"). The builder's skill and the script's failed-review message say "four reviews with a repeat" (mine).
   `done-when.md` and the planner's skill mix them too ("each round's review").
2. **Rewrite and re-plan.** The set's word is rewrite, used 24 times in the planner's skill, `done-when.md` and
   the lead's skill. "Re-plan" appears in what I added today: the planner's skill line 283, the script's task
   ("Re-plan APPLE-TILE M2") and a glossary row. The stored names `replans` and `for_replan` keep the older word.
3. **"Your task" and "the message that started you".** The reviewer's skill uses the first at lines 72, 79 and
   140 and the second at line 160, for the same prompt. In the planner's skill "task" means the text the lead
   passed in `--task`, which a reviewer never gets.
4. **Definitions and items.** The script's two tasks for a planner say "change the definitions of M2". The
   planner's skill never uses that word, and says "items".

### One word for two things

5. **Round.** Besides one review of a milestone, it means one turn of the builder's own loop of fresh opinions
   (the builder's skill line 153, "keep the best round", and `proofs.md` lines 126 to 132).

### Terms used before, or without, saying what they mean

6. The builder's skill uses "the lead" at lines 68, 94 and 105 and says who that is at line 157.
7. The builder's skill uses "the human" from line 62 on and never says who that is. The reviewer's and planner's
   skills each say it once.
8. The builder's skill line 185 and the failed-review message use "Must Fix" without saying what it means. Only
   the reviewer's skill does. (Mine. Noted only, since its name is under discussion.)
9. The reviewer's skill line 56: "the human can promote it". Nothing says what promoting a Suggestion does or how
   it is done.
10. The reviewer's skill line 86: "read the code on both sides of the boundary". No boundary has been mentioned.
11. The reviewer's skill line 140 and the review prompt: "how many still count" and "since its counts last
    started". Neither says that the counts start again after a rewrite, a diagnosis or the human's decision. (Mine.)
12. The planner's skill line 235: "set tripwires". The word is explained only inside a table in `proofs.md`.

### Words the glossary doesn't hold

13. "A block" for a Blocked milestone: the builder's skill line 218 ("treat it as a block") and the lead's skill
    line 254 ("what kind of block it is").
14. `domain-language` line 65 gives "the ladder" as an example of a name an agent made up. The lead's skill still
    uses `ladder` as the field's name, which is correct for a stored name, but the reader meets the word with no
    plain name beside it.

## Findings by file

### `build-milestone/SKILL.md`, the builder

| Line | What is there | What is wrong |
|---|---|---|
| 52 to 59 | Item 2 of "What finished looks like" | Five sentences in one item. The fourth is 47 words and defines Ready for Review in its middle. |
| 107 | "such as "D2.5, the window resize recording"" | Every other example in the set writes an item as `M2.1`. |
| 108 | "or the name of a crate" | It assumes a Rust project. |
| 115 to 116 | "run again, on the merged commit, the proofs of the items those files could affect" | The thing to run comes last, after two interruptions. |
| 121 to 122 | "Prove an item that needs the human at the machine, for human feedback or for access, after your last merge, on a build of the merged commit, so that…" | Four qualifiers are stacked before the reason. |
| 147 | "saves each check's whole output to a file and names it" | "Names it" reads as giving the file a name. It means the command prints where the file is. |
| 189 | "the script sends you the review" (mine) | It sends a message that says where the review is. |
| 244 | "leave force-pushing out" | An odd way to say that work reaches the main branch only through `merge`. |

### `review-milestone/SKILL.md`, the reviewer

| Line | What is there | What is wrong |
|---|---|---|
| 60 to 62 | "Watch for work judged only in favourable conditions, such as… and for work that is correct but too subtle…" | One 46-word sentence holds two different things to watch for. |
| 104 to 111 | Item 3, what a finding says (mine) | Eight sentences in one item, doing two jobs: what a finding says, and how findings are ordered and marked. |
| 107 to 108 | "If the old name was still in the workspace switcher, and you didn't open the breadcrumb or the rail" (mine) | The example has no set-up. The reader hasn't been told that something was renamed, or what a rail is. |
| 116 to 122 | The bullet on the done-when file | Six sentences that set four fields. |
| 155 | "A hole that only an input nothing produces can reach is a Suggestion." | Hard to parse on a first read. |

### `plan-module/SKILL.md`, the planner

| Line | What is there | What is wrong |
|---|---|---|
| 15 to 21 | The paragraph on the project settings | It ends by introducing the script and the lead, which are a different subject. |
| 82 | "what another module owns that the milestone comes close to" (mine, and in `done-when.md` line 123) | "Comes close to" is vague. It means the milestone uses it or could be tempted to change it. |
| 140 | "Don't let the blocked builder build another module's part" | A planner doesn't direct builders. The sentence should say what the planner does: plan the work in the module that owns it. |
| 164 to 172 | The paragraph on the human's words | Nine sentences on four subjects. |
| 165 to 166 | "which letters count as "accents", how a "cli called x" is run, what a size limit is measured in" | Three clipped examples in a row, and the second can't be understood without its story. |
| 195 to 196 | "Anthropic dropped fine-grained splitting once its models could hold a longer build" | An aside the reader can't check or use. `proofs.md` line 130 has another. |
| 226 | "shouldn't rest on asking" | Compressed. It means the build shouldn't depend on each request being granted. |
| 230 to 232 | "A condition the work must survive… is not a condition for checking it." | The first sentence is abstract, and the point arrives in the third. |
| 243 | "so it is caught for nothing from then on" | "For nothing" can read as "pointlessly". It means at no cost. |
| 250 to 254 | Item 2 of "What finished looks like" | It leads with running the design review yourself. A planner the `plan` command started can't, and that is the usual case, which comes last. |
| 281 to 283 | "end with the `KEEP` line described under…" (mine) | The reader has to jump to a later section to learn the line's form. |

### `build/SKILL.md`, the lead

| Line | What is there | What is wrong |
|---|---|---|
| 59 | "and don't revert anyone's commits" | No reason of its own, and nothing to do instead. |
| 60 | "the tables below say who fixes it" | Two of the three tables went today. (Mine, by omission.) |
| 238 | One row for `CHECKS_FAILED`, `NO_PROGRESS_FOR_HOURS` and `STALLED` | Three results and three meanings joined by "or", so the reader matches them by position. |
| 241 | One row for `HOST_FAILED`, `WRONG_MODEL_OR_EFFORT` and `PAUSED` | The same, in a cell of about 60 words. |
| 244 to 250 | "The other commands print results of their own…" | One paragraph lists eight result words and two fields. |
| 269 to 270 | "the failed reviews (`rounds`)" (mine) | Round and review again. |
| 273 to 274 | "`plan` prints `KEPT`, with `who` has to act and the `next` for it" (mine) | The sentence is broken. |
| 284 | "That counts no round:" | Clipped. |

### `plan-module/references/done-when.md`

| Line | What is there | What is wrong |
|---|---|---|
| 43 | "Nothing else that plans work goes anywhere else." | Two "else"s. It means a plan lives in these files and nowhere besides. |
| 117 to 118 | "The answer is recorded with the `owner` command." | It doesn't say who runs the command. The lead does. |
| 136 to 137 | "it refuses, and elsewhere it warns about, a plan over…" | Two verbs wait for one object. |
| 138 to 139 | "These are the ways the plan files of earlier projects grew until nobody could read them." | A story of past projects. |
| 240 to 244 | The bullet that defines `findings` | One sentence carries three fields and a condition inside a condition. |
| 360 | "If a planner has been through this before" (mine) | Vague. It means the milestone already has one in `replans`. |
| 372 to 373 | "A kept plan counts as that step's one try" (mine) | "Try" is loose. It means the count goes up as it would for a rewrite. |
| 389 to 391 | "…so it holds up the milestone it sits in; put it in the later milestone." | An instruction tacked on after a semicolon. |

### `plan-module/references/proofs.md`

| Line | What is there | What is wrong |
|---|---|---|
| 46 | The "Benchmark tripwire" row | Two long compound sentences inside table cells. |
| 61 to 62 | "Agents that skipped this looked at whatever caught their eye, decided it looked fine, and missed the broken parts." | Told as a story of what agents did. The reason is that a reader without a list looks at what catches its eye. |
| 62 to 64 | A boat, a cloud, a command-line tool and a screen | Four examples in a row. |
| 105 | "to the minimum requirements, and to being different in kind, and to nothing more" | Three "and to"s. |

### `plan-module/references/profile.md`

| Line | What is there | What is wrong |
|---|---|---|
| 23 to 46 | The note after each settings line, such as "*(script: required; `push` rebases onto Remote/Branch and pushes without force; `local` fast-forwards the local Branch only)*" | Label style, with 30 semicolons. Planners copy these notes into every project's settings, where every agent reads them. Fixing it means moving the explanations into sentences under the template, which is a change of shape and not of wording. |
| 63 | "<for example: no GPL code; never modify ../other-repo>" | The example teaches a bare prohibition. Thrum's settings came out the same way: "never modify Broadsides". |

### `domain-language/SKILL.md`

Lines 98 to 99 and 103 to 104 give the same reason twice: a human tends to accept a name that is offered.

### The saved prompts

| Prompt | What is there | What is wrong |
|---|---|---|
| The builder's first prompt | "If you can't go on, write your handoff to… then end with `BLOCKED <reason>: …`, where the reason is…, or, when you're missing a fact, with `NEEDS_CONTEXT: …`." | One 49-word sentence holds three ways to end. It also repeats item 4 of the builder's skill. |
| The message on a resumed builder's turn | "Still binding: the goal is every item of M2 pass with evidence and the work merged with…" | Squeezed, under a label. |
| The notes after a turn limit and for a new session | "Continue the objective. Still open: M2.2, M2.3. … Passed: M2.1. Background jobs still running: …" | Facts given as labels. |
| The failed-review message | "After four reviews with a repeat" (mine) | Round and review. |
| The review prompt | "since its counts last started" (mine) | Not explained to a reviewer. |
| The planner's two tasks | "change the definitions of M2" | The planner's skill says items. |

The messages for failed checks, a refused merge, a branch from before 2.1.0 and a missing dependency read well as
they are.

### Files with nothing to change

`interview-me/SKILL.md`, `older-projects.md` and the three agent files. `graded-examples.md` reads well, though
none of its five reviews shows a finding that says what the reviewer left untried, which the reviewer's skill now
asks for.

## Facts that are wrong or out of date, found while reading

- The planner's skill line 243 names "the `Check:` line of the project settings". The template calls it
  `Test command:`, and `migrate` renames `Check:`.
- The lead's skill line 60 points to "the tables below". One is left.
- The glossary line 261 says a planner "rewrites" a milestone that is For Replan. Since today it decides why
  first.
- `interview-me` line 243 says the `plan` command waits until the planner has finished. The lead's skill says to
  run `plan` as a background command. Both can be true, but neither mentions the other.

## Smaller things

About fifteen lines are wrapped oddly where an edit was dropped in, such as the reviewer's skill lines 12, 37, 76
and 172 and the planner's skill lines 26, 37, 130, 253 and 300. An agent reads them the same, but they show where
the text was patched.

## What this review can't tell you

It says whether the text follows the skill. It doesn't say whether agents build better from it, and no build has
run on today's wording yet. It is also my own reading, of text I mostly wrote, and you have corrected my reading
of this style twice today.
