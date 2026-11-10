# Library survey: how public skill libraries agree a shared set of project terms and keep to it

Survey date: 10 November 2026. Written for the design of a skill that gets an AI coding agent and the person it works for to agree a set of terms for a software project (a glossary), and then keeps later agents and files using those terms.

## How to read these notes

- **What a file says** and **what I think about it** are kept apart. Paragraphs and table cells marked **[file]** report what is in a file I read. Paragraphs marked **[judgement]** are my own reading. Sections 5 and 6 are judgement throughout, with the lines they rest on cited.
- `libs/` means `/private/tmp/claude-501/-Users-ryannel--claude-spares-spare-9ZHcrE/101c62dd-273c-4dbb-b8ea-4ac2a6b47ab8/scratchpad/libs/`. Every path below is under it unless it starts with `https://`.
- Quotes are short on purpose (under 15 words each) and carry the file and line, so the full wording can be read in place. Where a rule is longer than that, I quote its key clause and paraphrase the rest.
- "The person" means the human the agent works for. "The glossary" means whatever file a library uses to hold agreed terms, whatever it is called there.
- Nothing from the libraries was run. History (changelogs, pull requests, issues) came from `gh api`, because each clone holds one commit.

## Contents

1. What was read, and the verdict on each library
2. What each relevant library makes the agent do
3. The published methods the skills lean on (Evans, EventStorming)
4. Evidence the libraries give for their rules
5. Where the sources agree and disagree
6. What looks written for earlier, weaker models
7. What none of them covers that this job seems to need

---

## 1. What was read, and the verdict on each library

### The fourteen libraries supplied

| Library (folder under `libs/`) | Licence | Commit read | Verdict |
|---|---|---|---|
| mattpocock/skills (`mattpocock_skills`) | MIT | `4ae2317ddb` (2026-10-31) | **Most relevant.** A full glossary discipline: `domain-modeling`, `grilling`, `grill-with-docs`, a per-repo pointer file, and one-line "use the glossary" rules in about ten other skills. Checked fully. |
| EveryInc/compound-engineering-plugin (`EveryInc_compound-engineering-plugin`) | MIT | `dd9b7921c9` (2026-11-09) | **Highly relevant.** `CONCEPTS.md` glossary with rules for adding, merging and retiring entries, written by several skills as a side effect. |
| github/spec-kit (`github_spec-kit`) | MIT | `142089067d` (2026-11-10) | Partly relevant. Terms are one category in the `clarify` question pass and one check in `analyze`. No glossary file. The "constitution" holds principles, not terms. |
| bmad-code-org/BMAD-METHOD (`bmad-code-org_BMAD-METHOD`) | MIT | `a867e1604b` (2026-11-07) | Partly relevant. A Glossary section in the requirements template, a `glossary.md` file beside a ticket, and "no invented terms" rules. No process for agreeing terms. |
| garrytan/gstack (`garrytan_gstack`) | MIT | `dbb4b5064c` (2026-11-10) | Narrowly relevant. A script-checked list of banned terms, run during review. No glossary process. |
| obra/superpowers (`obra_superpowers`) | MIT | `22f0b463e7` (2026-11-03) | **No glossary skill.** Side effects only: match the person's vocabulary in the interview, and carry naming rules word for word from the design into the plan. Checked fully (all fifteen skills grepped, `brainstorming` and `writing-plans` read). |
| wshobson/agents (`wshobson_agents`) | MIT | `9c61ab243d` (2026-11-08) | Slightly relevant. A "Term / Use / Don't Use" table in one template. Domain-driven design appears as description only. |
| gsd-build/get-shit-done (`gsd-build_get-shit-done`) | MIT | `bdcaab2c75` (2026-05-31) | **Nothing in what it ships to users.** Its own repository uses the mattpocock convention on itself, and is a useful example of that convention going wrong. |
| Fission-AI/OpenSpec (`Fission-AI_OpenSpec`) | MIT | `579fcac57a` (2026-11-09) | **Nothing in what it ships to users.** Its own repository has a test that keeps a retired term out of the code and docs. |
| addyosmani/agent-skills (`addyosmani_agent-skills`) | MIT | `301b02b12b` (2026-11-01) | **No glossary skill.** Two side mentions. |
| multica-ai/andrej-karpathy-skills (`multica-ai_andrej-karpathy-skills`) | MIT (stated in `README.md:169-171`; no licence file) | `2c60614193` (2026-04-20) | **Nothing.** Checked fully: one 65-line guideline file in three copies. |
| anthropics/skills (`anthropics_skills`) | Apache-2.0 per skill (`skills/*/LICENSE.txt`); no licence file at the root | `2c5958ecac` (2026-11-06) | **Nothing on project terms.** Its guidance on prompts written for older models is used in section 6. |
| anthropics/claude-plugins-official (`anthropics_claude-plugins-official`) | Apache-2.0 | `dceb15d508` (2026-11-09) | **Nothing.** It lists the mattpocock plugin in its marketplace (`.claude-plugin/marketplace.json:2352`) and has generic "consistent terminology" advice for writing commands. |
| phuryn/pm-skills (`phuryn_pm-skills`) | MIT | `9af7bfd0bc` (2026-11-08) | **Nothing.** Only "avoid jargon" and "define terms when first used" lines in document-writing skills. |

### Found by searching GitHub, and cloned

`gh search code` for "ubiquitous language" in `SKILL.md` files, and `gh search repos` for ubiquitous language, glossary, domain-driven design and event storming. Stars are from `gh api` on the survey date.

| Repository (folder under `libs/`) | Stars | Licence | Commit read | Why it was read |
|---|---|---|---|---|
| CodeAlive-AI/ai-driven-development (`extra_CodeAlive-AI_ai-driven-development`) | 169 | MIT | `d2c1745186` (2026-11-09) | **The most detailed glossary skill found anywhere.** A "thesaurus" consulted before anything is named. |
| citypaul/.dotfiles (`extra_citypaul_.dotfiles`) | 760 | MIT at the root, with nested notices | `cd4028d57d` (2026-10-02) | A five-step protocol for every new term, with the person deciding each one. |
| ciembor/agent-rules-books (`extra_ciembor_agent-rules-books`) | 3,244 | MIT | `893a88a6fc` (2026-09-10) | Rules distilled from Evans's book. No conversation, no file. |
| evanklem/evanflow (`extra_evanklem_evanflow`) | 419 | MIT | `c9ae21f8ed` (2026-05-12) | A reworked copy of the old mattpocock skill that writes `CONTEXT.md`. |
| danielvm-git/bigpowers (`extra_danielvm-git_bigpowers`) | 288 | MIT | `72f5e4c8b4` (2026-11-09) | A near copy of the old mattpocock skill with a "HARD GATE" added. |
| softspark/ai-toolkit (`extra_softspark_ai-toolkit`) | 179 | Apache-2.0 | `e181059fb6` (2026-11-06) | A near copy of the old mattpocock skill. Nothing new. |
| pedronauck/skills (`extra_pedronauck_skills`) | 652 | none | `682e7388ba` (2026-11-02) | `ddd-master`: says what an agent can and cannot do in event storming. |
| techygarg/lattice (`extra_techygarg_lattice`) | 211 | MIT | `a772470df2` (2026-10-24) | A glossary is an optional extra section. Nothing more. |
| NeoLabHQ/context-engineering-kit (`extra_NeoLabHQ_context-engineering-kit`) | 1,815 | GPL-3.0 | `23e2428e80` (2026-08-26) | Only checklist lines such as "naming follows ubiquitous language". Nothing more. |
| dev-cycles/contextive (`extra_dev-cycles_contextive`) | 369 | MIT | `382d6d071a` (2026-04-16) | Not a skill. An editor tool with a mature glossary file format, which the citypaul skill borrows. |
| PakhomovAlexander/project-hub (`extra_PakhomovAlexander_project-hub`) | 19 | MIT | `99d8c72bdf` (2026-08-24) | Low use, but shows one way to force every session to load the glossary. |
| mattpocock/skills, removed file (`extra_mattpocock_skills_history/`) | — | MIT | parent of `c66bdeeee0` | The removed `ubiquitous-language` skill, fetched with `gh api`. |

**[file]** The removed mattpocock `ubiquitous-language` skill is the most copied design. Code search for a `SKILL.md` in a folder named `ubiquitous-language` returned 30 results, the page limit. Six sit in folders named after mattpocock (in `mkurman/zorai`, `stevesolun/ctx`, `FradSer/dotclaude`, `Miosa-osa/canopy`, `jtenner/starshine-mb`, `yogeshhk/TeachingDataScience`). Two more that I compared line by line, `softspark/ai-toolkit` and `danielvm-git/bigpowers`, are near copies. I did not open the rest.

**[judgement]** "Well-used" is thin here. Outside mattpocock/skills (about 320,000 stars) and compound-engineering, nothing that is specifically a glossary skill has more than a few hundred stars. Treat the search finds as a source of ideas, not of proven practice.

---

## 2. What each relevant library makes the agent do

### 2.1 mattpocock/skills

Files read:

- `mattpocock_skills/skills/engineering/domain-modeling/SKILL.md` (74 lines), `GLOSSARY-FORMAT.md` (60 lines), `ADR-FORMAT.md`
- `mattpocock_skills/skills/productivity/grilling/SKILL.md` (30 lines), the interview that drives it
- `mattpocock_skills/skills/engineering/grill-with-docs/SKILL.md` (one body line: call the two skills above)
- `mattpocock_skills/skills/engineering/setup-matt-pocock-skills/SKILL.md` and its template `domain.md` (51 lines), which becomes `docs/agents/domain.md` in the person's repository
- `mattpocock_skills/docs/engineering/domain-modeling.md` and `docs/engineering/grill-with-docs.md`, the author's own account of how the skills behave in use
- `mattpocock_skills/GLOSSARY.md`, the repository's own glossary
- `mattpocock_skills/CHANGELOG.md`
- `extra_mattpocock_skills_history/ubiquitous-language_SKILL_at_c66bdeeee0-parent.md`, the removed earlier skill

The design has two halves. One skill **changes** the glossary (`domain-modeling`). Every other skill only **reads** it, through a single line of prose. The author states the split in `domain-modeling/SKILL.md:8`: reading the file "is not this skill: that's a one-line habit any skill can do".

| Question | What the files say **[file]** |
|---|---|
| When work on terms starts | During a design interview, before any specification is written. `grill-with-docs` is "the head of the main build chain" (`docs/engineering/grill-with-docs.md:76-80`). It also starts mid-work whenever another skill settles a name: `improve-codebase-architecture/SKILL.md:66-69`, `triage/SKILL.md:76`, `wayfinder/SKILL.md:79,111`. Nothing is set up in advance: "Create files lazily: only when you have something to write." (`domain-modeling/SKILL.md:40`). |
| Where candidate terms come from | The person's words in the interview, checked against the existing glossary and against the code. The code is read to answer questions of fact; the person is asked which word is right. For a repository with no glossary the documented route is an explicit request, and "One user reported more than 50 questions" (`docs/engineering/domain-modeling.md:64`). |
| Two words for one thing | The agent picks one and records the rest on the entry: "pick the best one and list the others under `_Avoid_`" (`GLOSSARY-FORMAT.md:27`). |
| One word for two things | The agent stops and asks. The model sentence is "You're saying 'account': do you mean the Customer or the User?" (`domain-modeling/SKILL.md:50`). |
| The person's word conflicts with the glossary | "call it out immediately" (`domain-modeling/SKILL.md:46`), with the model sentence "Your glossary defines 'cancellation' as X, but you seem to mean Y. Which is it?" |
| The code disagrees with what the person says | "check whether the code agrees" and surface the contradiction (`domain-modeling/SKILL.md:58`). The docs page adds that the skill makes language and code agree "out loud, before it changes either" (`docs/engineering/domain-modeling.md:48`). There is no rule for a term the code already uses with a different meaning beyond asking "Which is right?". |
| How the person is asked | In rounds. Each round holds every question that does not depend on an unanswered one. The agent must "number each question and give your recommended answer" (`grilling/SKILL.md:8`) and "Word each question so "yes" accepts your recommended answer." (`grilling/SKILL.md:24`). Facts are the agent's to look up: "Finding _facts_ is your job, never the user's." Decisions are the person's (`grilling/SKILL.md:28`). There is no limit on the number of questions; a cap was refused on purpose (`docs/productivity/grilling.md`, "Can I cap the number of questions?"). People who prefer one question at a time add a line to their own `CLAUDE.md`. |
| How the person approves | By answering the question. The entry is then written at once: "Don't batch these up: capture them as they happen." (`domain-modeling/SKILL.md:62`). The interview as a whole ends with a confirmation: "Do not act on it until the user confirms" (`grilling/SKILL.md:30`). There is no separate approval of the written entry. |
| What an entry contains | The term in bold, a definition of one or two sentences, and an `_Avoid_` line of rejected words. Rules: "One or two sentences max. Define what it IS, not what it does." (`GLOSSARY-FORMAT.md:28`) and "Only include terms specific to this project's context." (`GLOSSARY-FORMAT.md:29`). No example sentence, no "what it is not", no name used in code. |
| What must stay out | Implementation detail, decisions, anything that is not a term: "It is a glossary and nothing else." (`domain-modeling/SKILL.md:64`). Decisions that are hard to reverse go to a separate decision record under `docs/adr/`; everything else stays in the conversation (`docs/engineering/grill-with-docs.md:33-39`). |
| File name, format, location | `GLOSSARY.md` at the repository root, Markdown. Until version 1.3.0 it was `CONTEXT.md`. |
| More than one file | Only when the repository shows signs of being a multi-package repository (`setup-matt-pocock-skills/SKILL.md:61-63`). Then a root `GLOSSARY-MAP.md` lists one `GLOSSARY.md` per area and how the areas relate. The agent must "infer which one the current topic relates to. If unclear, ask." (`GLOSSARY-FORMAT.md:60`). |
| How later agents are made to read it | A setup skill writes `docs/agents/domain.md` and adds a pointer to it in `CLAUDE.md` or `AGENTS.md`. That file tells every engineering skill to read the glossary before exploring, and "Don't drift to synonyms the glossary explicitly avoids." (`domain.md:43`). About ten skills also carry their own line, for example `tdd/SKILL.md:10` (test names), `to-tickets/SKILL.md:21` (ticket titles), `pr/SKILL.md:37` (pull request text), `codebase-design/DESIGN-IT-TWICE.md:30` (include glossary terms in the brief for each sub-agent). |
| When a later agent needs a word that is not there | "either you're inventing language the project doesn't use (reconsider) or there's a real gap" (`domain.md:45`); a real gap is noted for the `domain-modeling` skill. |
| When the file is absent | "proceed silently" and "don't suggest creating them upfront" (`domain.md:11`). |
| How it is kept current, and who may change it | The agent edits it inline during any session that runs `domain-modeling`. No review step, no owner, no rule for removing an entry. The docs page lists as a sign of health that the file "gets shorter as often as it gets longer" (`docs/engineering/domain-modeling.md:82`), but no instruction produces that. |
| How names in code relate to it | Code names are meant to follow the glossary (module names, test names, ticket titles), and the glossary must not contain code names. The docs page says synonym control matters most "at naming boundaries: module names, table names, status enums, issue titles, CLI commands" (`docs/engineering/domain-modeling.md:70`). |

Real example entry, from the repository's own glossary (`mattpocock_skills/GLOSSARY.md:7-9`):

```md
**Issue tracker**:
The tool that hosts a repo's issues: GitHub Issues, Linear, a local `.scratch/` markdown convention, or similar. …
_Avoid_: backlog manager, backlog backend, issue host
```

**[file]** The same file keeps two sections the current format template no longer shows: `## Relationships` (lines 21-25) and `## Flagged ambiguities` (lines 27-30), the second recording, for example, that "backlog" had meant both a tool and a body of work.

**The earlier skill, now removed** (`extra_mattpocock_skills_history/…`, 93 lines) **[file]**: a command the person ran by hand at the end of a conversation. It scanned the conversation, proposed a glossary, and wrote `UBIQUITOUS_LANGUAGE.md` in one pass. The file had tables of "Term / Definition / Aliases to avoid", a Relationships list, a required example dialogue between a developer and a domain expert, and a "Flagged ambiguities" section. The changelog says it was replaced because the new skill maintains the model "rather than dumping a glossary from one conversation" (`CHANGELOG.md:240`).

### 2.2 EveryInc/compound-engineering-plugin

Files read:

- `EveryInc_compound-engineering-plugin/skills/ce-compound/references/concepts-vocabulary.md` (114 lines), the rules for the file
- `skills/ce-compound/references/assembly.md:58-78`, `lightweight.md:21`, `grounding-validation.md:37`, `refresh/modes.md:20-25`, `refresh-and-discoverability.md:90-96`, `report.md:23-24`
- `skills/ce-brainstorm/references/dialogue.md:21,71` and `plan-write.md:22-32`
- `skills/ce-plan/references/research.md:35` and `final-review.md:97`
- `skills/ce-code-review/references/personas/learnings-researcher.md:31-35`
- `CONCEPTS.md` at the root (282 lines), the repository's own glossary
- `tests/skills/ce-brainstorm-ask-decisions.test.ts`

Here the glossary is a **side effect**. No skill exists to agree terms. `ce-compound`, the skill that writes up a lesson after a piece of work, also updates `CONCEPTS.md`. The interview skill and the planning skill add to the file if it already exists.

| Question | What the files say **[file]** |
|---|---|
| When work on terms starts | After work, not before it. The file is created the first time a lesson write-up meets a qualifying term (`concepts-vocabulary.md:3`). During the interview the agent only reads the file and raises conflicts; "Glossary writes still wait until after the plan." (`dialogue.md:71`). The stated reason: the final name is often chosen late, so writing during early dialogue "would miss the final resolved name" (`plan-write.md:26`). |
| Where candidate terms come from | Two routes, named in the file. "Accretion": a term comes up because it caused confusion. "Seeding": the agent defines the core nouns of the area from the "declared domain model", meaning the schema, core types, main models and top-level docs, "not a full-codebase trawl" (`concepts-vocabulary.md:20`). The reason for seeding: "the nouns a system is built around rarely break" (`concepts-vocabulary.md:16`), so they never come up through confusion and the file fills with side detail. |
| Two words for one thing | "pick the best one and drop the rest" (`concepts-vocabulary.md:29`). The dropped words go on an `Avoid:` line under the surviving entry. |
| One word for two things | Recorded, once settled, as a one-line note in a "Flagged ambiguities" section at the end of the file, described as "the audit trail for opinions the team has formed" (`concepts-vocabulary.md:73`). |
| The person's word conflicts with the glossary or the code | In the interview, the agent must "put that conflict to them before treating their wording as settled", but only "when it would change a product decision" (`dialogue.md:71`). |
| How the person is asked and how they approve | **They are not asked about glossary writes.** "Apply vocabulary edits silently in every mode — no user prompt." (`concepts-vocabulary.md:114`; same in `assembly.md:78` and `plan-write.md:32`). In place of approval there are two controls. The run's final report must state what changed in the file, or "scanned, no qualifying terms" (`report.md:23`). And in the full mode a separate read-only sub-agent checks each new or edited entry against the source code, because an entry written from a summary is "exactly how wrong semantics enter the glossary" (`assembly.md:64`, `grounding-validation.md:37`). The person can edit the file directly; the file's first line says so. |
| What an entry contains | A heading, a definition of one sentence saying what the term means here and what sets it apart from its neighbours, an optional `Avoid:` line, and an optional second paragraph for rules that are not obvious (life cycle, ownership) (`concepts-vocabulary.md:59-61`). Optional `## Relationships` section. |
| What must stay out | File paths, class names, function signatures, table names, dates, owners, links to pull requests, version claims, and current values: "State the behavior, not the number" (`concepts-vocabulary.md:35-39`). General programming words. The test for the whole file: "Each entry teaches its concept to a reader with no access to anything else" (`concepts-vocabulary.md:33`). |
| What earns an entry | Two tests: precise enough that a new engineer would need it defined, and "a concept in its own right rather than a property of one already defined" (`concepts-vocabulary.md:45`). |
| File name, format, location | `CONCEPTS.md` at the repository root, Markdown headings grouped by subject. One file only; no rule for more. |
| How later agents are made to read it | Each reading skill has a line: `ce-plan/references/research.md:35` ("Plan with those terms rather than synonyms."), `ce-brainstorm/references/dialogue.md:21`, the review researcher at `learnings-researcher.md:31-35`. After any change to the file, the skill checks whether the project's `AGENTS.md` or `CLAUDE.md` would lead an agent to it, and proposes a one-line addition, with the person's consent in the interactive mode (`refresh-and-discoverability.md:90-96`). If the file does not exist: "Never nag for an artifact the project has not adopted." |
| How it is kept current | Six named changes: add, refine, fold (merge into the entry that already carries the meaning), retire (move to a `## Retired` section with what the term meant and what removed it), delete, scrub (remove rule-breaking detail) (`concepts-vocabulary.md:7`). Each run that touches an entry also checks that entry's neighbours, on evidence already in hand (`concepts-vocabulary.md:55`). |
| Who may change it | Split by skill. The interview and planning skills may add and refine, and only if the file exists. `ce-compound` may also fold and scrub, and is the only creator. Only its "refresh" job may retire or delete, because removal needs investigation (`plan-write.md:28`, `assembly.md:62`). Removal needs positive evidence of where the concept went: "uncertainty leaves it standing", and "a deleted class, path, or symbol is never that evidence" (`concepts-vocabulary.md:51`). |
| How names in code relate to it | Kept apart on purpose. Entries must not name code, and are meant to outlive the code that implemented them. Nothing says code names must follow the glossary; plans and reviews must use its terms. |

Real example entry, from the repository's own glossary (`EveryInc_compound-engineering-plugin/CONCEPTS.md:256-257`):

```md
### Offered work
Work the user has put up for review, as distinct from work that merely exists in the tree or on a remote. …
```

### 2.3 CodeAlive-AI/ai-driven-development (found by search)

Files read: `extra_CodeAlive-AI_ai-driven-development/skills/ubiquitous-language/SKILL.md` (591 lines), `references/generating-thesaurus.md` (538 lines, first 330 read closely), and the skill's `README.md`. Not read closely: `references/naming-audit.md`, `references/git-history-mining.md`, and the script.

This skill is aimed at **names in code**. Its description tells the agent to use it "PROACTIVELY when naming anything" (`SKILL.md:5`).

| Question | What the files say **[file]** |
|---|---|
| When work on terms starts | Two moments. Rarely: the person asks for the file to be generated from the code. Often: every time the agent is about to name something, it searches the file first: "Look up before inventing." (`SKILL.md:235`). |
| Where candidate terms come from | The code, not documents: derive the file from the codebase, "not from docs or specs" (`generating-thesaurus.md:8`). The agent reads a few dense files (database schema, API definitions, domain types, directory names) and stops when new scans return known terms. Stated position on authority: "The codebase is primary evidence, not automatic authority." (`SKILL.md:56`); what should become standard is the person's call; once approved, "the thesaurus wins for new code" (`SKILL.md:62`). |
| Two words for one thing | All names for a concept go on one line, the rejected ones after `avoid:`. Searching for a rejected word then lands on the line that gives the right one. |
| One word for two things | Recorded under `## Unresolved` with where it was found, the question, how many files it touches, and options. The agent is told not to assign the two meanings to separate areas itself: "Do NOT pre-assign bounded contexts." (`generating-thesaurus.md:199`). A split into areas is justified only if the person can name one rule that holds in one area and not the other (`generating-thesaurus.md:216-219`). |
| A term the code already uses differently | A `## Legacy` line: old name, arrow, replacement, where the old name still lives. New code uses the replacement. A large rename is noted as debt and the person is asked (`SKILL.md:301-306`). |
| How the person is asked | In one batch after generation: "Don't stop on each ambiguity" (`generating-thesaurus.md:69`); then present the unresolved list with its impact and ask which to settle first. For a new concept the agent first tries to reuse, combine or qualify existing terms, and only then asks: "What does the domain call it?" (`SKILL.md:283-291`). If the person has no answer, the item stays unresolved; the skill calls this "co-creation, not extraction" (`SKILL.md:290`). |
| How the person approves | By settling an unresolved item, which the agent then moves into the index. A generated file opens with a notice, "Reconstructed, not authored.", saying names found in code are evidence and definitions are the agent's reconstruction until a domain expert confirms them (`generating-thesaurus.md:235-239`). Individual entries are not marked as confirmed or unconfirmed. |
| What an entry contains | An index line: the term as people say it, the identifier used in code, a kind (entity, event, command, state, and so on), an optional area, and the words to avoid. Plus an entry with a one-sentence **Definition**, a **NOT** line naming the neighbouring term it is confused with, and **Related** terms. Optional: an example (`SKILL.md:171-216`). |
| File name, format, location | `docs/THESAURUS.md` by default, Markdown, with a format version in its header. Five fixed sections: Index, Terms, Forbidden, Legacy, Unresolved. Lines are written so one text search answers "what do I do with this name?"; tables are avoided because the `|` character interferes with search patterns (`SKILL.md:114-136`). Rule: "every name known to the project appears in **exactly one** registry line" (`SKILL.md:127`). |
| More than one file | No. One file; areas are marked on lines with `ctx:` only after the person confirms them. Suggested size: "Target: 15-40 terms per bounded context." (`generating-thesaurus.md:42`). |
| How later agents are made to read it | After generation the agent must add a section to every agent instruction file it finds (`CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, `.cursorrules`, Copilot's file), with the search commands, so that sessions without the skill still consult the file (`generating-thesaurus.md:162-195`). Stated reason: "the thesaurus is only useful if the agent knows about it". |
| How it is kept current | Six named changes: add, rename, split, merge, retire, deprecate, each with its effect on the file (`SKILL.md:552-571`). The test between rename and split: is it the same concept before and after? "keep at most 1 legacy alias per term" (`SKILL.md:569`). An optional step mines the git history to see which name came first and which is dying, as evidence for the person: "History is evidence, not authority." (`SKILL.md:353`). |
| Who may change it | The agent adds a new term itself before using it in code (`SKILL.md:293-299`). Conflicts and renames wait for the person. |
| How names in code relate to it | Directly. Each term has one identifier; every other spelling (variable, table, URL, constant) is derived from it mechanically and never reworded (`SKILL.md:529-550`). The scope is very wide: the lookup is to run before naming classes, functions, variables, parameters, database columns, files, configuration keys, and commit messages (`SKILL.md:275-279`). |

Real example, from the skill's own layout sample (`SKILL.md:143,149-152`):

```md
- **Order** `Order` kind:aggregate avoid: `Purchase`, `Transaction`, `Buy`

### Order
- **Definition**: A customer's confirmed request to buy one or more products at agreed prices.
- **NOT**: A payment (that's `Payment`), a shipment, or a draft cart (that's `Cart`).
```

### 2.4 citypaul/.dotfiles (found by search)

Files read: `extra_citypaul_.dotfiles/claude/.claude/skills/ubiquitous-language/SKILL.md` (92 lines), `resources/language-protocol.md` (68 lines), `resources/glossary-format.md` (66 lines).

This skill is about **who decides**. Its centre is a five-step protocol run for every new or doubtful term: detect, propose, decide, record, rename.

| Question | What the files say **[file]** |
|---|---|
| When work on terms starts | Whenever the agent needs a term the glossary lacks, spots two names for one concept or one name doing two jobs, hears a term that sits awkwardly, or a lint rule flags an unknown word (`language-protocol.md:7-12`). Not as an up-front exercise: "never a big up-front vocabulary exercise" (`glossary-format.md:54`). |
| Where candidate terms come from | The conversation, plans, research notes, and for existing code the exported names, event names, database tables and tests. All of these are candidates only: "Existing code is evidence, not automatic authority." (`glossary-format.md:58`). A word missing from the glossary is neither approved nor banned: "Absence from the glossary means **not yet agreed**." (`SKILL.md:26`). |
| How the person is asked | One term at a time. The agent stops and presents: the term, a proposed definition, which area it belongs to, an example sentence, and the alternatives it considered, with a recommendation (`language-protocol.md:16-24`). |
| How the person approves | They approve, pick a different word, or reject the concept. "An agent never coins a domain term silently." (`SKILL.md:35`). A name in use before approval must be "visibly provisional" (`SKILL.md:28`). |
| What is recorded | The glossary entry, in the same reviewable change as the code that first uses the word. A replaced or rejected word is kept as an alias that names the right term. A rename that changes meaning also gets a decision record; the test is "did the *meaning* move, or just the spelling?" (`language-protocol.md:34`). |
| File name, format, location | Whatever the repository already uses. If it has nothing, the skill suggests the Contextive format: `<area>.glossary.yml` beside the code, with name, definition, example sentences and aliases per term (`glossary-format.md:7-31`). |
| More than one file | Yes, one per area ("bounded context"). Rejected words are scoped to their area: "never flatten every context into one global banned-word list" (`glossary-format.md:48`). |
| How later agents are kept to it | By machine where possible: lint rules generated from the glossary that check identifiers and test titles, each message saying what fired, why, and what to use (`SKILL.md:40-51`). The skill separates the two kinds of control: "Prompt-level glossaries steer; deterministic gates enforce." (`SKILL.md:10`). Until a check is installed the agent must say so and "never imply protection that isn't there" (`SKILL.md:53`). Each check needs a test that feeds it a known banned word and proves it fails. |
| How names in code relate to it | Rename inside an area freely, decision first, then code, tests, schemas, docs together. Names that other systems consume (APIs, events, database contracts) are versioned, "never a casual rename" (`language-protocol.md:56`). For old code, enforce one area first and widen as work touches more; a rule that fires thousands of times on day one "will be bypassed" (`SKILL.md:60`). |

Example, from the skill's worked case (`language-protocol.md:62-68`), paraphrased: a checkout a customer walks away from needs a verb; `cancelOrder` already means the merchant cancelling; the agent proposes `abandonCheckout` with a definition, an example sentence and two rejected alternatives; the person approves; the glossary gains the entry in the same change as the code.

### 2.5 github/spec-kit

Files read: `github_spec-kit/templates/commands/clarify.md` (lines 60-240), `templates/commands/analyze.md` (lines 60, 125-160), `templates/spec-template.md:101-104`, `templates/constitution-template.md`, `templates/commands/constitution.md:89-144`, `templates/commands/plan.md:141-159`.

**[file]** There is no glossary file. Terms appear in three places:

- **`clarify`**, run after the specification is written and before planning. It scans the specification against a fixed list of categories. One category is "Terminology & Consistency", with two items: "Canonical glossary terms" and "Avoided synonyms / deprecated terms" (`clarify.md:113-115`). Gaps become questions. Rules for asking: "Present EXACTLY ONE question at a time." (`clarify.md:141`), "Maximum of 5 total questions across the whole session." (`clarify.md:130`), each answerable by picking from two to five options or in five words, each with a recommended option and a one-sentence "Why it matters", and "yes" accepts the recommendation (`clarify.md:131-171`).
- **Recording the answer.** Each answer is appended under `## Clarifications` in the specification as a question-and-answer line, and then applied to the body. For a term conflict: "Normalize term across spec", keeping the old word once as `(formerly referred to as "X")` only if needed (`clarify.md:194`). The file is saved after every answer. A closing check requires the "same canonical term used across all updated sections" (`clarify.md:206`).
- **`analyze`**, run after tasks are written. It reads the specification, plan and task list together and reports "Terminology drift (same concept named differently across files)" at medium severity (`analyze.md:148,159`). It writes nothing.

The specification template has a "Key Entities" list: what each entity represents and its "key attributes without implementation" (`spec-template.md:101-104`). The planning command turns these into `data-model.md` (`plan.md:141-142`).

**[file]** The "constitution" (`.specify/memory/constitution.md`) holds project principles such as "test first", with a version number and an amendment procedure (`constitution-template.md`, `constitution.md:99-114`). It contains no terms. It is relevant only as an example of a file later commands are forced to load and treat as binding (`analyze.md:60`).

**[judgement]** What spec-kit has that the glossary skills lack: terms are settled per feature inside the document that feature is built from, and a later read-only pass looks for the same concept under different names across three files.

### 2.6 bmad-code-org/BMAD-METHOD

Files read: `bmad-code-org_BMAD-METHOD/skills/bmad-agent-pm/assets/template-prd.md:7,23,43-44`, `skills/bmad-agent-po/references/ticket.md:14`, `skills/bmad-agent-po/references/spec.md:43-48`, `skills/bmad-agent-po/workflow.md:78-99`, `skills/bmad-ux/references/validate.md:35`, `skills/bmad-deep-recon/types/domain.md:10`, `docs/customize/customize-bmad.md:150`.

**[file]**

- The requirements document template has a `## Glossary` section, taken fourth in the interview order, after vision and user journeys and before features (`template-prd.md:7`). Its instruction: each domain noun defined once, with its relationships and how many of each there can be; "A new noun in Features joins the glossary in the same pass." (`template-prd.md:44`). The writing rule for the whole document: "Domain nouns are used exactly as the glossary defines them." (`template-prd.md:23`).
- Tickets must be written "in the project's vocabulary, no invented terms", and the agent offers the person a rewrite where their own text breaks this (`ticket.md:14`).
- A `glossary.md` file can sit beside a ticket as a "companion" that later steps read (`workflow.md:87`, `spec.md:43-48`). Companions written by an earlier skill are listed and never edited by the ticket skill.
- A consistency check in the design skill: "Glossary identical across spines, ticket, and sources." (`validate.md:35`).
- Research into a new field must produce a glossary: "build the glossary — it's why domain research exists" (`domain.md:10`).
- A team can make every agent load its own glossary through a configuration line (`customize-bmad.md:150`).

**[judgement]** BMAD treats the glossary as a section of a document and a file passed forward, and puts effort into keeping copies identical. It has no rules for a synonym, a word with two meanings, or a clash with code.

### 2.7 garrytan/gstack

Files read (not run): `garrytan_gstack/bin/gstack-banned-terms` (header, lines 1-35), `lib/banned-terms.ts:36-45`, `review/SKILL.md.tmpl:164-166`, `document-release/SKILL.md.tmpl:115-118`, `docs/troubleshooting.md:4865-4882`, `test/fixtures/multi-agent-wave/INCIDENTS.md:53`, `scripts/resolvers/preamble/generate-writing-style.ts:18-34`.

**[file]** A repository can keep `.gstack/banned-terms.json`: a list of terms, each with the paths where it is still allowed and a reason. A script checks only the lines a branch adds, and the review skill and the documentation-update skill both run it and treat each hit as a finding (`review/SKILL.md.tmpl:166`). By default the list is read from the copy committed on the base branch, not from the branch under review (`bin/gstack-banned-terms:26-28`). The sample file the script writes (`lib/banned-terms.ts:39-43`):

```json
{ "term": "legacy-name", "allowed_paths": ["CHANGELOG.md", "docs/migration/**"],
  "reason": "the product was renamed; the old name belongs to history only" }
```

**[file]** Separately, every gstack skill is told to explain a listed jargon word the first time it uses one in a session, even if the person used the word first (`generate-writing-style.ts:27`). The list is gstack's own, not the project's.

### 2.8 obra/superpowers

Files read: `obra_superpowers/skills/brainstorming/SKILL.md` (316 lines, all), `skills/writing-plans/SKILL.md:55-110,165-175`, `skills/subagent-driven-development/task-reviewer-prompt.md:25,196`, `skills/writing-skills/references/anthropic-best-practices.md:580-596`, `AGENTS.md:114`, `RELEASE-NOTES.md:360-376`.

**[file]** No skill, file or step deals with a project glossary. Three things touch terms:

- In the design interview: "Match their vocabulary; never use process jargon." (`brainstorming/SKILL.md:107`). Ask open questions first because "Their own words carry intent that your options can't." (`brainstorming/SKILL.md:115`). When playing back what was understood: "Only what they said goes in as theirs." Anything the agent filled in is marked as its own proposal (`brainstorming/SKILL.md:198-199`).
- In the plan: a "Global Constraints" block lists the design's project-wide rules, "naming and copy rules" among them, "with exact values copied verbatim from the spec" (`writing-plans/SKILL.md:72-75`). Each task has an "Interfaces" block giving the exact names it uses and produces, because the agent building one task sees only that task (`writing-plans/SKILL.md:102-106`). A self-check looks for a name spelled two ways in two tasks (`writing-plans/SKILL.md:171`). The reviewer of each task is handed the same constraints (`task-reviewer-prompt.md:25`).
- The project's own contributor rules say its wording is deliberate: "your human partner" is "not interchangeable with "the user"" (`AGENTS.md:114`).

**[judgement]** Superpowers keeps the person's words by carrying them forward unchanged through design, plan and review, with no separate file of terms. That is the mechanism to borrow from it: names reach an agent with a narrow view only if the brief it reads contains them.

### 2.9 wshobson/agents

Files read: `wshobson_agents/plugins/conductor/skills/context-driven-development/references/artifact-templates.md:132-153` and `details.md:45-60`, `plugins/backend-development/skills/architecture-patterns/SKILL.md:52-64`.

**[file]** The "conductor" plugin's project setup writes a `product-guidelines.md` file about how the product speaks to its users. Its template has a terminology table (`artifact-templates.md:143-148`):

```md
| Term | Use | Don't Use |
| workspace | preferred | project, repo |
```

It is to be updated when "New terminology is introduced" (`details.md:60`). The architecture skill states the domain-driven design rule in one line: "Every term in code matches the term used by domain experts" (`architecture-patterns/SKILL.md:60`). Nothing says how terms are agreed.

### 2.10 gsd-build/get-shit-done

Files read: `gsd-build_get-shit-done/docs/agents/domain.md` (32 lines), `CONTEXT.md` (615 lines; lines 1-80 and 286-296 read), `get-shit-done/templates/project.md:13,77`.

**[file]** What it ships to users has no glossary step. The project description template says "Use the user's words and framing" (`templates/project.md:77`). In its shipped workflows a file called `CONTEXT.md` is something else: the decisions from a discussion about one phase.

**[file]** The repository's own development uses the mattpocock convention, and shows what happens to it. `docs/agents/domain.md:9` describes the root `CONTEXT.md` as "domain glossary + recurring PR rules + workflow learnings". The glossary entries name source files and function signatures, and one entry runs to several hundred words (`CONTEXT.md:11-12`). The file also records a lesson about passing rules to other agents: agent prompts must quote the rule's own line, because "paraphrasing from predicate memory drifts and produces violations" (`CONTEXT.md:293`), with the incident beside it (`CONTEXT.md:294`).

**[judgement]** This is the exact failure the mattpocock and compound-engineering rules exist to prevent: a glossary that became a store for everything.

### 2.11 Fission-AI/OpenSpec

Files read: `Fission-AI_OpenSpec/test/vocabulary-sweep.test.ts`, `openspec/work/simplify-context-and-workspace-model/roadmap.md:48-62,455-478`, `docs/glossary.md` (the product's own glossary for its users).

**[file]** Nothing it ships sets up terms for a user's project. Its own repository renamed a concept ("context store" became "store") and guards the rename with a test that fails if the old words appear in source, tests, docs or scripts. Planning history is left out of the check on purpose (`vocabulary-sweep.test.ts:6-11`). The roadmap records the decision with a date, the rejected alternative and the reason: the runner-up noun was dropped "because agents already hear that as the code checkout being operated on" (`roadmap.md:459-470`). The roadmap also opens with a "Vocabulary For This Roadmap" list (`roadmap.md:48`).

### 2.12 addyosmani/agent-skills

Files read: `addyosmani_agent-skills/skills/interview-me/SKILL.md:86-104`, `skills/documentation-and-adrs/SKILL.md:263-266`, `skills/spec-driven-development/SKILL.md:106-111`.

**[file]** No glossary. The interview skill ends by restating what the person wants, in a few lines they can correct one by one, and says to "use their language where possible" (`interview-me/SKILL.md:96`). The documentation skill says an edit must keep "the project's established terminology" (`documentation-and-adrs/SKILL.md:265`).

### 2.13 Smaller finds from the search

- **ciembor/agent-rules-books** (`extra_ciembor_agent-rules-books/domain-driven-design/domain-driven-design.md:144-163`, `domain-driven-design.mini.md`) **[file]**: rules restating Evans. "One concept must have one name inside a bounded context." One name must not carry two meanings. Method names, test names and modules use the domain's words. "Rename code when the domain understanding improves." Listed as a mistake: "Keeping bad names because they already exist in the database". No conversation and no file.
- **evanklem/evanflow** (`extra_evanklem_evanflow/skills/evanflow-glossary/SKILL.md`, 93 lines) **[file]**: the old mattpocock table format in `CONTEXT.md`, with three additions. It reads the code first, because "Names in code are the *de facto* terminology." (line 25). It collects verbs and status values as well as nouns (lines 32-35). For each conflict it must "Propose recommended answers. Don't just dump the conflicts on the user." (line 44). It also says "Never auto-commit." (line 88). Seven other skills in the set end with "new domain term emerged → update `CONTEXT.md`".
- **danielvm-git/bigpowers** (`extra_danielvm-git_bigpowers/skills/define-language/SKILL.md`) **[file]**: the old mattpocock skill almost word for word, writing `specs/UBIQUITOUS_LANGUAGE_LATEST.md`, plus one added line (line 14) discussed in section 6.
- **pedronauck/skills** (`extra_pedronauck_skills/skills/mine/ddd-master/references/strategic.md:17-25`, `discovery.md:42-50`; no licence, so quoted minimally) **[file]**: gives a test for when terms are settled for an area: a short glossary exists, a domain expert can walk through one concrete scenario without translating, and class and module names match. States that "A compromise name for a polyseme hides a missing context." Says plainly that an agent can draft an event timeline from text and code and must label what it is unsure of, and must not claim to have run a workshop; confirming the language "in experts' mouths" stays with people.
- **PakhomovAlexander/project-hub** (`extra_PakhomovAlexander_project-hub/template/CONTEXT.md`, `template/CLAUDE.md:1-12`) **[file]**: the project's `CLAUDE.md` begins with `@AGENTS.md` and `@CONTEXT.md`, which makes Claude Code load the glossary into every session without the agent choosing to. The template advises: "Aim for the 5–15 terms that people actually get wrong or argue about." (`template/CONTEXT.md:17`). The `_Avoid_` line asks for the reason each rejected word is wrong.
- **dev-cycles/contextive** (`extra_dev-cycles_contextive/docs/web/src/content/docs/guides/setting-up-glossaries.mdx`, `defining-terminology.mdx`) **[file]**: an editor extension, not a skill. Glossary files are YAML named `*.glossary.yml`. A file applies to the folder it sits in and everything below it, so a large project gets one file per area simply by where the files are placed. Each term has `name`, `definition`, `examples` (ideally "exact sentences as said by your domain experts"), `aliases`, and free-form `meta`. The tool finds a term inside code names in any casing (`cargoId`, `cargo_id`) and shows the definition.
- **techygarg/lattice** and **NeoLabHQ/context-engineering-kit** **[file]**: a glossary is an optional section the person may add (`extra_techygarg_lattice/skills/ddd-refiner/SKILL.md:59,84,102`), or a line in a review checklist (`extra_NeoLabHQ_context-engineering-kit/plugins/reflexion/skills/reflect/SKILL.md:258`). Nothing to borrow.

### 2.14 Checked and found nothing

- **multica-ai/andrej-karpathy-skills**: nothing about terms. Nearest lines: "If multiple interpretations exist, present them - don't pick silently." and "Match existing style" (`CLAUDE.md:13,36`).
- **anthropics/skills**: no skill deals with a project's terms. `skills/frontend-design/SKILL.md:67` says an action "keeps the same name through the whole flow" in a user interface.
- **anthropics/claude-plugins-official**: nothing beyond "Consistent terminology: Use same terms throughout" in advice on writing command documentation (`plugins/plugin-dev/skills/command-development/references/documentation-patterns.md:710`).
- **phuryn/pm-skills**: nothing. The requirements skill says to avoid jargon (`pm-execution/skills/create-prd/SKILL.md:75`).

---

## 3. The published methods the skills lean on

### Eric Evans: ubiquitous language

Source: Eric Evans, *Domain-Driven Design Reference: Definitions and Pattern Summaries*, Domain Language, Inc., 2015, pages vi and 2-7. Licensed CC BY 4.0. https://www.domainlanguage.com/wp-content/uploads/2016/05/DDD_Reference_2015-03.pdf (read as a PDF on the survey date). It summarises his 2003 book *Domain-Driven Design: Tackling Complexity in the Heart of Software*.

**[file]** What it says about the language and how the conversation runs:

- Definition (page vi): a language structured around the domain model and "used by all team members within a bounded context". A bounded context is the boundary, typically a subsystem or one team's work, inside which one model applies.
- The problem (page 3): domain experts and developers each have their own vocabulary, everyday talk is disconnected from the words in the code, and "Translation blunts communication".
- Who does what in the conversation (page 3): "Domain experts should object to terms or structures that are awkward or inadequate", and "developers should watch for ambiguity or inconsistency that will trip up design".
- How to test a term (page 3): "Describe scenarios out loud using the elements and interactions of the model", find easier ways to say things, and take the result back to the code.
- The instruction (page 4): use the same language in diagrams, writing, speech and code within the boundary. "Recognize that a change in the language is a change to the model." Try alternative wordings, then rename classes, methods and modules to match. "Resolve confusion over terms in conversation".
- Scope (page 2): several models exist on any large project, so set explicit boundaries and keep terms "strictly consistent within these bounds", without trying to unify outside them.
- Code (page 6): take the terminology of the design from the model, so that a change to the code may be a change to the model.

Also read: Martin Fowler, "UbiquitousLanguage", 31 October 2006, https://martinfowler.com/bliki/UbiquitousLanguage.html, and "BoundedContext", 15 January 2014, https://martinfowler.com/bliki/BoundedContext.html. The second gives the standard example of one word with several meanings: at an electricity company "meter" meant different things to different departments. (Fetched through a summarising tool, so I rely on these two pages only for the dates and that example.)

**[judgement]** Three points in Evans that the skills mostly drop:

1. Evans names no glossary file. The language lives in speech and code, and the pattern text never asks for a written list. Every skill here adds the file because an agent has no memory between sessions.
2. Evans gives the domain expert the right to **object** to a term. Most skills have the agent propose and the person accept; only the citypaul protocol and the mattpocock interview give the person a real veto per term.
3. Evans's test is speaking scenarios aloud with the terms. Only mattpocock (`domain-modeling/SKILL.md:54`) and the removed example-dialogue rule use scenarios to test a term.

### EventStorming (Alberto Brandolini)

Source: ddd-crew, *EventStorming Glossary & Cheat sheet*, https://github.com/ddd-crew/eventstorming-glossary-cheat-sheet, commit `e9bcda0fb1`, CC BY-SA 4.0, 995 stars; it cites Brandolini's books *Introducing EventStorming* and his chapter in *DDD: The First 15 Years*. The official site https://www.eventstorming.com/ describes the method only as a workshop format for exploring business domains across disciplines.

**[file]** What the cheat sheet says about running the conversation:

- Start from events, not from nouns. "A Domain Event is a verb at the past tense." People write the events they know and place them on a timeline, first without order ("chaotic exploration"), then the group makes the timeline consistent and removes duplicates.
- Disagreements are marked, not argued out. A "hotspot" note is used to "visualise and capture hot conflicts", including inconsistencies in language, questions and objections, so they can be explored later.
- A facilitator stays neutral so they can "cut long discussions short and visualise them with hotspots".
- Invite everyone who has the knowledge and everyone who needs it, usually domain experts and engineers.
- Areas of the business with their own language ("emerging bounded contexts") show up from the timeline; they are an output, not an input.
- The sheet itself warns to "avoid jargon as much as possible", because it sets insiders apart from outsiders, and notes that the method retired its own word "aggregate" in favour of "constraint" when talking to business people.

**[judgement]** None of the fourteen libraries, and none of the search finds that I read, runs event storming as its conversation. The usable ideas are small: ask what happens (events and verbs) before asking what things are called, and park a naming disagreement visibly instead of forcing an answer on the spot. CodeAlive's `## Unresolved` section is the nearest equivalent of a hotspot.

---

## 4. Evidence the libraries give for their rules

Only two libraries give real evidence, and almost all of it is about the glossary file going wrong, not about a glossary improving an agent's work.

### mattpocock/skills

| Rule or change | Evidence **[file]** |
|---|---|
| "It is a glossary and nothing else." (`domain-modeling/SKILL.md:64`) | Issue #130, opened 4 May 2026, still open, 12 comments: with one model the file was "used as a plan", rewritten after every answer, with decisions written in the shape of term definitions. Commit `e74f0061bb` (13 May 2026) replaced a soft line ("Don't couple `CONTEXT.md` to implementation details") with the present wording. The docs page calls this "the most-reported problem with the skill, across several models" (`docs/engineering/domain-modeling.md:44`) and says the guidance "is not yet strong enough to prevent the growth" (line 55). Issue #321: one area's file passed 1,000 lines. |
| Entry format cut to term, definition, avoid | Commit `e7df78bb81` (19 May 2026): "Removed relationships, example dialogue, and flagged ambiguities from CONTEXT.md template", 16 lines removed. No reason given in the message. |
| One-shot `ubiquitous-language` skill removed | `CHANGELOG.md:240`: replaced by a skill that maintains the model "rather than dumping a glossary from one conversation". Commit `c66bdeeee0`, 5 August 2026. |
| File renamed from `CONTEXT.md` to `GLOSSARY.md` (version 1.3.0) | `CHANGELOG.md:75-77`; issue #207 asked for it in May 2026; `docs/engineering/domain-modeling.md:58` gives the reason: the name should say what the file is, and a reader's remark that with agents "everything is context". Issues #1153 and #1176 record the cost: repositories set up earlier had no upgrade path until the setup skill learned to rename the old file (`CHANGELOG.md:27`). |
| "Call the Skill tool twice" wording | `CHANGELOG.md:91-94` and issue #556 (open, 10 comments): "Even on strong models" the interview loaded and the glossary skill did not, "so the shared language … never gets established". Naming a skill in prose "does not reliably cause it to load". The docs page: if the glossary is unchanged at the end of an interview, "that is what happened" (`docs/engineering/domain-modeling.md:9`). |
| Facts for the agent, decisions for the person | `CHANGELOG.md:275`: the earlier single line read as permission to answer decisions too once another skill ran the interview. |
| "yes" accepts the recommendation | `CHANGELOG.md:19`, issue #706. |
| Known gaps the author states and has not closed | Entries are never revisited when code changes: issue #827 (closed) reports domain docs describing an old model after sixteen schema commits, "caught late, cost a full audit". Names already settled in the issue tracker are raised again as new: issue #717 (open). No way to start a glossary for a large old codebase in bounded time: issues #101, #930. Writes silently missing when the skill runs inside another tool's pipeline (`docs/engineering/grill-with-docs.md:49`). The pointer file not being read: issue #1376 (open, reported on Opus 5.5). |
| Doubt about the whole idea | The author's own docs: a term and its plain-English expansion may get the same result from the model, so the value may go to the people, not the agent; skip it on a one-day build; and "an unreviewed, agent-authored glossary is worse than none" because later sessions treat its claims as true (`docs/engineering/domain-modeling.md:70`). No measurement either way. |

### EveryInc/compound-engineering-plugin

| Rule or change | Evidence **[file]** |
|---|---|
| `CONCEPTS.md` introduced, seeded as well as grown | Pull request #838, merged 2 June 2026. Claims three benefits (person and agent, between skills, across sessions) without measurement. The seeding rule is argued, not measured. |
| Fold, retire and delete added; second test for an entry | Pull request #1540, merged 25 August 2026, with measurement from a real project using the skills: across all 25 commits to that project's glossary, 380 lines added and 11 removed; entries grew from 35 to 76 while the codebase doubled. Its conclusion: "The file simply had no subtract." It also found that terms which were only a property of an existing entry had been getting their own headings. |
| Neighbour check runs on every write-up, not only when an entry changed | Same pull request: because most runs add nothing, the check "almost never ran", which is how code identifiers stayed in the file. |
| Report must state what changed | Same pull request: a run could merge or clean entries and still report "scanned, no qualifying terms". |
| Whole file is read, not a slice | Same pull request: reading headings plus one group cost about 1,000 tokens against about 7,500 for the file, but the full read "caught a cross-cluster term collision a bounded read would have missed". |
| Retired terms kept in a tail section | Same pull request: tried on Claude and Codex with the repository's skill test cells; before the change both deleted the entry, after it both moved it to `## Retired` with an explanation. These were one-off runs; no test rows were added. |
| Conflict raised during the interview | Pull request #1487, merged 19 August 2026, and `tests/skills/ce-brainstorm-ask-decisions.test.ts:5-8,60-83`: closes a seam where the agent "let conflicting terms slide until the write-up". The test checks that the instruction text is present, not that an agent behaves that way. |
| Entries checked against source by a separate agent | `assembly.md:64` and `grounding-validation.md:37` give the reason in words only. |

### The others

- **gstack** **[file]**: `test/fixtures/multi-agent-wave/INCIDENTS.md:53` records the incident behind the banned-terms check: "a renamed product's old name landed in README while the glossary was allowed". The same table (line 49) records agent prompts that paraphrased shared rules differently; the fix was one shared text block, tested for "same bytes". Tests: `test/owner-brief-contributor-banned.test.ts`.
- **superpowers** **[file]**: `RELEASE-NOTES.md:372` says naming rules are now copied word for word into the plan "so they actually reach the implementers and reviewers downstream". The same release notes say a plan written this way "needed one round of fixes where the control needed two to four" (line 374); that figure is for the plan structure as a whole, not for naming.
- **get-shit-done** **[file]**: `CONTEXT.md:294`: a paraphrased rule in agent briefs "caused 5 of 8 agents" to break the rule it summarised.
- **OpenSpec** **[file]**: the vocabulary test itself, and the dated decision in `roadmap.md:459-470`.
- **spec-kit, BMAD, wshobson, CodeAlive, citypaul, evanflow, ciembor**: no test, changelog entry or issue that I found ties a term rule to an observed failure. CodeAlive's layout choices come with reasons in the text (for example why not tables) but no measurements. The spec-kit `clarify` command dates from September 2025 (`gh api` history: first commit `c7b61f4b`, 23 September 2025).

**[judgement]** No library shows, by test or measurement, that later agents keep to a glossary, or that work is better when they do. The measured facts are about the file: it grows without limit unless something removes entries, it fills with implementation detail and decisions unless told very firmly not to, and agents skip loading the skill that maintains it.

---

## 5. Where the sources agree and disagree

Everything in this section is **[judgement]**, resting on the lines cited in section 2.

### They agree on

1. **One name per concept, and the rejected names are written down on the winner's entry.** mattpocock (`_Avoid_`), compound-engineering (`Avoid:`), CodeAlive (`avoid:`), the conductor table ("Don't Use"), project-hub, citypaul (aliases), spec-kit ("Avoided synonyms / deprecated terms"), and Evans's rule as restated by ciembor. This is the most widely shared idea, and the one part of the entry every format keeps.
2. **The agent chooses and recommends; it does not hand the person a list.** mattpocock ("Be opinionated"), compound-engineering (same words), evanflow, spec-kit (recommended option), citypaul (recommendation with alternatives).
3. **Definitions are one or two sentences and say what the thing is.** mattpocock, compound-engineering, CodeAlive, evanflow, project-hub (one to three).
4. **Only words with a meaning specific to this project.** General programming words are left out everywhere they are mentioned.
5. **The glossary is not a specification or a notebook.** mattpocock and compound-engineering say it in nearly the same words, and CodeAlive says the file "captures concepts, not behavior". All three say it because the file filled with other material in practice.
6. **A clash between the person's word and the existing glossary is raised at once, in the conversation.** mattpocock, compound-engineering's interview, bigpowers.
7. **Existing code shows what words are in use but does not get to decide.** CodeAlive and citypaul say this in almost the same words; mattpocock asks the person "which is right?".
8. **Later agents find the file through a short pointer in `CLAUDE.md` or `AGENTS.md`, plus one line in each skill that names things.** mattpocock, compound-engineering, CodeAlive, project-hub. Nobody relies on the agent discovering the file.
9. **Start with one file at the root. Split by area only on real evidence.** mattpocock (only for multi-package repositories), CodeAlive (only after the person confirms two meanings), Evans (the boundary is where the language changes).
10. **Do not create or demand the file before there is something to put in it.** mattpocock ("Create files lazily"), compound-engineering ("Never nag"), citypaul ("never a big up-front vocabulary exercise").

### They disagree on

| Question | Positions |
|---|---|
| **When an agreed term is written to the file** | *The moment it is settled, mid-conversation* (mattpocock: "Don't batch these up"). *After the plan, once the name has stopped moving* (compound-engineering: early capture "would miss the final resolved name"). *In one pass at the end of a conversation* (the old mattpocock skill and its copies). *In the same change as the code that first uses it* (citypaul). mattpocock's inline writing is the setting in which the file turned into a running plan (issue #130). |
| **Whether the person approves each term** | *Yes, one at a time, before any use* (citypaul: "An agent never coins a domain term silently."). *Yes, by answering interview questions* (mattpocock). *Only conflicts and open questions; the agent adds plain new terms itself* (CodeAlive). *No: the agent writes silently, reports what changed, and a second agent checks the entries against code* (compound-engineering). |
| **Where terms should come from first** | *The person's words in conversation* (mattpocock, superpowers, Evans). *The code, and explicitly not the docs* (CodeAlive). *The schema and core types* (compound-engineering's seeding). *Events and verbs before nouns* (EventStorming, evanflow partly). |
| **Whether code names belong in the file** | *No, never* (mattpocock, compound-engineering: entries must outlive the code). *Yes, one identifier per term, and old names with their locations* (CodeAlive). *Where a check needs them* (citypaul: "Forms are explicit where they matter"). |
| **What an entry holds beyond definition and avoided words** | *Nothing* (mattpocock since May 2026). *A "what it is not" line and related terms* (CodeAlive). *An example sentence* (Contextive, citypaul; the old mattpocock dialogue). *A second paragraph of rules, relationships, a list of settled ambiguities, a retired list* (compound-engineering). *Relationships and how many of each* (BMAD, evanflow). mattpocock removed relationships, dialogue and ambiguities from its template, yet its own glossary still uses two of the three. |
| **File name** | `GLOSSARY.md` (mattpocock now), `CONTEXT.md` (mattpocock before, evanflow, get-shit-done, project-hub), `CONCEPTS.md` (compound-engineering), `UBIQUITOUS_LANGUAGE.md` (old mattpocock and copies), `docs/THESAURUS.md` (CodeAlive), `glossary.md` beside a ticket (BMAD), `*.glossary.yml` (Contextive), a section inside another document (BMAD, spec-kit, conductor). mattpocock's rename shows the cost of changing the name later. |
| **Format** | Bold term with lines under it (mattpocock, project-hub); headings (compound-engineering); tables (old mattpocock, evanflow, conductor); search-friendly token lines with a stated case against tables (CodeAlive); YAML (Contextive). |
| **How entries leave the file** | *No rule* (mattpocock). *Fold, retire or delete, only by one job, only on positive evidence* (compound-engineering). *Rename, split, merge, retire, deprecate, with the old name kept as a pointer* (CodeAlive). |
| **How many questions, and how grouped** | *Rounds of independent questions, no limit* (mattpocock). *One at a time, five at most* (spec-kit). *One term at a time* (citypaul). *Collect everything, then one batch* (CodeAlive). |
| **How keeping to the terms is checked** | *An instruction in prose only* (most). *A read-only pass over specification, plan and tasks* (spec-kit `analyze`). *A script over the lines a change adds, run in review* (gstack). *Lint rules generated from the glossary, each with a test that proves it fires* (citypaul). *A repository test for one retired word* (OpenSpec). |
| **What to do when a later agent needs a word that is missing** | *Reconsider, or note the gap for the glossary skill* (mattpocock). *Add it yourself, then use it* (CodeAlive; compound-engineering's planner). *Stop and propose it to the person* (citypaul). |
| **Whether a glossary helps the agent at all** | compound-engineering asserts it does. mattpocock's own docs doubt it and say the gain may be for the people. Neither measures it. |

---

## 6. What looks written for earlier, weaker models

Everything here is **[judgement]**. The yardstick is Anthropic's own audit guidance in `libs/anthropics_skills/skills/claude-api/shared/prompt-audit.md`: emphasis added for older models now "causes over-triggering and rigid behavior" (line 62); when several instructions are marked critical "the markers stop carrying information" (line 73); "plan before acting" and step-by-step scripts should be deleted because current models plan unprompted (line 84); and fixed numeric caps tuned against an older model should be dropped. That guidance is written for Claude models; I assume it carries over to the two GPT-6 models named in the brief, which I have not verified.

| Library and lines | What is there | Why it may now do harm |
|---|---|---|
| **spec-kit** `templates/commands/clarify.md:129-141` | "Maximum of 5 total questions", "EXACTLY ONE question at a time", answers limited to five words or a multiple-choice letter. | Written in September 2025. A term with two meanings cannot be settled in five words, and a five-question cap shared with security, data and scope questions leaves terms last. mattpocock refused a cap for this reason. |
| **spec-kit** `clarify.md:62-228` | Nine numbered execution steps, a per-write validation list, and capitals ("NEVER", "MUST") through the question rules. | A fixed script for something a capable model does by judgement. The validation list re-checks what the model just wrote. |
| **spec-kit** `analyze.md:60`, `clarify.md:243` | The constitution is "**non-negotiable**"; "You **MUST** complete this section". | Pressure wording with no reason beside it. |
| **bigpowers** `skills/define-language/SKILL.md:14` | "**HARD GATE** — Ubiquitous language is NOT optional. Every term … that could be misunderstood must be glossed." | Added on top of the copied mattpocock text. Pushes the agent to define everything, which is the over-filling that mattpocock and compound-engineering spent months removing. |
| **CodeAlive** `skills/ubiquitous-language/SKILL.md:5,275-279` | "Use PROACTIVELY when naming anything", and "**ALWAYS** run this before naming" a list that includes variables, parameters and commit messages. | With a model that follows instructions closely this means a glossary search before every local variable. The skill's own body later exempts short-lived local names (`SKILL.md:502-503`), so the two parts pull against each other. |
| **CodeAlive** `SKILL.md:577-591` | An eleven-question checklist before naming anything, ending "stop and fix before proceeding". | A reminder list of what the body already says; it adds weight, and a stop, to every naming act. |
| **CodeAlive** `references/generating-thesaurus.md:101,164`; `SKILL.md:441-463` | "**This step is mandatory**" twice; a fixed list of banned words ("Manager", "Service", "Data", "Item"…) "never use in domain layer". | The banned list is the author's taste applied to every project. citypaul's version of the same idea is better judged: treat such words "as prompts for review, never universal bans" (`extra_citypaul_.dotfiles/…/ubiquitous-language/SKILL.md:44`). |
| **ciembor** `domain-driven-design/domain-driven-design.mini.md:1`, `domain-driven-design.md:146-163` | Title "OBEY Domain-Driven Design"; every section headed "Rules (MUST unless marked SHOULD or MUST NOT)", "Required behavior (MUST)", "Anti-patterns (MUST NOT)". | Uniform pressure on every line, so none stands out. "Rename code when the domain understanding improves" as an unqualified MUST invites renames nobody asked for. |
| **citypaul** `resources/language-protocol.md:16`; `SKILL.md:32,73-92` | "STOP. Do not use the term in code, tests, or the DSL yet." for every new term; "Silent evolution is forbidden"; an eighteen-item verification checklist. | The idea (the person decides names) is sound. As a hard stop on every missing word it will interrupt a long unattended build each time a helper concept needs a name. The checklist repeats the body. |
| **evanflow** `skills/evanflow-glossary/SKILL.md:20-93` | A five-step numbered flow and a "Hard Rules" list, including "One sentence per definition. If you need a paragraph, the term is too vague — split it." | The fixed sequence is harmless but unnecessary. The one-sentence rule is too rigid: compound-engineering found some terms need a second paragraph for their rules. |
| **The old mattpocock skill and its copies** `extra_mattpocock_skills_history/…:11-20,69,85-93` | A five-step process, a required example dialogue of three to five exchanges, a five-step re-run procedure. | The author removed all of it. The dialogue requirement asks for invented conversation in a file meant to hold agreed facts. |
| **superpowers** `skills/brainstorming/SKILL.md:3,269-283,285-294` | Description opens "You MUST use this before any creative work"; a `<HARD-GATE>` block; a "Red Flags" table of thoughts to distrust. | Not about terms, but it is the interview a glossary step would sit inside. The body is otherwise written for current models (plain reasons, judgement calls). The capitals in the description are a trigger aid; the gate has a stated reason and two exceptions, so it is the least dated of these. |
| **compound-engineering** `skills/ce-compound/references/assembly.md:60`, `refresh/overview.md:50`, `research.md:47` | "This is unconditional. Do not pre-judge from memory that nothing qualifies."; "**CRITICAL: glob … fresh every run.**" | Reminders to do what the skill just asked. The first two carry a reason and trace to a measured failure (the step being skipped), so they may be earned. The capitals in the third are the older habit. |
| **mattpocock** `skills/productivity/grilling/SKILL.md:3,6` | "relentlessly", twice. | Deliberate: the changelog says the word "grill" was chosen to sharpen when the skill loads (`CHANGELOG.md:273`). With a model that follows wording closely it also explains the reports of fifty-question sessions. Worth a softer word in a new skill. |
| **mattpocock** `.agents/invocation.md:20`, and every "Call the Skill tool twice" line | Exact tool-call wording so both skills load. | Not a weak-model crutch: issue #556 reports the failure "Even on strong models", and issue #1376 reports a pointer file unread on Opus 5.5. This is a real, current limit of skills that depend on other skills. The lesson for a new skill is to avoid depending on a second skill being loaded. |
| **get-shit-done** `CONTEXT.md:3-7,291-294` | Rules as `KEY=value` lines agents must cite by identifier; "MUST quote". | The format is odd, but the lesson under it (quote, do not paraphrase) has an incident behind it and matches superpowers and gstack. Keep the lesson, not the format. |

Not dated, and worth keeping as written: mattpocock's `domain-modeling/SKILL.md` and `GLOSSARY-FORMAT.md` (short, reasons given, no capitals); compound-engineering's `concepts-vocabulary.md` (states tests and reasons, leaves counts to judgement: "The codebase sets the count", line 20); BMAD's template comments ("This template is expert prior knowledge, not a checklist", `template-prd.md:17`).

---

## 7. What none of them covers that this job seems to need

Everything here is **[judgement]**. "This job" is the one in the brief: an agent and the person agree the terms, and then every later agent and every file keeps to them, across Claude Code and Codex.

1. **No evidence that later agents keep to the glossary.** No library tests it. The only checks that look at later work are spec-kit's read-only pass over three planning files, gstack's banned-word scan of a change, and citypaul's optional lint. A design that claims "every later agent and every file" needs its own check, and should say in what it produces whether that check ran.

2. **Agents that start with a clean view are barely handled.** The usual mechanism is a pointer in `CLAUDE.md`, which a sub-agent or a separately launched reviewer may not load, and which mattpocock's own issues show being skipped. The stronger pattern exists only outside the glossary skills: put the exact names into the document the agent is handed (superpowers' "Global Constraints" and "Interfaces" blocks; mattpocock's one line about sub-agent briefs at `codebase-design/DESIGN-IT-TWICE.md:30`), and pass them word for word, not summarised (get-shit-done, gstack). No library says which terms a brief should carry when the glossary is too long to paste whole.

3. **Nobody records who agreed a term.** A file edited by agents mixes entries the person approved with entries an agent inferred. mattpocock warns that an unreviewed agent-written glossary is worse than none, and compound-engineering writes silently by design. The nearest things are CodeAlive's file-level "Reconstructed, not authored" notice and citypaul's "visibly provisional" names. No format marks a single entry as agreed by the person, proposed by an agent, or taken from code.

4. **The agent's own invented labels are not treated as a source of the problem.** Every library assumes the competing words come from the person, the code or the documents. In long agent runs a third name often comes from the agent itself: a label it coined mid-task and then used in the plan, the code and the chat. Only Anthropic's migration guide mentions it, telling the model the reader does not know "the codenames or shorthand you created along the way" (`anthropics_skills/skills/claude-api/shared/model-migration.md:1068`). citypaul's rule against coining silently is the only skill rule that touches it.

5. **Nothing says the chosen term should be plain.** All the selection rules are about precision ("the best one"). None prefers the word the person already uses, or a longer ordinary phrase over a short invented one. Superpowers' "Match their vocabulary" and gstack's explain-on-first-use rule are about chat, not about which term wins. For a person who is not a developer, or who works only through chat, this matters more than precision between two technical synonyms.

6. **The word in prose and the name stored in code or data are treated as one thing, or the stored name is banned from the file.** mattpocock and compound-engineering forbid code names in the glossary. CodeAlive and Contextive tie each term to one identifier. Nobody covers the middle case that real projects have: a status or field value that is fixed in files and data (and costly to change) alongside a clearer phrase used when talking to the person, with the entry stating both and which to use where. The same gap covers names that come from outside the project (a framework's or a vendor's word that the code must use but the person does not).

7. **Verbs, states and roles get little attention.** The formats and examples are almost all nouns. evanflow lists verbs and status values to collect, CodeAlive has kinds for events, commands and states, and EventStorming starts from events. Misunderstandings between a person and an agent are often about a step or a state ("done", "ready", "reviewed"), which none of the main skills singles out.

8. **A project with no code yet is not covered as its own case.** CodeAlive needs code. compound-engineering creates the file only after work has produced a lesson. mattpocock covers it only through a general design interview with no end condition for terms. The brief asks for agreement before planning; none of the libraries defines what "the terms are agreed enough to plan" looks like. pedronauck's three-part test (short glossary, a scenario walked through without translating, code names match) is the only stated end condition, and its third part needs code.

9. **A term that changes after it has been used.** CodeAlive and citypaul say how to rename code. compound-engineering says how to retire an entry. Nobody says what to do with plans, task lists, records of finished work and chat summaries already written with the old word. The practice visible in three repositories is to leave history alone and state where the old word is still allowed (mattpocock's rename commit left the changelog untouched; OpenSpec's test skips planning history; gstack's `allowed_paths`). That is a rule a new skill could state outright.

10. **Changes by several agents at once.** mattpocock lets any session edit the file; compound-engineering limits removal to one job but lets several skills add. Nobody addresses two agents working in parallel that each add or change a term, or a builder that needs a new word while the person is away. Options seen: note the gap and carry on (mattpocock), add it yourself (CodeAlive), stop (citypaul). None has a "use a marked provisional name, list it for the person" path with a defined place for the list, though citypaul and CodeAlive's `## Unresolved` come close.

11. **Size, and what a brief should load.** Reports of files at 500 to 3,000 lines (mattpocock) and a measured 7,500 tokens (compound-engineering) show the cost. Suggested sizes exist (5 to 15 terms in project-hub; 15 to 40 per area in CodeAlive) with no evidence behind them. compound-engineering chose to always read the whole file and gave a reason. Nobody sets a size at which to split, other than "when the repository has several packages".

12. **Asking a person who answers in chat.** mattpocock's rounds with a recommended answer where "yes" accepts are the best-developed way of asking, and its docs note some people need one question at a time. None of the libraries shows the person the resulting entry before it is treated as agreed, and none says how to present a batch of term decisions so that a short reply settles them.

13. **Two meanings inside one small project.** Splitting by area is tied to multi-package repositories (mattpocock) or to a confirmed rule difference (CodeAlive). A single-package project where one word means two things in two modules gets only the advice to pick two different words.

14. **Whether to do this at all.** mattpocock's docs say to skip the glossary on a one-day build. No library gives a test for when a project is too small or too short-lived for the cost, or a lighter form (for example, a short list of terms inside the plan) for that case. BMAD's glossary section inside the requirements document and spec-kit's per-feature clarifications are that lighter form, but neither is offered as a choice.
