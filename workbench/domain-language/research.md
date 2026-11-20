# Research: skills and practice for agreeing a project's domain language

Written 19 November 2026, for a rewrite of `domain-language` as a standalone skill that does not depend on the
orchestrate set.

This builds on [references/01-library-survey.md](references/01-library-survey.md) (10 November 2026), which read
fourteen libraries and about a dozen GitHub finds in depth. That survey is not repeated here. What is new in this
pass:

- mattpocock/skills was re-read from `main` today (`domain-modeling/SKILL.md`, `GLOSSARY-FORMAT.md`,
  `setup-matt-pocock-skills/domain.md`, `docs/engineering/domain-modeling.md`, `grilling/SKILL.md`,
  `wait-what/SKILL.md`). The old `ubiquitous-language` skill is deleted, not deprecated; the `deprecated/` folder is
  empty.
- Newly read: chrislacey89/skills `ubiquitous-language`, anton-abyzov/specweave `sw-glossary`,
  AgentiveStack/skills `domain`, evans-sam/skills `ubiquitous-language`, terrylica/cc-skills `glossary-management`,
  the skills.sh listing for petekp's copy, pedronauck `ddd-master` references `discovery.md` and `when-not.md`, a
  third-party Cursor/Claude glossary guide, the Domain Storytelling quick-start guide, and Vernon's IDDD excerpt.
- Checked for drift since the survey: the last commit to CodeAlive's skill is 2026-08-21, to citypaul's 2026-08-09,
  and to compound-engineering's `concepts-vocabulary.md` 2026-11-02. All predate the survey, so its reading of them
  stands. **I did not re-read those three files today**; quotes from them below come from the survey.
- anthropics/skills and openai/skills have no glossary, terminology or domain-language skill (tree search today).

Marking: **[read]** means I read the file or page in this pass or it is unchanged since the survey read it.
**[unverified]** means I could not read the primary text.

---

## 1. The best sources, ranked

Ranked by how much a standalone rewrite can take from them, not by stars.

### 1. mattpocock/skills: `domain-modeling` with `grilling`, the pointer file and the docs page [read]

https://github.com/mattpocock/skills/tree/main/skills/engineering/domain-modeling
and https://github.com/mattpocock/skills/blob/main/docs/engineering/domain-modeling.md (repo ~328k stars)

**Does well**
- Splits the job cleanly: one skill *changes* the language; every other skill only *reads* the file through a
  one-line habit. "Merely reading GLOSSARY.md ... is not this skill".
- Four in-conversation moves, each with a model sentence: challenge against the glossary, sharpen fuzzy words
  ("do you mean the Customer or the User?"), stress-test with invented edge-case scenarios, and check the human's
  claim against the code ("Your code cancels entire Orders, but you just said...").
- Lean entry format: bold term, one or two sentences on what it *is*, `_Avoid_` list. "Be opinionated."
- The guard that matters most, learned from its most-reported failure: "It is a glossary and nothing else."
- `grilling` is the best question protocol found: rounds of independent questions, a recommended answer on each,
  "Word each question so 'yes' accepts your recommended answer", and "Finding facts is your job, never the user's."
- The docs page is unusually honest: auto-loading is "the weakest part of the skill"; a glossary may help the
  humans more than the agent; "an unreviewed, agent-authored glossary is worse than none"; skip it on a one-day
  build; it does not invent vocabulary the human does not have.
- Lazy creation, and later agents are told to "proceed silently" if the file is missing.
- `wait-what` (a one-line, human-invoked skill) is a cheap drift-repair tool: re-pitch the last message using the
  glossary's language.

**Does badly**
- Precision is the only selection rule. Nothing prefers the human's own word or a plain longer phrase.
- No per-entry provenance: an agent-written guess and a human-agreed term look the same.
- No rule for removing entries ("gets shorter as often as it gets longer" is a hope, not an instruction); files
  of 500 to 3,000 lines are reported.
- Bundles ADRs in the same skill (issue #557 asks to split them).
- Depends on a second skill loading; models often load `grilling` and skip `domain-modeling`.
- Code names are kept out of the glossary entirely, so a status stored as `claimed` has nowhere to be recorded.
- "Relentlessly" in `grilling` produces 50+ question sessions on brownfield repos.

### 2. EveryInc/compound-engineering-plugin: `CONCEPTS.md` rules (`ce-compound/references/concepts-vocabulary.md`) [read via survey; file unchanged since]

https://github.com/EveryInc/compound-engineering-plugin (26k stars)

**Does well**
- The only source with a full life cycle: add, refine, fold, retire, delete, scrub, each named.
- Removal needs positive evidence of where the concept went; "uncertainty leaves it standing".
- Two discovery routes, named: *accretion* (a term arrives because it caused confusion) and *seeding* (define the
  core nouns from the declared domain model: schema, core types, top-level docs, "not a full-codebase trawl"). The
  reason for seeding: the nouns a system is built around rarely cause confusion, so accretion alone never records
  them.
- Entry test: "Each entry teaches its concept to a reader with no access to anything else."
- A separate read-only agent checks new entries against the source, because an entry written from a summary is how
  wrong meanings get in.
- After any change, checks that `AGENTS.md`/`CLAUDE.md` would lead an agent to the file. "Never nag for an
  artifact the project has not adopted."

**Does badly**
- Writes "silently in every mode — no user prompt". The human never agrees the names.
- Starts only after work is done, so it cannot help agree names before a plan.
- Lives inside a larger workflow; not usable alone.

### 3. chrislacey89/skills: `ubiquitous-language` [read]

https://github.com/chrislacey89/skills/blob/main/ubiquitous-language/SKILL.md (7 stars, updated today; cites Evans,
Hofer & Schwentner, Martraire)

**Does well**
- Starts by walking one workflow as a story: "[who] does [what] using [tool]". Nouns become term candidates, verbs
  behaviour candidates. This is Domain Storytelling turned into an agent instruction.
- Treats a domain expert *correcting* a developer's word as a high-value signal.
- Names three kinds of hidden concept: circumlocutions (a clause used because no word exists), hidden rules
  described procedurally, and contradictions that dissolve once a new concept is named. "Name the unnamed."
- A behaviour check, not just a name check: when the human states a rule, make *one* search for the code that
  enforces it; if the code disagrees, say so before writing the term; if nothing enforces it, record "unenforced".
  "do not edit the glossary to match a bug."
- Defines when a term is *settled* (human confirmed name and definition, and the code check ran), and writes it
  then, so an interrupted conversation still leaves agreed terms on disk.
- "Modeling Out Loud" as a private diagnostic: compose a short scenario using the terms; a term that needs a gloss
  or gets swapped for another word is suspect. Kept out of the file.
- One question per turn, and use the host's question tool (`AskUserQuestion`, `request_user_input`).

**Does badly**
- Tables in the file (hard to grep, noisy diffs), plus relationships, a "Model-code fractures" table and a
  surfaced-concepts table: the file holds findings and recommendations, not only names.
- `disable-model-invocation: true`: only runs when typed, so nothing catches drift mid-work.
- One question per turn is slow for twenty terms.
- Tiny install base; untested.

### 4. anton-abyzov/specweave: `sw-glossary` [read]

https://github.com/anton-abyzov/specweave/blob/main/skills/sw-glossary/SKILL.md (173 stars; adapted from
mattpocock, last changed 2026-10-27)

**Does well**
- Each entry says where the term lives at each level: `Data` (table), `Code` (type, route), `UI` (screen text),
  plus optional `Rules`. This is the nearest published equivalent of our `Stored as`, and it adds UI text.
- Harvest before asking: README, schema or migrations, models and types, routes, UI strings. List every mismatch
  across levels, then ask: "The table is `purchases`, the type is `Order`, the button says Basket. Call all three an
  Order?"
- "Drift is work, not an edit": avoided words in code or data are listed for the human and renamed as planned
  work, never silently.
- A check command lists avoided words used as identifiers *and* backticked code names that no longer exist, with a
  strict mode for CI. The manual fallback is given: `git grep -n -i -w purchase`.
- Adds a short "Shared language" section to `AGENTS.md`.

**Does badly**
- The check is a SpecWeave CLI feature, not portable.
- Recommends names to the human before hearing the human's own words, which invites accepting tidy proposals.
- Every entry carries code paths, so the file goes stale as code moves (the check partly offsets this).

### 5. CodeAlive-AI/ai-driven-development: `ubiquitous-language` [read via survey; unchanged since 2026-08-21]

https://github.com/CodeAlive-AI/ai-driven-development/tree/main/skills/ubiquitous-language (187 stars)

**Does well**
- A `NOT:` line naming the neighbouring concept a term is confused with (our `Not:` came from here).
- Separate `## Unresolved` (a clash with its locations, impact and options) and `## Legacy` (old name, new name,
  where the old one still lives) sections: a written form of EventStorming's hotspot.
- Lines written to be found by one text search; a stated case against tables.
- A generated file opens with "Reconstructed, not authored": names from code are evidence until a human confirms.
- "The codebase is primary evidence, not automatic authority."
- After generation, adds a pointer to every agent instruction file it finds (`CLAUDE.md`, `AGENTS.md`,
  `GEMINI.md`, `.cursorrules`, Copilot's file).
- Optional git-history mining to see which of two names is newer: "History is evidence, not authority."

**Does badly**
- "Use PROACTIVELY when naming anything", including variables and commit messages: a glossary lookup before every
  local name.
- A fixed list of banned words ("Manager", "Service") as one author's taste; heavy MUST/mandatory wording.
- 591-line SKILL.md plus a 538-line reference.

### 6. citypaul/.dotfiles: `ubiquitous-language` [read via survey; unchanged since 2026-08-09]

https://github.com/citypaul/.dotfiles/tree/main/claude/.claude/skills/ubiquitous-language (760 stars)

**Does well**
- Who decides: "An agent never coins a domain term silently." A name used before agreement must be "visibly
  provisional".
- "Absence from the glossary means not yet agreed": a missing word is neither approved nor banned.
- The clearest statement of enforcement: "Prompt-level glossaries steer; deterministic gates enforce." Lint rules
  generated from the glossary, each with a test proving it fires, and "never imply protection that isn't there".
- Rename vs meaning change: "did the meaning move, or just the spelling?"
- Names consumed by other systems (APIs, events, database contracts) are versioned, "never a casual rename".
- On old code, enforce one area first; a rule that fires thousands of times on day one gets bypassed.

**Does badly**
- A hard STOP for every new term, which halts any unattended run.
- An eighteen-item checklist repeating the body.
- Defaults to Contextive YAML files per bounded context: heavy for a small project.

### 7. Domain Storytelling (Hofer and Schwentner) [read: quick-start guide; book unverified]

https://domainstorytelling.org/quick-start-guide

**Does well** (as an elicitation method an agent can run in chat)
- Every sentence is actor, activity, work object; actors and work objects are nouns, activities verbs. Steps are
  numbered. This captures roles and steps as well as things.
- Concrete examples, not abstract models: start with the common case, note variations, give only significant
  alternatives their own story.
- The moderator uses the participants' words, not their own, and the experts can see at once whether they were
  understood.
- Scope is set on three axes: granularity, as-is vs to-be, and whether software appears in the story ("pure" vs
  "digitalized"). That last axis is useful: a pure story yields the human's business words; a digitalized one
  yields the names of screens and statuses.

**Does badly** for this job: a workshop method for a room with a drawing tool; it has no glossary file and nothing
about later agents. The book's chapter on learning domain language was not read **[unverified]**.

### 8. Eric Evans, *Domain-Driven Design Reference* (2015, CC BY 4.0) [read via survey]

https://www.domainlanguage.com/wp-content/uploads/2016/05/DDD_Reference_2015-03.pdf

**Does well**
- Roles: domain experts "should object to terms or structures that are awkward"; developers watch for ambiguity.
- The test: "Describe scenarios out loud using the elements and interactions of the model."
- "Recognize that a change in the language is a change to the model."
- "Translation blunts communication": the cost of a prose name differing from the code name.
- One language per bounded context; do not force unity across boundaries.

**Does badly** for this job: names no file, assumes a team with memory, and gives no procedure.

### 9. EventStorming cheat sheet (ddd-crew, after Brandolini) and pedronauck `ddd-master` [read]

https://github.com/ddd-crew/eventstorming-glossary-cheat-sheet;
https://github.com/pedronauck/skills/tree/main/skills/mine/ddd-master (655 stars)

**Does well**
- Ask what *happens* (past-tense events) before what things are called.
- Mark a disagreement as a hotspot and move on instead of forcing a verdict; "visualise both opinions".
- pedronauck states what an agent can and cannot do here: it can synthesise a first event list from code and text
  and label uncertainty; it cannot claim it facilitated a workshop or that the language is confirmed "in experts'
  mouths". A good honesty line for a chat skill.
- `when-not.md` keeps "lowercase ddd" (ask, name, split terms) even when tactical DDD is refused: language work is
  useful on projects too simple for DDD.

**Does badly**: the workshop needs people in a room; ddd-master is mostly tactical DDD, out of scope here.

### 10. Vaughn Vernon, *Implementing Domain-Driven Design*, ch. 1 [read: InformIT excerpt]

https://www.informit.com/articles/article.aspx?p=1944876&seqNum=3

**Does well**
- The glossary records rejected alternatives *and why* they failed.
- A few people write it, the whole team reviews it, "be ready to edit heavily".
- The written forms can be thrown away when stale; speech and code last longest.

**Does badly** for this job: no procedure, and "discard the glossary" does not fit agents with no memory.

### Noted but not ranked

- **Khononov, *Learning Domain-Driven Design*, ch. 2–3**: the language should be free of "ambiguity, implicit
  assumptions, and extraneous details" (ch. 3 preview, via search snippet). His advice on a wiki glossary, Gherkin
  tests and the limits of tools is from memory only **[unverified]**: O'Reilly returned 403.
- **terrylica/cc-skills `glossary-management`** (3 stars): syncs a glossary into Vale substitution rules and runs it
  from a PostToolUse hook. Proof that a prose linter can enforce avoided words in docs; the setup is personal and
  global (`~/.claude`), not per project.
- **The old mattpocock `ubiquitous-language` family** (evans-sam, petekp, many forks; listed on skills.sh): scans
  the conversation at the end and dumps a `UBIQUITOUS_LANGUAGE.md` with tables, relationships and an invented
  example dialogue, then promises "From this point forward I will use these terms consistently." Its author
  deleted it in favour of inline capture. Useful only as the design to avoid.
- **AgentiveStack/skills `domain`** (72 stars): a mattpocock derivative that asks one question at a time and
  writes glossary, per-context docs and ADRs. Nothing new.
- **Cursor guidance**: Cursor project rules live in `.cursor/rules/*.mdc` with `alwaysApply`; a third-party guide
  (https://guilde-llimes.github.io/docs/04-nice-to-have/domain-glossary.html) advises keeping only the 10–15 terms
  the model most often confuses in an always-applied rule and the rest in a file read on demand, and listing the
  plausible synonyms to avoid. Single unofficial source; no evidence given.
- **spec-kit** (`clarify` + `analyze`, via survey): a read-only pass reporting "Terminology drift (same concept
  named differently across files)" is the only published *audit* of drift across plan files.

---

## 2. Techniques worth taking

### 2.1 Discovering terms

- **Get the human's telling first, then harvest.** Ask for one concrete walk through the main job as a story:
  who does what, with what, in what order (Domain Storytelling; chrislacey89 step 1). The human's nouns and verbs
  come out in one answer, before any name is offered. Our own eval showed that offering names first makes the
  human accept tidy agent names.
- **Harvest the repository yourself, by level.** Schema or migrations, core types, routes, status enums, UI
  strings, README and docs (specweave; compound-engineering's *seeding*: the declared model, not a full trawl).
  Keep a note of which level each name came from: data, code, UI, docs, human.
- **Look for what has no name.** Circumlocutions, rules described as "if X and Y and not Z", and arguments that
  dissolve once a concept is named (chrislacey89). Also labels an agent coined mid-task (our own finding; nobody
  else covers it).
- **Steps, statuses and roles, not only nouns.** EventStorming's events-first question ("what happens next?") and
  storytelling's actor–activity–work-object sentences both surface verbs and states, which is where human and agent
  most often misunderstand each other ("done", "ready", "reviewed").
- **Accretion after the first pass.** A term also arrives later, when it causes confusion (compound-engineering).
  The skill should welcome that path rather than require a complete glossary up front.

### 2.2 Surfacing and settling ambiguity with the human

- **Three kinds of clash**: one thing with several names, one name for several things, and a thing with no name
  (every source). Add a fourth: a name only the code or an agent uses.
- **Ask in rounds, with a recommendation the human can accept with "yes"** (mattpocock `grilling`), except when
  asking for the human's own word, where offering a name biases the answer (our rule). Use the host's question tool
  when there is one (chrislacey89).
- **Show the mismatch concretely**: "table `purchases`, type `Order`, button 'Basket': call all three an Order?"
  (specweave). The human judges a concrete clash faster than an abstract question.
- **Stress-test with an invented edge case**: "pays for 3 items, one ships late: one Order or two?" (mattpocock,
  specweave). Forces the boundary between two neighbouring terms and produces the `Not:` line.
- **Check the human's stated rules against the code, once.** If the code disagrees, raise it before writing the
  entry; if nothing enforces it, say so; never edit the glossary to match a bug (chrislacey89, mattpocock).
- **Park, don't force.** A clash the human cannot settle now goes in an open-questions section with where it
  occurs (EventStorming hotspot; CodeAlive `## Unresolved`).
- **Rename vs meaning change** (citypaul): if only the spelling moved, it is a rename; if the meaning moved, it is a
  model change and may split an entry.
- **The human may object** (Evans): treat a reluctant "ok" to an agent's name as weaker than the human's own word.

### 2.3 Glossary format and location

- **One `GLOSSARY.md` at the repository root** is the strongest convention (mattpocock since 1.3.0, specweave;
  mattpocock's rename from `CONTEXT.md` shows the cost of changing the name later). Split per area only when one
  word really means two things in two areas and the file is already lean (mattpocock `GLOSSARY-MAP.md`; Evans).
- **Entry**: name; one or two sentences on what it *is*; `Avoid:`; optionally `Not:` (nearest neighbour and the
  difference, CodeAlive); where it is stored when that name differs (our `Stored as`; specweave's Data/Code/UI); a
  marker for entries the human has not agreed (our `Proposed:`; citypaul's "visibly provisional").
- **Bold term with lines under it, not tables**: greppable, clean diffs (CodeAlive's argument; mattpocock's format).
- **Names and meanings only.** No decisions, specs, plans or implementation detail (mattpocock, compound-engineering,
  all their bug reports). Findings like code mismatches go in the chat report, not the file.
- **Only project-specific terms**; general programming words stay out (every source).
- **Optional sections**: open questions (unresolved clashes) and retired names. Keep both short.
- **Create lazily**, when the first term is agreed (mattpocock, specweave, compound-engineering).

### 2.4 Making later agents keep to it, and flagging drift

- **A pointer in the always-loaded instruction file**: one line in `AGENTS.md`, and `CLAUDE.md` if present, and
  `.cursor/rules` with `alwaysApply` for Cursor users (CodeAlive writes to every agent file it finds;
  compound-engineering checks discoverability after each change; specweave adds a "Shared language" section). Do
  not rely on the skill being loaded.
- **The pointer says what to do, not only where the file is**: use these names in code, plans, tests, tickets and
  chat; don't drift to `Avoid` words; if a needed concept is missing, either you are inventing language (reconsider)
  or there is a gap (add it as proposed) (mattpocock `domain.md`).
- **Put the names in briefs.** A subagent may not load the pointer; whoever writes a brief copies the relevant
  entries into it, word for word (mattpocock's design-it-twice line; survey §7).
- **Flag drift at the moment it happens**: when the human uses a word that disagrees with the glossary, ask then
  (mattpocock, compound-engineering). When the agent notices its own drift, correct it in the next message.
- **A mechanical check where the human wants one**: `git grep -n -i -w <avoided>` over docs (specweave's manual
  path), a repository test for a retired word (OpenSpec), or Vale substitution rules (terrylica). Exclude the
  glossary itself and records of the past. Say plainly when no check exists (citypaul).
- **Check stale stored names too**: a backticked code name in the glossary that no longer exists is drift in the
  other direction (specweave).
- **Rename stored names only as planned work** the human asked for: "Drift is work, not an edit" (specweave;
  citypaul for names other systems consume).
- **A repair tool for the human**: a short "say that again in the glossary's words" request (mattpocock
  `wait-what`) is cheap and worth mentioning in the skill's report.

### 2.5 When the skill should trigger, and when not

Trigger when: the human or agents use different words for one thing; a word means two things; the human says terms
are confusing or asks for a glossary, ubiquitous language or domain language; a project or feature is being shaped
before a plan and has more than a handful of concepts; an agent is about to introduce a name for a new concept that
users or other modules will see.

Do not trigger for: naming one local variable or function; general programming terms; a one-day build or a
throwaway script (mattpocock docs); writing a CLAUDE.md or style guide; tactical DDD design (aggregates, repositories)
— language work is useful without it (pedronauck). A file lookup ("what does X mean here?") needs no skill: read the
file. Keep the description free of "PROACTIVELY"/"ALWAYS" wording (CodeAlive's over-triggering).

---

## 3. Our current skill compared

`skills/orchestration/domain-language/SKILL.md`, read today.

### What it does that none of the sources do

- **Prefers the human's own word, then the explicit familiar name, even if longer**, and leaves good short names
  alone. Every other source optimises for precision only.
- **Asks for the human's word before proposing one**, and withholds suggestions in that message. The sources all
  propose and ask for confirmation, which our eval showed loses the human's vocabulary.
- **`Proposed:` per entry**, and the rule that an unmarked entry is read as the human's decision. Nobody else marks
  provenance per entry (CodeAlive marks the whole file; citypaul marks names in code).
- **The middle path for a new name while the human is away**: add it as proposed, report it, carry on. Others either
  stop (citypaul), add silently (CodeAlive, compound-engineering) or just note a gap (mattpocock).
- **`Stored as`**: a stored name stays, prose uses the agreed name and gives the stored one once. Only specweave
  comes close (Data/Code/UI), and it pushes toward renaming.
- **Code keeps its own word for consistency** (`createBooking` → `moveBooking`), and comments count as code.
- **A finished-test**: the main job written as numbered steps using only everyday words and glossary names, each
  step saying who does it, agreed by the human in chat. The steps double as the way to show names in use and to find
  missing ones. Evans's "scenarios out loud" is the nearest source.
- **Agent-coined labels** ("the sweep", "the shelf") named as the likeliest names to replace.
- **Records of the past are left as written** when a name changes; current documents are updated keeping every fact.
- **Fit the effort to the project**: five entries and no conversation for a small tool.
- **Names go in the chat message itself**, because the human may not open files.

### What it lacks

- **It is entangled with orchestrate**: `ORCHESTRATE.md`, the plans folder, `agent_loop.py adopt`, lead and planner
  roles, JSON check files. All must go.
- **No `Not:`-producing edge-case questions.** It has the `Not:` line but no technique to find the neighbour:
  the invented boundary scenario (mattpocock, specweave).
- **No behaviour check against code.** It checks names, not the rules the human states about them (chrislacey89,
  mattpocock).
- **No explicit harvest by level** (data, code, UI, docs), and no concrete "three names, call them all X?" question
  form (specweave).
- **No "name the unnamed" heuristics** beyond agent-coined labels: circumlocutions and procedural rules
  (chrislacey89).
- **No open-questions section** for a clash the human cannot settle yet (hotspot, CodeAlive `Unresolved`).
- **No life-cycle rules beyond "propose removing"**: no fold or retire with evidence (compound-engineering).
- **Pointer wording is thin**: "add one line that names the file" does not say what a later agent should *do*;
  mattpocock's `domain.md` wording does, and Cursor users need `.cursor/rules`.
- **No instruction to copy entries into briefs** for subagents.
- **No check for stale stored names** (a `Stored as` value that no longer exists in code).
- **No rounds-with-recommendation question protocol**, or use of the host's question tool. It says "a few at a time"
  only.
- **No statement of limits**: that it cannot confirm a word is the human's until the human uses it, and that a
  glossary may help humans more than agents (mattpocock's docs, pedronauck's honesty line).

---

## 4. Recommended outline for the new standalone skill

Target: one SKILL.md of roughly the current length, plus one reference file for the entry format and the drift check.
No dependency on any other skill. Written in house style (reasons, not rules; plain names; no failure stories).

**Frontmatter**
- `name: domain-language`
- `description`: Agrees one name for each thing in a project with the human, keeps the names in `GLOSSARY.md`, and
  keeps code, plans and chat using them. Use when people or agents use different words for one thing, one word for
  two things, the terms have become confusing, before planning a project with many concepts, or when asked for a
  glossary, ubiquitous language or domain language. Not for naming one variable, general programming terms, or a
  throwaway script.

**Body**

1. **What this is for** (short). Agents start with no memory; an unwritten name is reinvented slightly differently
   each session. The glossary is for the human to follow the work as much as for the agents.
2. **How much to do.** Fit to the project: five entries shown to the human for a small tool; nothing for a one-day
   job; the full conversation where human, plans and code already disagree.
3. **What finished looks like.** The main job written as numbered steps, each saying who does it, using only
   everyday words and glossary names; the human has agreed those steps in chat; unagreed entries are marked; current
   documents follow the names (with the grep check).
4. **Finding the names.**
   - Ask for the human's telling first: one concrete run through the main job, who does what with what.
   - Harvest the repository yourself, by level: data, code, UI text, docs. Facts are the agent's job.
   - Look for the four kinds of clash, unnamed concepts (circumlocutions, procedural rules), agent-coined labels,
     and steps and statuses as well as things.
5. **Settling them with the human.**
   - In rounds, names written into the message; use the host's question tool if there is one.
   - Where the human gave a word, it wins. Where they didn't, ask what they call it and suggest nothing in that
     message.
   - Concrete mismatch questions ("table X, type Y, button Z: call all three an Order?") with a recommendation.
   - Invented edge cases to find the boundary between neighbours (feeds `Not:`).
   - Check stated rules against the code once; raise disagreements; never write a rule the code contradicts without
     saying so.
   - Park what can't be settled in the open-questions section.
   - Show the names in use as numbered steps; the human's reply agrees what it shows, nothing more.
6. **Which name to choose.** Keep the current rules: human's word; explicit familiar name even if longer; known tool
   names; leave good short names; one thing one name; one name one thing; project-specific only.
7. **The glossary file.** `GLOSSARY.md` at the root (or where the project already keeps one). Entry: name, what it
   is, `Not:`, `Avoid:`, `Stored as:`, `Proposed:`. Optional `## Open questions` and `## Retired`. Names and
   meanings only. Created when the first name is agreed. Split by area only when one word truly means two things
   in two areas.
8. **Names already stored.** Unchanged from now: stored names stay, prose uses the agreed name and gives the stored
   one once, code keeps its own word for consistency, renaming storage is planned work the human asks for, and
   comments count as code.
9. **Keeping to it.**
   - Read it before writing a plan, design, user-facing text or report.
   - A new concept: look first; else add as `Proposed:`, use it, and report it.
   - When the human's word disagrees with the glossary, ask at that moment.
   - Changes to agreed names, removals and merges are the human's call; propose with a reason. Fold or retire only
     with evidence of where the concept went.
   - On a rename: old name to `Avoid`, records of the past left as written, current documents updated keeping every
     fact.
   - When writing a brief for another agent, copy the entries it needs into the brief.
10. **Making later sessions find it.** A short section in `AGENTS.md` (and `CLAUDE.md`, and `.cursor/rules` with
    `alwaysApply` if present) that says where the file is and what to do: use these names, don't use `Avoid` words,
    treat `Proposed:` entries as unconfirmed, add a missing concept as proposed. Report that you added it.
11. **Checking for drift.** The grep over current documents for each `Avoid` word, excluding the glossary and
    records of the past; and a check that each `Stored as` name still exists. Offer to make it a test only when the
    human wants a name kept out for good. Say plainly when no check is in place.
12. **Limits** (two or three lines). A name is the human's only once they have used or chosen it; the agent
    cannot facilitate a workshop or speak for absent experts; a glossary nobody reads helps nobody, so keep it short
    and prune it.

**Reference file** (`references/glossary-format.md`): a worked entry for each line type, an open question, a retired
entry, the `AGENTS.md` pointer text, and the drift-check commands.

**Evals to carry over and add**: keep `tangled-terms`, `new-name-mid-task`, `small-tool` (strip orchestrate
settings from them). Add one where the human's stated rule contradicts the code, and one where a later session with
only the `AGENTS.md` pointer (no skill) must keep to the names.
