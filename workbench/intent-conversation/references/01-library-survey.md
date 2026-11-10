# Library survey: how established skill libraries run the "what do you want to build" conversation

Written 2026-11-10. Source material: fourteen public skill libraries, shallow-cloned under
`/private/tmp/claude-501/-Users-ryannel--claude-spares-spare-9ZHcrE/101c62dd-273c-4dbb-b8ea-4ac2a6b47ab8/scratchpad/libs/`
(one folder per library), plus one successor repository I cloned into the same place
(`open-gsd_gsd-core`, see library 6). History came from each repository's own changelog,
release notes and docs, and from `gh` for a handful of issues and pull requests.
No script from any library was run.

## How to read this file

- **"The files say"** paragraphs report what is written in the library. File paths are relative
  to that library's folder under `libs/`. Line numbers are from the commit named in the table.
- **Quotes** are in double quotes with the file and line. They are kept short on purpose; the
  surrounding sentence is my paraphrase.
- **"Judgement"** paragraphs and the whole of Parts 4 and 5 are my own reading, not something a
  library says. Parts 2 and 3 are reporting, with judgement marked where it appears.
- "The agent" is the model running the skill. "The person" is whoever it is talking to.
- "One at a time" means one question per message. "Batch" means several questions in one message.

## Coverage

| # | Repository | Licence | Commit read (commit date) | What is relevant | How much I read |
|---|---|---|---|---|---|
| 1 | obra/superpowers | MIT | `22f0b463e7a5e579904dd6211a520321035526f7` (2026-11-03, v7.0.2) | `brainstorming` skill, its design spec, release notes | Fully, except the visual companion |
| 2 | mattpocock/skills | MIT | `4ae2317ddb22b046e26455e4f9c9b3aaaf62212d` (2026-10-31) | `grilling`, `grill-me`, `grill-with-docs`, `wayfinder`, `to-spec`, `domain-modeling`, `prototype`, their docs pages | Fully for those; not `triage`, `to-tickets`, `to-questionnaire` |
| 3 | multica-ai/andrej-karpathy-skills | No LICENSE file and GitHub reports none; `SKILL.md` frontmatter and `plugin.json` both declare MIT | `2c606141936f1eeef17fa3043a72095b4765b9c2` (2026-04-20) | One principle ("Think Before Coding") and two worked examples | Fully (it is one short file plus examples) |
| 4 | github/spec-kit | MIT | `142089067d5a66974cb215fe964c37d643020db5` (2026-11-10) | `/speckit.specify`, `/speckit.clarify` command templates | Both in full; `plan`, `checklist`, the `assess` extension only skimmed |
| 5 | bmad-code-org/BMAD-METHOD | MIT (plus a trademark file) | `a867e1604b365d48ea03cbd109da1066ba0c84bc` (2026-11-07) | `bmad-forge-idea`, `bmad-facilitate`, `bmad-agent-pm` | Those three; not `bmad-brainstorming`, `bmad-advanced-elicitation`, the analyst or product-owner agents |
| 6 | gsd-build/get-shit-done | MIT | `bdcaab2c752d9a33a1a1ca9acf3a3c81fb991815` (2026-05-31). **Archived**; its README redirects to open-gsd/gsd-core (MIT), which I cloned at `aa3bf0e986379d46c6e23c50bfa30ad812f5aa55` (2026-11-09) | `references/questioning.md`, `workflows/discuss-phase*`, `workflows/spec-phase.md`, `workflows/new-project.md` | Questioning in full; the workflows in large part. `questioning.md` is byte-identical in the successor; `discuss-phase.md` differs only in paths, hooks and a language rule |
| 7 | EveryInc/compound-engineering-plugin | MIT | `dd9b7921c9c80498eba84994ff1b8e1e81dbc1db` (2026-11-09) | `ce-brainstorm` and its references; two "solutions" write-ups about it | SKILL.md and nine of twenty reference files; not `ce-ideate`, `ce-plan`, `ce-prototype` |
| 8 | Fission-AI/OpenSpec | MIT | `579fcac57ae00c2dff38f971b6d88b6f1f098b8a` (2026-11-09) | `openspec-explore`, the clarifying step of `openspec-propose` | Explore in full; propose by search |
| 9 | garrytan/gstack | MIT | `dbb4b5064c3757354231f8dbb65de5b476949e2a` (2026-11-10) | `office-hours` (template and two section files), `spec` | Office-hours phases 1 to 4 and its rules; `spec` in outline; not `plan-ceo-review`, `autoplan` |
| 10 | addyosmani/agent-skills | MIT | `301b02b12bff98e4688e6984af6556802322bbde` (2026-11-01) | `interview-me`, `idea-refine`, `spec-driven-development` | `interview-me` nearly in full; the other two in part |
| 11 | anthropics/skills | No root licence file. The README says many skills are Apache 2.0; the `doc-coauthoring` folder has no licence file of its own | `2c5958ecac7cee2b583967a2c4981d0f4a75c579` (2026-11-06) | `doc-coauthoring` (adjacent: it is about a document, not a build); two lines in `skill-creator` | Outline only |
| 12 | anthropics/claude-plugins-official | Apache 2.0 | `dceb15d50832e6adf380bedc26dde03d251324b9` (2026-11-09) | `feature-dev` command | In full. `plugin-dev/commands/create-plugin.md` follows the same pattern; other plugins not relevant |
| 13 | phuryn/pm-skills | MIT | `9af7bfd0bc47fdad43c2eaa7a43cd13918e7aaef` (2026-11-08) | `/write-prd` command | In full. Thin for this purpose |
| 14 | wshobson/agents | MIT | `9c61ab243def98f72da12abd41cfcf5bcd91af9d` (2026-11-08) | `conductor/commands/new-track.md`, `before-you-build` skill | The question rules and the approval steps; thin for this purpose |

Every library had something. Libraries 11, 13 and 14 are thin, and library 3 has a principle but
no process. Apart from the GSD successor in row 6, I did not add any further library: the
fourteen were not thin overall.

---

# Part 1. What each library makes the agent do

## 1. obra/superpowers — `brainstorming`

Files: `skills/brainstorming/SKILL.md` (316 lines), `skills/brainstorming/builder-check-prompt.md`,
`docs/superpowers/specs/2026-10-05-brainstorming-rebuild-design.md`, `RELEASE-NOTES.md`,
`skills/using-superpowers/SKILL.md`, `skills/writing-plans/SKILL.md`.

This skill was rebuilt from scratch in v7.0.0 (2026-10-09) and retuned twice in the four weeks
after (v7.0.1, v7.0.2). It is the most recently tested text in the survey; Part 2 has the history.

**The files say.**

- *Before the first question.* The agent first asks itself what it already knows: "what do I know
  about what they want, and why?" (SKILL.md:19-20). If everything that matters is in the request, it
  does the task and says what it did. Otherwise, in an existing project or when the person pointed
  at material, it reads first: "keep reading until you can explain how the relevant parts work today
  and what this change would touch" (47-48). It must "Never ask what the project or their context
  already answers, or reopen what they've already decided" (48-50).
- *The first message* has two shapes (52-97). If the person already said what they want: about 200
  words that restate the request in the agent's words, add what the agent found in the project, and
  flag anything "like a constraint, a conflict, or a cheaper path" (63). Then one of: an open "why"
  question if the reason is unknown; the single open decision that would most change the build,
  with choices sketched and a pick; or, when nothing is open, a short design to approve. If the
  person has not said what they want: one open question, with the reason for asking: "Say why
  you're asking: what the answer would change about what you build" (79-80).
- *An offer to skip* is added only when the skill started by itself and not at the person's request:
  "Or if you'd rather I just dive in, say so." (92). If they take it, the skill is finished.
- *How questions are asked.* The filter: "Ask a question only when the answer would change what gets
  built and neither the request nor the project answers it. Otherwise, state your call and your
  reason as a proposal they can correct" (101-103). One at a time (106). Process matters (where
  files go, whether to write things up, whether to look further) are never asked: "Do them and say
  so" (105). Until the reason is known, questions are open "with no example answers attached"
  (115); after that, a decision with nameable choices gets each choice sketched, its trade-off, and
  the agent's pick (116-118). Each question builds on the last answer or on something found (143-147).
- *A list of topics, explicitly not a question list:* "This is territory, not a script. Never read
  these out as questions" (131-132): what kind of thing it is, why now, goals, non-goals,
  "anti-goals (what would make this a failure even if it technically works)" (136-137), prior art,
  current state, details they care about.
- *Technical choices.* The agent reads from how the person talks whether they want to decide the
  platform, language and libraries. If they talk about outcomes, the agent decides and states each
  choice in a line. "Any choice you make goes in the design as your call, never as something they
  agreed to" (128-129).
- *Pushback and alternatives.* Before writing anything up, the agent sends one message that lays
  out the ways of building it: think of several, drop the weak ones, sketch the two or three left
  with trade-offs, "Recommend one and say why, then ask which way they want to go" (162-163).
  There is no rule that tells the agent to cut scope; the nearest is the "cheaper path" line above.
- *Playing back.* As each part is understood, the agent describes it back "in about 200-300 words"
  (194), then returns to questions. "Only what they said goes in as theirs. Anything you filled in
  goes in as your proposal, with your reason" (198-199).
- *Throwaway builds.* The agent may offer a quick throwaway build ("spike") to learn what the
  person wants; it gets no tests and skips planning and review (182-188). Keeping it "is a new
  request" (294).
- *Splitting a large request.* One sentence: "If this is really several independent projects, say
  so, agree on an order, and brainstorm them one at a time" (226-227). `writing-plans` has a
  backstop that suggests separate plans if the design covers several subsystems
  (`writing-plans/SKILL.md`, "Scope Check").
- *Deciding it has asked enough.* SKILL.md gives no test during the conversation. The test is on
  the written document: a fresh subagent plays a builder in the domain and reports "only the
  questions you'd still need answered before you could plan this well"
  (`builder-check-prompt.md`:14-15). The agent sorts those into: already answered (add to the
  document), minor (decide and mark as its own call), and the person's (bring them in one
  message). "That's the only round of questions the check produces" (SKILL.md:265-266). The check
  runs for a project, not for a small change.
- *What it writes.* A design document: intent and why, goals, non-goals, anti-goals, constraints,
  the approaches considered and which was picked, the technical choices the person made, and
  "what's left to the builder" (229-239). A small change gets the same points in a line or two
  each. Location in a software repository:
  `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`, committed (245-246).
- *Approval.* Nothing is built until the person approves the document (269-283, inside a
  `<HARD-GATE>` tag). "Approval covers what you showed them. A design doc you haven't written
  isn't approved" (293).
- *Handoff.* After approval the agent invokes `superpowers:writing-plans` "and no other skill"
  (282). The plan carries a `Spec:` pointer to the design (release notes v6.3.0), and the person
  reviews the saved plan before anything runs (v6.4.1).

## 2. mattpocock/skills — `grilling` and the skills around it

Files: `skills/productivity/grilling/SKILL.md` (30 lines; the whole interview),
`skills/productivity/grill-me/SKILL.md` and `skills/engineering/grill-with-docs/SKILL.md` (each one
line that loads `grilling`), `skills/engineering/domain-modeling/SKILL.md`,
`skills/engineering/wayfinder/SKILL.md`, `skills/engineering/to-spec/SKILL.md`,
`skills/engineering/prototype/SKILL.md`, `skills/engineering/ask-matt/SKILL.md`,
`docs/productivity/grilling.md`, `docs/productivity/grill-me.md`,
`docs/engineering/grill-with-docs.md`, `docs/engineering/to-spec.md`,
`.out-of-scope/question-limits.md`, `.out-of-scope/native-question-tool.md`, `CHANGELOG.md`.

The docs pages are written for people, not the agent, and are unusually candid about what goes
wrong. I use them as evidence in Part 2.

**The files say.**

- *Before the first question.* Nothing is prescribed as a first step. Looking things up is woven
  into the interview: "Finding _facts_ is your job, never the user's" (grilling/SKILL.md:28). When
  a question needs a fact from the files or tools, the agent sends a subagent with a fresh context
  to find it and does not wait: only the questions that depend on that fact wait.
- *How questions are asked.* In rounds, not one at a time (changed in pull request #593). The agent
  models the subject as a tree of decisions and asks, in one numbered message, every decision
  whose prerequisites are settled: "the questions you can ask _now_ without guessing at answers
  you haven't heard yet" (8). Each question has a fixed shape, a title and body after a ❓ and the
  agent's recommended answer alone on a ➡️ line (12-22). "Word each question so "yes" accepts your
  recommended answer" (24). A question that depends on another still open in the same round waits
  for a later round (26). The docs give the opt-out: a person who wants one at a time adds a line
  to their own `CLAUDE.md` (docs/productivity/grilling.md:45-52).
- *Plain chat only.* The maintainer refuses to route questions through a host's question tool,
  because pickers "push the model towards multiple-choice questions with pre-baked answers"
  (.out-of-scope/native-question-tool.md:9).
- *Pushback and alternatives.* The interview skill only carries "relentlessly" (description and
  line 6) and the recommended answer per question. Real pushback comes from `domain-modeling`,
  loaded alongside by `grill-with-docs`: the agent challenges a word that conflicts with the
  project glossary, proposes a precise term for a vague one, invents edge-case scenarios, and
  checks the person's claims against the code: "Your code cancels entire Orders, but you just said
  partial cancellation is possible. Which is right?" (domain-modeling/SKILL.md:58). No rule cuts
  scope. Questions that talking cannot settle (how something should look or feel) go to a
  throwaway `prototype`.
- *Splitting a large request.* A separate, user-invoked skill, `wayfinder`, for work "more than one
  agent session can hold". Its first act is to name the destination ("The destination fixes the
  scope", wayfinder/SKILL.md:111). It then interviews breadth-first, writes a map as one issue on
  the tracker, and creates one child issue per decision that can be stated precisely now. Each
  child issue is a question "sized to one 100K token agent session" (57), typed as research,
  prototype, grilling or task, and marked as needing the person or not. What cannot yet be stated
  precisely goes in a "Not yet specified" section; what is ruled out goes in "Out of scope". One
  decision is resolved per session. If the first pass finds nothing unclear, it stops: no map
  needed (112).
- *Deciding it has asked enough.* "The session is done when the frontier is empty: every branch of
  the design tree visited, nothing left silently assumed" (30). There is no cap on questions, on
  purpose (.out-of-scope/question-limits.md).
- *What it writes.* `grill-me` writes nothing. `grill-with-docs` writes glossary terms into
  `GLOSSARY.md` the moment each is settled, and an architecture decision record under `docs/adr/`
  only when the decision is hard to reverse, surprising without context, and a real trade-off
  (domain-modeling/SKILL.md:66-74). Everything else decided stays in the conversation only.
- *Approval.* "Do not act on it until the user confirms you have reached a shared understanding"
  (30).
- *Handoff.* In the same conversation, without clearing it, the person runs `to-spec`, which says
  "Do NOT interview the user; just synthesize what you already know" (to-spec/SKILL.md:7). It
  checks one thing with the person (where the feature will be tested), then writes a spec from a
  fixed template (problem, solution, a long list of user stories, implementation decisions,
  testing decisions, out of scope) and publishes it as an issue labelled `ready-for-agent`.
  `to-tickets` then splits it. For single-session work the docs say to skip the spec and go
  straight to implementation (docs/engineering/to-spec.md).

## 3. multica-ai/andrej-karpathy-skills — `karpathy-guidelines`

Files: `skills/karpathy-guidelines/SKILL.md` (67 lines), `README.md`, `EXAMPLES.md`.

**The files say.** This is not a conversation skill. It is four standing principles for coding,
derived from a post by Andrej Karpathy that the README quotes: models "make wrong assumptions on
your behalf and just run along with them without checking". The first principle is the relevant
one (SKILL.md:13-21): state assumptions; if several readings exist, "present them - don't pick
silently" (19); say so when a simpler approach exists and "Push back when warranted" (20); when
something is unclear, stop, name it, ask. The fourth principle turns a task into a check that can
be verified ("Add validation" becomes writing tests for invalid inputs and making them pass,
56-58). It opens with a caveat: "For trivial tasks, use judgment" (11).

`EXAMPLES.md` shows the intended behaviour: for "Add a feature to export user data", a message
listing four numbered clarifications (scope, format, fields, volume), then "Simplest approach:"
with a proposal; for "Make the search faster", three readings with effort estimates and a
question. So in practice it shows a batch of questions, with a proposal attached.

It says nothing about reading the repository first, how many questions, when to stop, what to
write down, approval, or handing over to planning.

## 4. github/spec-kit — `/speckit.specify` then `/speckit.clarify`

Files: `templates/commands/specify.md` (349 lines), `templates/commands/clarify.md` (291 lines),
`templates/spec-template.md`, `CHANGELOG.md`.

Spec-kit inverts the order of the other libraries: the agent writes the document first and asks
afterwards.

**The files say.**

- *Before the first question.* `specify` takes the person's one-paragraph description and writes a
  full specification from a template immediately. It loads a project "constitution" if one exists.
  It does not read the codebase. Its instruction is "Make informed guesses" (specify.md:127, 301)
  and record them in an Assumptions section. It may leave at most three
  `[NEEDS CLARIFICATION: ...]` markers, only where the choice changes scope or user experience and
  "No reasonable default exists" (131). It lists things not to ask about because defaults exist
  (data retention, performance targets, error handling, authentication method; 314-320).
- *How questions are asked, first pass.* The (up to three) markers are put to the person all at
  once, each as a table of suggested answers with their implications plus "Custom"
  (206-234). No recommended answer here.
- *How questions are asked, second pass.* `clarify` scans the written spec against a ten-category
  list (scope, data model, user flows, quality attributes, integrations, edge cases, constraints,
  terminology, completion signals, placeholders; clarify.md:73-123), marks each Clear, Partial or
  Missing, and builds a queue of at most five questions ranked by impact times uncertainty. It
  asks "EXACTLY ONE question at a time" (141). Each must be answerable by a choice among two to
  five options or in five words or fewer (131-133). Each leads with a real question, then one
  "Why it matters" sentence, then "**Recommended:** Option [X]" with reasoning, then the options
  table (146-165). The person can reply "yes" to accept the recommendation.
- *Pushback, alternatives, scope.* None. Technical choices are kept out: the spec is "WHAT" and
  "WHY", "no tech stack" (specify.md:286-287).
- *Splitting.* Only "You must only create one feature per ... invocation" (specify.md:113).
- *Deciding it has asked enough.* Hard cap of five questions, or the person says "done", or all
  critical ambiguity is resolved (clarify.md:175-178). If the cap is hit with important categories
  open, they are listed as Deferred (237).
- *What it writes.* `specs/<number>-<short-name>/spec.md` with user stories, functional
  requirements, success criteria, assumptions; plus a quality checklist file. `clarify` writes
  each accepted answer into the spec straight away, under `## Clarifications` with a dated
  session heading as "Q: ... → A: ...", and also edits the section the answer belongs to,
  replacing any statement it contradicts (182-198).
- *Approval.* There is no approval step for the spec. The checklist is self-graded by the agent.
- *Handoff.* Frontmatter `handoffs` offers the planning command; `clarify` is "expected to run ...
  BEFORE" planning, and skipping it requires a warning about rework (clarify.md:60).

## 5. bmad-code-org/BMAD-METHOD — `bmad-forge-idea`, `bmad-facilitate`

Files: `skills/bmad-forge-idea/SKILL.md` (113 lines), `skills/bmad-facilitate/SKILL.md` (102 very
long lines), `skills/bmad-facilitate/references/guidance-planning.md`,
`skills/bmad-agent-pm/SKILL.md`, `CHANGELOG.md`. (`bmad-build/step-01-clarify-and-route.md` says
"Do not conduct an intent interview here", so the build skill is not part of this.)

Two different conversations: `forge-idea` tests whether an idea holds up; `facilitate` coaches a
person through a planning document (a product requirements document and similar) chosen by the
product-manager agent.

**The files say, for `bmad-forge-idea`.**

- *Before the first question.* It establishes three things, confirming rather than asking where
  the prompt already shows them: what the idea is, whether the person wants to clarify it, test
  it, or improve it, and whether it is new or a change to an existing project (42-53). For an
  existing project the files are the source of truth: "Do not accept a label or summary as
  proof", and a contradiction between files and the person's claim is resolved before continuing
  (76).
- *How questions are asked.* "Work one question at a time, in dependency order" (70). "Include your
  current best answer or hypothesis when it helps the user respond" (72). "Find discoverable
  answers yourself instead of asking" (72). Vague or overloaded words are challenged before going
  on (74).
- *Pushback.* Strong and deliberate: "Praise is noise" (80); agreement is allowed only when it
  helps the person think. The person can say "attack this" or "defend this" to change the
  stance. Each turn uses two invented or installed characters to raise objections (86-100).
- *Deciding it has asked enough.* Three named endings: the idea is hardened, killed, or merely
  clearer (104-108). "Do not steer the conversation toward "shall we build it?"" (12).
- *What it writes.* A running log on disk from the start, one bullet per decision, assumption,
  weak point or rejected idea, so a session survives interruption (61-64, 82-84). On "hardened":
  a short file of "only the decisions, rejected options, and reasons that matter downstream ...
  If it reads like a document, it is too long" (106). Always an HTML report.
- *Handoff.* It offers the short file to the planning agents as their input if they are installed.

**The files say, for `bmad-facilitate`.**

- *Before the first question.* "Read every input before asking" (Facilitation section): the ticket
  or document in play in full, other long sources through subagents.
- *How questions are asked.* It first invites the person to pour everything out ("why this
  document exists, who will act on it") and to add "anything else?", holding specific questions
  until the broad shape is out. It then plays back the purpose, reader and domain in its own
  message. Two paths follow. Coaching (the default): "one question at a time", each answer written
  into the document as it lands, and "No message asks more than two things". Fast (when the person
  wants speed): one batch of what the template requires plus at most three of the agent's
  highest-impact questions, then a whole draft with every default logged as an assumption.
- "Coach, do not quiz: open questions for vision and discovery, options with a recommendation only
  between named alternatives."
- *Pushback.* "Push back on thin answers, harder at higher stakes, hardest on unexamined
  assumptions, less as the document firms up or the user tires."
- *Deciding it has asked enough.* "Coaching stops when the remaining questions would not change the
  document", the template's own done condition holds, and every section is settled.
- *Who said what.* "Nothing goes in as the user's that they did not say or accept." A blanket yes
  does not count: "a yes to a group, such as "your recommendations", accepts nothing, because they
  did not weigh each one". Unconfirmed inferences are tagged `[ASSUMPTION: ...]` in the body
  (guidance-planning.md).
- *Scaling to the work.* Stakes are read as one of six levels from hobby to regulated; at hobby
  level "one line fills a section" and reviewers are skipped (guidance-planning.md).
- *Review and approval.* Reviewers include "a fresh reader given only the document, asked what it
  would still need answered to use it", one round. At the end the agent names "the three decisions
  you are least confident about, then wait for their read". Status becomes `final` unless a
  blocking open question remains.
- *No person present.* A "headless" mode asks nothing, fills every blank with a best guess logged
  as an assumption, and returns a status of complete, partial or blocked with the open questions.
- *Handoff.* The document sits in the initiative folder; the product-owner agent turns it into
  tickets.

## 6. gsd-build/get-shit-done (archived) and open-gsd/gsd-core

Files (same relative layout in both; root is `get-shit-done/` in the archived repository and
`gsd-core/` in the successor): `references/questioning.md` (162 lines),
`workflows/new-project.md`, `workflows/discuss-phase.md`,
`workflows/discuss-phase/modes/default.md`, `workflows/discuss-phase-assumptions.md`,
`workflows/spec-phase.md`, `CHANGELOG.md`.

Three separate conversations at three levels: the whole project, what a phase must deliver, and
how a phase should be implemented.

**The files say.**

- *Project level (`questioning.md`, used by `new-project`).* The agent opens with one free-text
  question, "What do you want to build?", then follows what the person emphasised. "Don't follow
  a script. Follow the thread" (11). A four-item list is to be checked silently, not walked: what
  they are building, why, who for, what done looks like (120-131). It names things not to do,
  including "Canned questions", "Corporate speak", "Premature constraints — Asking about tech
  stack before understanding the idea" (149-158). Follow-up questions go through the host's
  question tool with two to four concrete options, switching to plain text when the person wants
  to explain freely (103-118). When the agent could write the project file, it asks "Ready?" with
  the choices to create it or keep exploring (133-147). Output: `PROJECT.md`.
- *What a phase delivers (`spec-phase.md`).* Up to six rounds of two or three questions. Each round
  takes a different viewpoint (what exists, what is the simplest version, what is excluded, what
  could fail). After each round the agent scores four dimensions from 0 to 1 and computes an
  "ambiguity score" with weights; the gate is "ambiguity ≤ 0.20" (20). Output: `SPEC.md`.
- *How a phase is implemented (`discuss-phase.md`).* Before asking, the agent reads the project
  file, requirements, up to three earlier phases' decisions, and scans the code. It then lists
  three or four specific undecided areas, annotated with what the code already has, and the
  person picks which to discuss. Per area: four single questions with two or three concrete
  options and a recommended one, then "More questions ... or move to next?". Scope is fixed by the
  roadmap: a new capability is "its own phase" and goes into a "Deferred Ideas" section;
  "Don't lose it, don't act on it" (discuss-phase.md, scope_guardrail). The agent is told what
  not to ask the person: codebase patterns, technical risks, implementation approach.
- *An alternative with fewer questions (`discuss-phase-assumptions.md`).* The agent reads the code,
  states what it believes with file evidence and the consequence if wrong, and asks the person
  only to correct it: "~2-4 corrections vs ~15-20 questions".
- *What it writes.* `CONTEXT.md` per phase with sections for decisions, the documents the person
  referred to, existing code, specific ideas and deferred ideas; plus a log of each question, the
  options shown and the choice. Answers are checkpointed after each area.
- *Approval and handoff.* The "ready" question is the only approval. `CONTEXT.md` is read by the
  research and planning agents, which are told what is locked.

## 7. EveryInc/compound-engineering-plugin — `ce-brainstorm`

Files: `skills/ce-brainstorm/SKILL.md` (69 lines, mostly a table that routes to references), and
under `skills/ce-brainstorm/references/`: `interaction-rules.md`, `settled-decisions.md`,
`phase-0.md`, `dialogue.md`, `product-pressure-test.md`, `approaches.md`, `synthesis-summary.md`,
`plan-write.md`, `handoff.md`. Also
`docs/solutions/skill-design/confirmations-filter-by-salience-not-length-caps.md`.

The most elaborate procedure in the survey: about 2,200 lines of reference files.

**The files say.**

- *Before the first question.* The agent classifies the request (software or not; a quick question
  that needs no conversation; or a yes/no on adopting a named technology, which is sent to another
  skill). It sizes the work as Lightweight, Standard or Deep; "when it stays uncertain, take the
  heavier tier" (phase-0.md). If requirements are already clear it keeps the exchange brief
  (phase-0.md, 0.2). It scans the repository to a depth matched to size; for Standard and Deep it
  starts a subagent that writes a file of quotes from the code "during the user's think-time on
  the opening questions" (dialogue.md, 1.1). A claim that something is absent from the code must
  be checked or labelled unverified.
- *Decisions the person already made.* A decision carried in from earlier conversation is
  "settled" only if a trade-off or alternative was in view when they chose; a bare instruction
  nobody examined gets "exactly one in-pipeline challenge"; a settled one is never asked again
  (settled-decisions.md). "An agent never labels its own unexamined proposal, and never upgrades
  bare assent" (settled-decisions.md:15).
- *How questions are asked* (interaction-rules.md:20-30). One per turn: "Stacking several questions
  in a single message produces diluted answers". Multiple choice by default, through the host's
  question tool, single-select. An open question only when the answer is a story, when options
  would steer, "or when you cannot write 3-4 genuinely distinct, plausibly-correct options without
  padding". An open question must be concrete enough to answer; "What's your take?" is given as
  too thin. "Ask only for user decisions": look up what can be looked up; choose technical details
  from the project's evidence. Yes/no questions are worded so agreeing accepts the recommendation.
  The agent asks "what the user is already thinking before offering your own ideas" (dialogue.md).
- *Pushback.* The agent privately scans the opening for four gaps: no evidence anyone wants it, a
  vague beneficiary, no account of what people do today, and attachment to one solution shape
  (product-pressure-test.md). Each gap found becomes one open question; "a concrete, well-framed
  one may earn zero". "Use the result to sharpen the conversation, not to bulldoze the user's
  intent."
- *What the agent may recommend.* It recommends added scope only when the person's goal is not met
  without it, or when leaving it out lets harm land unnoticed. "A recommendation never narrows
  something the user asked for" (interaction-rules.md:29).
- *Alternatives.* Two or three approaches at the level of mechanism, not architecture, with at
  least one non-obvious angle. Order matters: "Present approaches first, then evaluate", because
  leading with a recommendation "anchors the conversation prematurely" (approaches.md).
- *Splitting a large request.* If the request holds more than one outcome that could be planned
  and delivered separately, the agent proposes a breakdown in plain language and asks "which one
  area this brainstorm should own"; the rest is kept as context, not scope (phase-0.md,
  coherent-work gate). Named devices or providers are coverage, not separate workstreams.
- *Deciding it has asked enough.* A listed exit condition: the main user is identified or marked
  unknown; the outcome is stated; in-scope and out-of-scope boundaries are known; success signals
  are known or recorded as assumptions; every gap found has been asked about; "OR the user
  explicitly wants to proceed" (dialogue.md, end of 1.3). Before leaving, the agent checks for
  consequences of combining the person's separate answers that they are unlikely to have tracked.
- *Playing back.* A short message in chat before any file: the problem in one or two sentences,
  what is being built, and "Call outs" for bets the agent made without asking. It must "Show what
  you understood and what you assumed, not what the user said" (synthesis-summary.md). It is
  asked open-ended, with no option menu.
- *What it writes.* Lightweight work ends as a chat paragraph and no file. Otherwise a
  requirements-only plan at `<docs root>/plans/YYYY-MM-DD-HHMM-<type>-<topic>-plan.md`, which the
  planning skill later extends in place. Decisions the person made carry an inline label,
  "(session-settled: user-directed — chosen over <alternative>: <reason>)". Implementation detail
  is kept out.
- *Approval.* The chat playback is the approval point. After writing, the agent runs its own
  four-part readiness check.
- *Handoff.* A menu of next steps; the planning skill receives the file path and the path of the
  code-quotes file. A caller skill can ask for a structured return (status, path or brief, open
  items, key decisions) in place of the menu (handoff.md).

## 8. Fission-AI/OpenSpec — `openspec-explore`, `openspec-propose`

Files: `skills/openspec-explore/SKILL.md` (355 lines), `skills/openspec-propose/SKILL.md`,
`CHANGELOG.md`, `openspec/explorations/explore-workflow-ux.md`.

**The files say.**

- Explore is described as "a stance, not a workflow. There are no fixed steps, no required
  sequence, no mandatory outputs" (16).
- *Before the first question.* The agent lists changes in flight and the project's existing specs,
  and reads the project's context and rules. "Do not ask the user to repeat facts you can verify"
  (48).
- *How questions are asked.* When planning a change: resolve the blocking decision before the
  details that depend on it; "Ask one focused question at a time, and briefly explain why it
  matters and which decision it unlocks. Batch questions only if the user asks" (51); recommend
  when evidence supports it; "Avoid a fixed question format" (52). It keeps confirmed decisions,
  proposed defaults and open questions apart: "Silence is not acceptance" (53).
- *Pushback.* Mild: challenge assumptions, reframe, compare options in tables, draw diagrams.
- *Deciding it has asked enough.* "Stop asking when the user has enough clarity ... do not exhaust
  every branch or force a proposal" (55).
- *What it writes.* Nothing by default; decisions are tracked "in the conversation, not in files".
  An optional summary (problem, approach, open questions). Any write needs the artefacts named, a
  direct yes/no question, and confirmation "in a separate user message" (351). Agreeing to
  recommendations "is not permission to write" (53).
- *Handoff.* The agent names the next command (`/openspec-propose`); it never starts implementing.
- `openspec-propose` goes the other way: it writes the proposal, design, specs and tasks in one
  step, asking first only where ambiguity "would materially affect scope, externally observable
  behavior, compatibility, or acceptance criteria"; "For minor details, make a reasonable
  assumption and record it" (propose/SKILL.md:54).

## 9. garrytan/gstack — `office-hours`, `spec`

Files: `office-hours/SKILL.md.tmpl` (379 lines; `SKILL.md` is generated from it),
`office-hours/sections/phase-2a-startup-diagnostic.md.tmpl`,
`office-hours/sections/phase-2b-builder-brainstorm.md.tmpl`,
`office-hours/sections/design-and-handoff.md.tmpl`, `spec/SKILL.md.tmpl`, `CHANGELOG.md`.

**The files say, for `office-hours`.**

- *Before the first question.* The agent reads `CLAUDE.md` and `TODOS.md`, the last thirty commits,
  the relevant code, and earlier design documents for the project. Then it asks one thing with six
  choices: what the person's goal is (startup, internal project, hackathon, open source, learning,
  fun). The answer picks one of two modes (tmpl:76-121).
- *How questions are asked.* "ONE AT A TIME" through the host's question tool, though the questions
  themselves are open (2a:69, tmpl:373). In startup mode there are six fixed questions (evidence
  of demand, what people do today, the specific person, the smallest version someone would pay
  for, what was observed, how it fares in three years), with a table choosing which three apply to
  the product's stage. In builder mode five looser ones ("What's the coolest version of this?").
  Questions already answered are skipped.
- *Pushback.* The strongest in the survey. "Be direct to the point of discomfort" and "Push once,
  then push again" (2a:19-20). Five phrases are banned, such as "That's an
  interesting approach" (2a:27-33). After the questions comes a separate step that challenges the
  premises (is this the right problem, what if we do nothing, what existing code already does
  this) and lists them for the person to agree or disagree with one by one (tmpl:209-225).
- *Skipping.* If the person says to skip the questions, the agent pushes back once and asks two
  more; on a second request it complies (2a:156-161).
- *Alternatives.* Two or three implementation approaches in a fixed block (summary, effort, risk,
  pros, cons, what it reuses). One must be the minimal version and one the "ideal architecture".
  A recommendation follows, then a stop until the person picks (tmpl:241-273).
- *Scope.* The "narrowest wedge" question and the required minimal approach.
- *Splitting.* Nothing found.
- *What it writes.* A design document, status DRAFT, at
  `<project state dir>/{user}-{branch}-design-{datetime}.md` under `~/.gstack`. It always ends
  with "the assignment", one real-world action for the person.
- *Approval.* The person approves and the status becomes APPROVED.
- *Handoff.* Later skills find the design document by its path pattern; the closing message
  suggests a plan-review skill.

**The files say, for `spec`.** A five-phase interrogation that ends in a filed issue. Questions
come "3-5 questions per round, max", numbered, at the end of the message (spec/SKILL.md.tmpl,
"How to Ask Questions"). The first phase runs until five things are answered: who is affected,
current behaviour, desired behaviour, why now, how we will know it is done. The agent reads code
before the technical round and cites what it found. The issue template includes a
"What's Working Well / Do Not Touch" section.

## 10. addyosmani/agent-skills — `interview-me`, `idea-refine`, `spec-driven-development`

Files: `skills/interview-me/SKILL.md` (235 lines), `skills/idea-refine/SKILL.md`,
`skills/spec-driven-development/SKILL.md`, `evals/cases/interview-me.json`, `evals/README.md`.

**The files say, for `interview-me`.**

- Its stated purpose is closest to the brief for this survey: find "what the user actually wants
  instead of what they think they should want" (3), before any plan, spec or code.
- *Before the first question.* The agent writes its best one-sentence reading of what the person
  wants, with a confidence percentage and what is missing (40-51). Nothing about reading the
  repository.
- *How questions are asked.* One at a time, each with the agent's guess and the reasoning behind
  it, in a fixed `Q:` / `GUESS:` layout (53-60). It argues the case: a wrong guess is faster to
  react to than a blank; batches "encourage skim-reading". It names the risk, "a polite user
  agreeing with your guess to be agreeable", and the countermeasure, sometimes guessing where it
  expects disagreement (77).
- *A probe for borrowed answers.* When the person answers with convention or buzzwords
  ("scalable", "the standard approach"), the agent asks: "If you didn't have to justify this to
  anyone, what would you actually want?" (90).
- *Deciding it has asked enough.* "Can I predict the user's reaction to the next three questions I
  would ask?" (136). If several rounds pass without that, the agent says so and offers to step
  back (140).
- *What it writes.* A restatement of five to eight lines: outcome, user, why now, success,
  constraint, out of scope (94-109). Saved to `docs/intent/[topic].md` only if the person agrees.
- *Approval.* An explicit yes. "Sounds good" and "Whatever you think is best" do not count; the
  latter means the person is delegating, so the agent offers two concrete options (113-122).
- *Handoff.* The agent offers the next skills and then stops its turn without starting them
  (124-130).
- *When not to use it.* Unambiguous requests, a person who asked for speed, and any run with no
  live person, where the agent should "flag that as a blocker" (36).

**`idea-refine`** restates the idea as a "How Might We" problem, asks three to five sharpening
questions "no more", then generates five to eight variations and converges on a one-page file with
a "Not Doing" list. **`spec-driven-development`** tells the agent to list its assumptions before
writing, and for a request that bundles several separately testable capabilities, to propose a
small table of modules and build order and get it approved "before any module spec is written";
then one spec per module.

## 11. anthropics/skills — `doc-coauthoring`

File: `skills/doc-coauthoring/SKILL.md` (375 lines). Adjacent only: it is for writing a document
with a person. The agent first asks whether the person wants the structured approach at all, then
a few questions about the document's audience and purpose, then invites the person to pour out
everything they know in any form. After that it asks a numbered batch of five to ten clarifying
questions that the person may answer in shorthand. Its test for enough context is worth noting:
it has enough "when edge cases and trade-offs can be asked about without needing basics
explained" (97). At the end a fresh subagent with only the document is asked the questions a
reader would ask.

## 12. anthropics/claude-plugins-official — `feature-dev`

File: `plugins/feature-dev/commands/feature-dev.md` (125 lines). Seven fixed phases. If the
request is unclear the agent asks what problem is being solved, summarises, and confirms. It then
sends two or three subagents to explore the code and reads the files they name. Only then comes
the main round: it lists edge cases, error handling, scope boundaries and similar gaps and must
"Present all questions to the user in a clear, organized list" (66), one batch. If the person
says "whatever you think is best", it gives a recommendation and gets explicit confirmation (69).
Next, subagents design two or three architectures (minimal change, clean, pragmatic); the agent
recommends one and asks. Nothing is written down as a spec; approval is a chat yes; implementation
follows in the same command.

## 13. phuryn/pm-skills — `/write-prd`

File: `pm-execution/commands/write-prd.md` (71 lines). The agent extracts what the input already
gives, researches what the web can answer, and asks only about three things if missing (the user
problem, the target users, the success measure), "in one message, three questions at most". If
the person says "just write it", gaps become marked assumptions. It writes a one-to-two-page
document, then says in one line what it left out on purpose and offers to tighten scope: "If the
idea is too big, proactively suggest phasing and spec only Phase 1."

## 14. wshobson/agents — `conductor` `new-track`, `before-you-build`

Files: `plugins/conductor/commands/new-track.md` (414 lines),
`plugins/before-you-build/skills/before-you-build/SKILL.md` (50 lines).

`new-track` asks a fixed, numbered list per kind of work (for a feature: summary, user story in a
set format, acceptance criteria, dependencies, scope boundaries, technical considerations), under
"CRITICAL RULES": one question per turn, "Maximum 6 questions total" (38-43). It writes
`conductor/tracks/{id}/spec.md`, the person reviews it, then it writes `plan.md` and the person
reviews that. `before-you-build` is not a conversation: it is a short risk review (demand,
positioning, monetisation, retention, trust, distribution) that returns a verdict, the main
assumption, the smallest evidence to find first, and what not to build yet.

---

# Part 2. Evidence the libraries give for their rules

Ordered by how much weight I would put on it. "Seen failure" means the library describes a real
session or a measured test in which the behaviour went wrong before the rule was added.

## Strong: measured, with numbers

**Superpowers, the v7 rebuild and its two retunes** (`RELEASE-NOTES.md`; issue #2530; pull request
#2644, whose description I read through `gh`). This is the best-documented sequence in the survey.

- v7.0.0 made the first message always ask an open question about "a real moment". Issue #2530
  ("v7's brainstorm questions are rather annoying", 35 comments, the reporter using Opus 5.5)
  gives the failures: asked to implement part B of a spec, the agent asked how the person's
  experience with part A had been; asked to fix a listed piece of technical debt, it asked what
  made them decide to fix it. The release notes for v7.0.1 concede the questions "got annoying
  fast and felt formulaic".
- v7.0.1 added reading the project before the first message, and the rule to lay out approaches
  and write a design document before building. Measured: in one test scenario the agent "skipped
  the doc without asking in 24 of 24 runs before this change and 3 of 24 after".
- v7.0.2 added the question filter (ask only if the answer changes what gets built), "why" first,
  named choices with a recommendation, and no process questions. Measured in blind-graded test
  conversations: filler questions fell from 41 to 23; the reason behind the request came out
  before any approach in 33 of 33 conversations (28 of 33 before); nothing was built before
  approval (it had been 4 times before). Against the older v6.4.2 skill on the same scenarios:
  fewer filler questions (23 against 34) and the reason drawn out far more often (33 of 33
  against 19 of 33).
- The pull request records what failed on the way, which is the most useful part:
  - Removing the mandatory question on its own "made things worse": the agent offered options in
    its first message, the simulated person picked one, and the reason never came out (graders
    rated the "why" conversation good in 1 of 9 runs, against 7 of 9 before).
  - "Ask why first" missed runs where the agent guessed the reason; adding "even if you can
    guess" fixed that.
  - A bare "which one?" on a real conflict (a spec that assigned one keyboard shortcut to two
    features) happened in 8 of 8 runs before; options with a recommendation in 8 of 8 after.
  - Allowing a short design in the first message spread to later messages, so it was limited
    strictly to the first message.
  - The offer to skip is counted as filler by graders but kept on purpose, as consent when the
    skill starts by itself.
- Earlier entries with a seen failure: the technical-choices rule was added "after a session
  designed an iOS app, never asked about platform, and built a web app" (v7.0.0, #2482). The
  approval rule was tightened after a session "took "that scope is ok" as permission to scaffold"
  (v6.4.1, #2258). The hard gate and checklist were added in v4.3.0 because "Models were skipping
  the design phase and jumping straight to implementation skills ... or collapsing the entire
  brainstorming process into a single text block".
- Evidence against a rule: v5.0.6 removed a loop in which a subagent reviewed the design document,
  because it "doubled execution time (~25 min overhead) without measurably improving plan
  quality" across five versions and five trials each. (The v7 builder check is a different
  design: one round, asking a narrower question.)
- Evidence on how to phrase rules
  (`docs/superpowers/specs/2026-06-10-positive-instruction-redesign-design.md`): in small tests
  on Opus, a prohibition on what to include in generated text did worse than no guidance (4.4
  unwanted items against 3.6), while a positive list of what the text should contain did best
  (3.0). Short prohibitions of one discrete act held. Tables of tempting thoughts paired with
  corrections are reported to work because they are read at the moment of decision.
- The test harness lives outside this repository (`docs/testing.md` points to
  prime-radiant-inc/superpowers-evals). I did not read it.

**Compound Engineering, the pre-write confirmation**
(`docs/solutions/skill-design/confirmations-filter-by-salience-not-length-caps.md`, dated
2026-09-30). The earlier problem: the chat summary before writing "had turned into a 15-20+ bullet
audit that users approved without reading". Tested with a simulated person who has hidden needs
and a blind grader, on Claude and Codex. What failed:

- A per-section limit produced a 620-word, 18-bullet confirmation on an ambitious scope; seven
  bullets restated decisions the person had just made.
- "Explicit caps did not move Claude output length": about 370 words with or without a 250-word
  cap.
- Loose tests ("something they would want to confirm or correct") let every restated feature
  through.
- What worked: open with the problem in the agent's words; include only what would change what
  gets built if wrong; describe the thing in prose; name effects, not mechanisms. And: "Agents
  copy examples more closely than they follow prose", so a worked example must obey its own rule.

A second write-up (`strong-models-mask-defensive-skill-fixes.md`, 2026-07-09) warns that a capable
model often already ignores a misleading instruction, so a test can show no difference even
though the fix matters on weaker hosts, and that a fix for one failure should be tested for
causing its opposite.

**gstack** (`CHANGELOG.md`). `office-hours` has eleven evaluation tasks, including two safety
tasks: no code written during a session, and no design document before the person picks an
approach. After the skill was cut by 40 percent in size, a panel scored it 27 of 27 against 26 of
27 before, with "no skill: 14/27". Evidence against a neighbouring skill: `/plan-eng-review` was
removed because "Two evals found no gain": plain Opus 5.5 without it found the planted flaws in 15
of 16 reviews, and a session told to use the skill cost 7.1 times a plain one.

## Medium: a reported failure, no measurement

**mattpocock/skills** (`CHANGELOG.md`, the docs pages, `.out-of-scope/`).

- Facts versus decisions (pull request #464). The old line said to explore the codebase when a
  question could be answered that way. Once another skill ran the interview to resolve a ticket,
  that line "read as license to answer _decisions_ autonomously too". The changelog says this
  fixes "students' reports of `/wayfinder` grilling _itself_ instead of the human".
- The confirmation before acting (#464) was added as an explicit stop. The docs still report the
  failure: "It ran out of questions and started building", most often on "lower-effort or
  non-frontier models", with the advice to add a line to the person's own instruction file.
- "Yes" accepts the recommendation (#1193, from issue #706): the recommendation sometimes argued
  against the question as worded, so agreeing meant answering "no".
- Rounds in place of one at a time (#593): the claim is that the "Same 13 questions land in ~3
  rounds instead of 13". No test is cited. The docs concede the weakness: the agent picks each
  round by judgement and can put two dependent questions together; and "a large part of the
  audience" switches back to one at a time.
- No cap on questions: issue #44, "Codex just asked me 200 questions". The maintainer's reply is
  that redundant questions are a quality problem to fix in the wording, "not in a counter", and
  that a very long session usually means the scope was too big.
- No question tool: five issues asked for it; the maintainer tried it and declined, because
  pickers push towards pre-written answers.
- Loading a second skill by name is unreliable ("a real bug, still unfixed"); the visible sign is
  "a session that asks everything at once with no recommendations".
- Decisions are lost downstream: "This is the most serious open complaint about the skill."
  Precise answers (ordering guarantees, negative requirements, numeric defaults) get softened
  into weaker prose in the spec.
- The person nodding along: "answering "agreed, agreed, agreed" for forty questions" produces a
  plan the agent wrote and the person did not decide. This is described as the main way sessions
  fail, with no countermeasure in the skill itself.
- The spec template's user stories "do not fit architectural work. You end up writing stories
  nobody asked for".

**OpenSpec** (`CHANGELOG.md`). #1716: guardrails let "if the user asks" cover answers to the
agent's own clarifying questions, "so an agent could treat a design discussion as a go-ahead" and
start editing files; hence the named-scope, yes/no, separate-message confirmation. #1832: two
passages contradicted each other about whether a capture request needed confirmation, so the same
request either wrote several files or stopped and asked, "depending on which passage the agent
weighed". #1017: explore was changed to ask dependency-aware questions, recommend defaults and
check the code before asking.

**spec-kit** (`CHANGELOG.md`, pull requests #3745 and #4507 read through `gh`). #3745: agents
presented topic labels or bare requirement numbers as questions (the example given is "Acceptance
device/runtime matrix (FR-023)"), so every question must now be a full sentence ending in a
question mark, followed by why it matters. #4507: the agent treated "better deferred to planning"
as a catch-all and skipped quality requirements, acceptance criteria and edge cases; deferral is
now limited to implementation method, technology comparison and task breakdown. #1557: the file
had two conflicting question limits (10 and 5).

**get-shit-done** (`CHANGELOG.md`). Fixes that point at failures of the question tool more than of
the conversation: an infinite self-discussion loop in automatic mode; the tool being called with
no person present; menus that broke on hosts other than Claude Code (now plain numbered lists);
empty tool responses (hence the retry rule); answers lost on interruption (hence checkpoints).

**BMAD** (`CHANGELOG.md`). The rebuilt critique skill reports that "blind judges ranked it above
the old skill and above a plain "push harder"". For the two conversation skills I found only
trigger tests, no behaviour tests, and no failure stories.

## None found

Karpathy guidelines (the source is a social-media post about model behaviour in early 2026; the
repository has no tests or changelog). `feature-dev`. pm-skills `/write-prd`. wshobson `conductor`
and `before-you-build`. Anthropic `doc-coauthoring`. addyosmani `interview-me` has one behaviour
test case (asks one at a time; does not propose solutions first; surfaces the underlying goal)
and no recorded results; its ledger of rejected changes has no rows for these skills.

---

# Part 3. Where the libraries agree and disagree

## Agreement

1. **Look things up; do not ask the person for facts.** Superpowers, mattpocock, BMAD (both
   skills), OpenSpec, Compound Engineering, GSD (discuss and assumptions modes), gstack,
   pm-skills. Exceptions: spec-kit `specify` does not read the code; Karpathy and `interview-me`
   are silent; `feature-dev` asks its opening questions before exploring but holds the main batch
   until after.
2. **Ask only what would change what gets built, and only what the person alone can decide.**
   Stated outright by superpowers, Compound Engineering, OpenSpec propose, spec-kit, BMAD
   facilitate, GSD discuss. Karpathy has no filter at all.
3. **Attach a recommendation when the choices can be named.** Superpowers (after the reason is
   known), mattpocock, spec-kit clarify, OpenSpec, GSD, gstack, `interview-me`, BMAD forge,
   `feature-dev`.
4. **Do not build during the conversation, and approval must be of something the person saw.**
   Superpowers, mattpocock, OpenSpec, gstack, `interview-me`, `feature-dev`, Compound Engineering.
   Several say the same thing about weak agreement: "Silence is not acceptance" (OpenSpec),
   "Sounds good" is ambiguous (`interview-me`), bare assent is never upgraded (Compound
   Engineering), a yes to a group "accepts nothing" (BMAD).
5. **Keep the agent's own guesses visibly separate from what the person said.** Superpowers (the
   agent's "call"), BMAD (`[ASSUMPTION: ...]`), Compound Engineering ("Call outs", provenance
   labels), spec-kit (Assumptions section), addyosmani spec skill, pm-skills, GSD ("You decide").
6. **Write down what is out of scope.** Nearly all that write anything: non-goals and anti-goals
   (superpowers), Out of Scope (mattpocock spec and map), Deferred Ideas (GSD), Scope Boundaries
   (Compound Engineering), "Out of scope" line (`interview-me`), "Not Doing" (`idea-refine`),
   Delay (`before-you-build`).
7. **Play the understanding back before writing.** Superpowers, `interview-me`, Compound
   Engineering, BMAD facilitate, `feature-dev`, GSD.
8. **Give the person a way out.** Superpowers (skip offer), Compound Engineering ("OR the user
   explicitly wants to proceed"), spec-kit ("done"), OpenSpec, GSD, gstack (after one pushback),
   pm-skills ("just write it").
9. **Match the amount of process to the size of the work.** Superpowers (three sizes), Compound
   Engineering (three tiers), BMAD (six stakes levels), pm-skills, GSD (skip when nothing is
   undecided).
10. **Build something throwaway when talking cannot settle the question.** Superpowers,
    mattpocock, Compound Engineering, GSD, BMAD.
11. **Keep implementation detail out of the document about what is wanted.** spec-kit, Compound
    Engineering, GSD, mattpocock (no file paths or code in the spec), superpowers (only the
    technical choices the person made).

## Disagreement

1. **One question per message, or a batch.**
   One: superpowers, BMAD forge and coaching path, Compound Engineering, OpenSpec, gstack
   office-hours, `interview-me`, conductor, spec-kit clarify.
   Batch: mattpocock (a round of all independent questions), `feature-dev` (one organised list),
   spec-kit specify (up to three at once), gstack spec (three to five per round), GSD spec-phase
   (two or three per round), pm-skills (up to three), `doc-coauthoring` (five to ten), BMAD fast
   path, Karpathy's examples.
   The arguments on each side: one at a time keeps each answer shaping the next and avoids
   "diluted answers" (Compound Engineering) and skimming (`interview-me`); rounds cut waiting
   without losing dependency, provided no question in a round depends on another (mattpocock).
   Only mattpocock has field experience on both sides, and reports that many users switch back.
2. **Open questions or multiple choice.**
   Compound Engineering defaults to multiple choice through the host's question tool and treats
   open questions as the exception. Superpowers does the opposite until the reason is known:
   "Options steer. Ask them to describe it first" (SKILL.md:289). Mattpocock refuses the question
   tool altogether. spec-kit clarify forces a choice or a five-word answer. GSD opens with free
   text and then uses the tool. gstack sends open questions through the tool.
3. **Whether to lead the person.**
   `interview-me` attaches a guess to every question from the first and says "Leading is the
   point". Superpowers found, in testing, that offering choices before knowing the reason lost
   the reason. Compound Engineering asks what the person is already thinking first, and shows
   approaches before its recommendation to avoid anchoring; spec-kit puts the recommendation
   first.
4. **A cap on questions.** spec-kit 5; conductor 6; GSD spec-phase 6 rounds; `idea-refine` 3 to 5;
   pm-skills 3. Mattpocock rejects caps on principle. Superpowers, Compound Engineering, OpenSpec
   and BMAD use a filter in place of a number.
5. **The test for "enough".** All branches of the decision tree visited (mattpocock); the agent can
   predict the next three reactions (`interview-me`); a weighted clarity score (GSD spec-phase); a
   listed set of things known (Compound Engineering, GSD project level, gstack spec); remaining
   questions would not change the document (BMAD); a fresh reader has nothing important to ask
   (superpowers, BMAD); the person feels clear (OpenSpec).
6. **What gets written, and where.** Nothing (`grill-me`, OpenSpec explore, Compound Engineering
   for small work); a short statement of intent (`interview-me`, BMAD forge); a design document in
   the repository (superpowers) or outside it in the tool's own state folder (gstack); a
   requirements file that planning later extends in place (Compound Engineering); a specification
   folder (spec-kit, conductor); an issue on the tracker (mattpocock, gstack spec); a per-phase
   decisions file (GSD).
7. **Who decides the technical "how".** Kept out of the conversation entirely (spec-kit, Compound
   Engineering, GSD: the person "shouldn't be asked"); read from how the person talks
   (superpowers); put to the person as implementation or architecture options (gstack,
   `feature-dev`).
8. **How hard to push.** gstack ("to the point of discomfort") and BMAD forge ("Praise is noise")
   at one end; GSD ("Never accept fuzzy answers") in the middle; superpowers lists
   "Interrogation" as something to avoid and Compound Engineering says not to "bulldoze the
   user's intent". `before-you-build` says to "avoid dismissing the user's idea".
9. **An independent read of the result.** Superpowers (builder check, one round), BMAD (fresh
   reader), Compound Engineering (a subagent that checks claims against code), gstack (an
   optional second model). Mattpocock, `interview-me`, spec-kit, OpenSpec: none. Superpowers'
   own history cuts both ways: it removed a review loop that showed no gain, then added a
   narrower one.
10. **Whether the skill starts by itself.** Superpowers and gstack want it before almost any new
    work. Mattpocock's `grill-me` and BMAD facilitate run only when the person names them.
    `interview-me` triggers on an underspecified request.
11. **What to do when the person asks to skip.** Superpowers offers the skip unasked when it
    started by itself. GSD discuss removes the skip option because the person ran the command.
    gstack resists once.
12. **Write first or ask first.** spec-kit and OpenSpec propose draft the whole thing with marked
    assumptions and ask afterwards; BMAD's fast path and GSD's assumptions mode do the same. The
    rest ask first.

---

# Part 4. What looks written for earlier, weaker models (my judgement)

All of this part is judgement. The test I applied: would a current model (Opus 5.5, Fable 5.2,
GPT-6 Astra, GPT-6.1 Sol) do the right thing without this text, and could the text make it do the
wrong thing by being followed too literally or too forcefully?

One caution before the list. Two behaviours that look like "weak-model" problems have recent
evidence on a current model, so the rule behind them is not dated even where the wording is:

- *Building before approval.* Superpowers measured this in tests run in October and November 2026
  (design document skipped in 24 of 24 runs; built before approval 4 times in one test set; the
  pull request names Opus as the model and the issue reporter was on Opus 5.5), and its v6.4.2 notes say frontier models "including Opus 5.5" would sometimes try to
  implement the whole project while writing the plan. A stop before building is still earning its
  place. What the evidence supports is the stop and a precise definition of what counts as
  approval, not capitals.
- *Asking too much.* The v7.0.0 failure was a capable model following a "always ask an open
  question" instruction faithfully. Current models over-comply with question quotas; that is the
  live risk, more than under-asking.

## Capitals, pressure and absolute language

- **Superpowers.** `skills/using-superpowers/SKILL.md`:10-16 ("ABSOLUTELY MUST", "even a 1%
  chance", "You cannot rationalize your way out of this") and the twelve-row table of forbidden
  thoughts (36-51), including "Skill check comes BEFORE clarifying questions". The brainstorming
  description opens "You MUST use this before any creative work" (`brainstorming/SKILL.md`:3);
  the design spec says this strong wording was kept deliberately. Likely harm: the skill starts
  on requests that do not need it, which is what the skip offer and the "do it and say what you
  did" branch then have to undo. Also `<HARD-GATE>` as a tag (269-283): the content is sound and
  evidenced; the tag is shouting.
- **gstack.** `office-hours/SKILL.md.tmpl`:68 ("HARD GATE"), :273 ("STOP. Do NOT proceed"), :373;
  `sections/phase-2a-startup-diagnostic.md.tmpl`:3 ("These are non-negotiable"), :69 and :154
  ("ONE AT A TIME", "STOP after each question"). `spec/SKILL.md.tmpl`:81 ("STRICT — do not skip or
  combine phases").
- **addyosmani `interview-me`.** :124-130 ("(CRITICAL)", "STOP YOUR TURN IMMEDIATELY"), :111
  ("non-negotiable").
- **`feature-dev`.** :61 ("CRITICAL ... DO NOT SKIP"), :89 ("DO NOT START WITHOUT USER APPROVAL").
- **conductor `new-track`.** :38-43 ("CRITICAL RULES").
- **spec-kit.** `clarify.md`:19 ("You **MUST** consider the user input"), :141 ("EXACTLY ONE"),
  `specify.md`:227-231 ("CRITICAL - Table Formatting", with instructions on pipe spacing).
- **GSD.** `questioning.md`:105-107 ("STOP using AskUserQuestion ... you MUST") and :158 ("NEVER
  ask about user's technical experience"); `discuss-phase.md` ("CRITICAL: No scope creep").
- **OpenSpec explore.** :14 ("IMPORTANT ... you must NEVER write code"). Mild by comparison.

## Fixed question lists and counts

- **conductor `new-track`** :47-150: the same six numbered questions for every feature, with a
  required user-story sentence shape. A person with a clear request answers a form.
- **gstack office-hours**, the six "forcing questions" with a routing table by product stage
  (`phase-2a`:69-152), and the five builder questions (`phase-2b`:27-37). Softened by skipping
  questions already answered, but still a list to get through.
- **GSD.** `discuss-phase/modes/default.md`:47 ("Ask 4 questions" per area, then a "more or next?"
  check); `spec-phase.md`:132-140 (six rounds, each assigned a viewpoint in advance).
- **spec-kit clarify** :73-123 (the ten-category scan run on every spec) and :129-138, :233 (cap of
  five; answers forced into a choice or five words). The five-word limit will cut off exactly the
  answers that carry intent.
- **`idea-refine`**: "Ask 3-5 sharpening questions — no more", "Generate 5-8 idea variations".
  **`doc-coauthoring`** :92, :156: "5-10 numbered questions" per stage. **pm-skills**: three.
- **Superpowers** word targets ("about 200 words", "about 200-300 words"; SKILL.md:57, 194).
  Compound Engineering's own testing found that numeric length caps did not control output and
  that the real fix was a rule about what belongs in the message.
- **mattpocock `to-spec`** :33, :41: "A LONG, numbered list of user stories ... extremely
  extensive". The project's own docs page admits this produces "stories nobody asked for".

## Rigid sequences and ceremony

- **`feature-dev`**: seven phases in fixed order with a to-do list for all of them, whatever the
  size of the feature (:16, :27).
- **spec-kit**: numbered execution steps written like a program, including "ERROR" outcomes
  (`specify.md`:121-144), a self-graded checklist with up to three repair loops (:148-238), and a
  repeated block of hook-handling instructions at the top and bottom of every command.
- **Compound Engineering**: a table of phases each with files that must be read first
  (`SKILL.md`:50-59), a five-item task list shown to the person, and about twenty reference files.
  It uses conditions more than capitals, and its rules are well argued, but the weight is itself
  a cost: the project's own write-up says a strong model already reasons past much of this.
- **GSD spec-phase** `ambiguity_model` (:8-20): four scores to two decimal places, weights, and a
  0.20 gate, shown to the person after every round. This is invented precision; the model is
  producing the numbers it is then gated on. The same applies, more lightly, to `interview-me`'s
  confidence percentages (:40-51), though its "can I predict the next three reactions" test is a
  better form of the same idea.
- **BMAD forge-idea**: two characters voiced on every turn, and a mandatory HTML report with a
  "wax-seal-style" stamp (:94-100, :110). Performance around the conversation, not part of it.
- **mattpocock grilling** fixed emoji layout (:12-22). Minor; it exists so a person can answer by
  number.
- **gstack office-hours** required approach slots: "One must be the "minimal viable"", "One must
  be the "ideal architecture"" (tmpl:264-265), and "The assignment is mandatory" (:374). Forced
  slots produce filler options when the real choice is elsewhere.

## Reminders to do what a capable model does anyway

- **Karpathy guidelines**, all four principles. The instruction to ask when uncertain has no
  filter, and the example for "export user data" asks things the repository or a default could
  settle ("How many users typically?"). With a current model this is likelier to cause
  unnecessary questions than to prevent a wrong assumption. The README itself says the guidelines
  "bias toward caution over speed".
- **`interview-me`** "Common Rationalizations" table and "Red Flags" list (two lists that restate
  the process), and **superpowers** "Red Flags" table (SKILL.md:285-294). Superpowers has
  evidence that such tables work as reminders at the moment of decision, and several of its six
  rows record real failures (the "sounds good" row, the spike row). The `interview-me` tables are
  longer and partly generic ("I'll figure it out as I build").
- **OpenSpec explore** "What You Don't Have To Do" (:201-208) and the instruction to draw ASCII
  diagrams "liberally" (:37, :93), which invites decoration.
- **gstack** banned-phrase list (`phase-2a`:27-33) and the five worked "BAD / GOOD" exchanges
  (:38-65). Superpowers' phrasing evidence suggests a ban on wording inside generated text tends
  to do worse than describing what the text should contain.

## Rules that override the person

- **gstack office-hours** escape hatch (`phase-2a`:156-161): when the person says to skip the
  questions, the agent is told to reply that "the hard questions are the value" and ask two more.
  A full skip is allowed only if the person shows users or revenue.
- **GSD discuss** `discuss-phase.md`:340: "Do NOT include a "skip" or "you decide" option" when
  choosing areas (the per-question options do allow "You decide").
- **mattpocock** "relentlessly", combined with no cap and a model that follows instructions
  faithfully, is the likely cause of the 200-question report.

## Workarounds for host tools, not for models

These are dated by tooling, and worth keeping out of a skill meant for both Claude Code and Codex:
GSD's rules for empty question-tool responses and its twelve-character header limit
(`questioning.md`:82, `discuss-phase.md` answer_validation); gstack's alternate question formats
for when the tool is missing; mattpocock's "Call the Skill tool with ..." phrasing, adopted
because naming another skill in prose did not reliably load it.

## What does not look dated

For balance: superpowers v7.0.2 `brainstorming`, mattpocock `grilling`, OpenSpec explore's
"Planning a Change" section, BMAD facilitate's Facilitation section, and Compound Engineering's
`interaction-rules.md` and `settled-decisions.md` are mostly written as reasons and conditions
rather than commands, and the first two are short.

---

# Part 5. What none of them covers (my judgement)

All of this part is judgement. "None" means I did not find it in what I read; where one library
comes close I say so.

1. **How the finished thing will be checked, and by whom.** Several ask what success looks like.
   None asks which checks a machine can run and which need the person (taste, a login only they
   hold, hardware only they have), or agrees up front what evidence the person will accept as
   done. Karpathy's fourth principle and spec-kit's "measurable" success criteria are the
   nearest. A planner that must write checkable completion conditions gets little from any of
   these documents.

2. **What the agent is allowed to touch, spend and reach.** Accounts, credentials, paid services,
   deployment targets, data that must not leave the machine, a budget. Only gstack's premise
   check (how will users get the thing) and mattpocock's "task" tickets for access touch this.
   For a long unattended build this is the most likely source of a mid-build stop.

3. **How the person wants to be involved during the build.** Superpowers asks which technical
   choices they want to own. Nobody asks which later decisions the agent may take alone, when the
   person wants to be interrupted, or how they want to hear about progress.

4. **A person who is not there, or answers hours later.** BMAD facilitate has a no-person mode;
   `interview-me` says to flag a blocker; Compound Engineering says the skill should not be used
   without a live person. None covers a conversation that proceeds in slow turns, or says which
   work can continue while a question is open (mattpocock does this for facts being looked up,
   not for the person's pending answers).

5. **The person's own words, kept verbatim.** Several keep "what they said" apart from "what the
   agent inferred", and BMAD says to keep the person's words for their claims. None stores the
   original request word for word in the output. Mattpocock's docs name the consequence as their
   most serious open complaint: precise answers get softened by each later step. A numbered list
   of decisions that later documents must cite (BMAD's stable ids, Compound Engineering's
   provenance labels, GSD's decision ids) is the partial answer three libraries have reached
   separately.

6. **Telling apart "I don't know", "I don't care" and "you decide".** `interview-me` handles
   "whatever you think" (treat as delegation, offer two options). Compound Engineering notices
   when two answers in a row show the person cannot evaluate the question, and offers to explain
   the territory. No library gives one rule covering all three, and none says what to record in
   each case (an open question, a default the agent may change freely, or a decision the person
   delegated).

7. **The person who agrees with everything.** Mattpocock names it as the main failure and leaves
   the fix to the person. `interview-me` suggests an occasional deliberately contestable guess.
   Nobody has a test for it, and the recommended-answer format that most libraries share makes
   it more likely.

8. **Ordering questions by what a wrong guess would cost.** The shared filter is "would the answer
   change what gets built". None adds the second half as a general rule: ask about what is
   expensive to undo, decide and state what is cheap to undo. The pieces exist in special cases:
   Compound Engineering's "expensive to unravel" test for when to prototype, and mattpocock's
   three conditions for writing a decision record.

9. **What must not change.** For work in an existing project, only gstack's `spec` template has a
   "Do Not Touch" section. No conversation asks what the person relies on today that the build
   must leave alone.

10. **A change of mind after the conversation ends.** Superpowers says to step up a size if work
    grows; BMAD has an update path that surfaces conflicts with earlier decisions; OpenSpec lets
    exploration resume mid-build. None says how a later change in what the person wants is
    recorded against the approved document so that planning and review see both.

11. **Other people.** Every skill assumes the person talking is the one who decides and the one
    who will use the result. BMAD asks who will act on the document; mattpocock has a separate
    skill for writing a questionnaire to someone else. None asks who else must agree, or who the
    real user is when it is not the person in the conversation.

12. **Not asking the same thing twice across the handoff.** If planning also asks questions, the
    person is interviewed twice. Only Compound Engineering has a mechanism (decisions marked as
    settled, which the planning skill must not reopen) and superpowers a softer one (the design
    lists what is left to the builder). Mattpocock relies on keeping the same conversation open.

13. **Evidence that the conversation improved what was built.** Every test I found grades the
    conversation itself: filler questions, whether the reason came out, whether anything was built
    early, the length of the confirmation. None measures whether the build that followed was
    closer to what the person wanted. gstack's removal of a planning-review skill after an
    outcome test is the only example of that kind of measurement, and it went against the skill.

14. **How long the conversation may run before it degrades.** Mattpocock's docs mention the
    context filling up and questions getting worse, and size each decision to one session. No
    skill tells the agent to notice this itself and move what has been settled into a file
    before continuing. BMAD and GSD write a running log, for resuming after interruption rather
    than for this.

---

# Not read, and limits

- Not opened: superpowers `visual-companion.md` and the external test repository; mattpocock
  `triage`, `to-tickets`, `to-questionnaire`; BMAD `bmad-brainstorming`,
  `bmad-advanced-elicitation`, the analyst, product-owner, UX and architecture skills; Compound
  Engineering `ce-ideate`, `ce-plan`, `ce-prototype` and eleven of `ce-brainstorm`'s reference
  files; gstack `plan-ceo-review`, `autoplan` and the shared question-format preamble; spec-kit
  `plan`, `checklist` and most of the `assess` extension; the rest of pm-skills and wshobson
  beyond the files named.
- BMAD `bmad-facilitate/SKILL.md` and several Compound Engineering reference files have very long
  lines; I read each line's first several hundred characters, so a rule stated late in a long
  line may be missing here. For that reason some BMAD and Compound Engineering quotes cite a
  section rather than a line number.
- `git log` in a shallow clone shows one commit. History here comes from changelogs, release
  notes, docs pages, one issue (obra/superpowers #2530), two superpowers pull-request
  descriptions (#2644 in full, #2571 not retrieved), two spec-kit pull requests (#3745, #4507),
  and two mattpocock issues (#44, #706). Numbers quoted from release notes and pull requests are
  the maintainers' own; I did not rerun any test.
- gsd-build/get-shit-done is archived. I compared its `questioning.md` and `discuss-phase.md`
  with the successor's and found the first identical and the second changed only in plumbing, so
  the description in Part 1 holds for both. I did not read the successor's changelog.
