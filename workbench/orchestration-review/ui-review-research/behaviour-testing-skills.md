# How popular agent skills test UI behaviour

Research for replacing the review-milestone method for user interfaces. Today the method in
`skills/orchestration/plan-module/references/proofs.md` ("How to inspect") was written for 2D and 3D graphics
(write the parts down before looking, view each from several angles). A recent project showed what it misses.
Each item was checked one way. The defects were in other ways of reaching the same thing: another entry point,
something already selected or open, or a request that failed or came back wrong.

Seen 2026-11-11. Install counts come from the skills.sh search API (`/api/search`) and the skill pages on that
date. Star counts come from the GitHub API on the same date. Every file was read over `gh api` or the web. Nothing
was installed or run.

Each skill has two parts. **What the text says** reports only what is written in the skill. **Inference** is my
judgement of how well it works. Evidence that a skill works, such as an eval or a write-up, is noted where it
exists.

---

## The landscape in one table

| Skill | Where | Popularity (2026-11-11) | Shape | Reads code? | Injects failures? |
|---|---|---|---|---|---|
| `agent-browser` → `dogfood` | vercel-labs/agent-browser | agent-browser 1.40M installs (rank 4 all-time); repo 49.5k stars. `dogfood` is served by the CLI (`agent-browser skills get dogfood`), so its own installs are not counted | Open exploration with a taxonomy checklist | **No, forbidden** | No |
| `webapp-testing` | anthropics/skills | 202k installs; repo 193k stars | Scripted Playwright mechanics | Only static HTML, for selectors | No |
| `playwright-cli` | microsoft/playwright-cli | 213k installs; repo 15k stars | Tool manual | n/a | Tool supports it (`route`); the skill does not say when to use it |
| `browser-testing-with-devtools` | addyosmani/agent-skills | 68k installs; repo 115k stars | Debugging workflows plus an example test plan | Yes, it is for building | No (diagnoses failures that occur) |
| `browser-qa` | affaan-m/ecc | 11k installs; repo 301k stars | Fixed four-phase checklist | No | No |
| `firecrawl-qa` | firecrawl/firecrawl-workflows | 31.6k installs; repo 222 stars | Report template, fan-out by area | No | No |
| `qa` / `qa-only` | garrytan/gstack | `qa` 491 skills.sh installs (most users install gstack through its own setup); repo 141k stars | Charters, then a hypothesis-logged probe loop | Diff to choose scope; **no source during browser discovery** | No |
| `ui-test` | browserbase/skills | 3.1k installs; repo 3.8k stars | Three written planning rounds, then assigned tests with a strict assertion protocol | Reads the diff | No |
| `ce-dogfood` | everyinc/compound-engineering-plugin | 913 installs (manual invocation only); repo 26k stars | Flow diagrams, then a matrix, then execution | Reads the full diff | Lists "server error … lost network" as a state to check |
| `playwright-interactive` | openai/skills | 5.7k installs; repo 28.7k stars | Inventory of claims and controls written first, then functional and visual passes | Its own implementation | No |
| `playwright-test-planner` (agent) | microsoft/playwright, Test Agents | Ships with Playwright ≥1.56 (repo 99.8k stars) | Explore, then write a test plan for a generator | Has Grep/Read tools | No |
| `exploratory-testing` | petrkindlmann/qa-skills | 1.8k installs; repo 262 stars | Classic session-based exploratory testing (charters, heuristics) | No | Lists it as a heuristic |
| `verification-before-completion` | obra/superpowers | 272k installs; repo 316k stars | Evidence rule, not UI-specific | n/a | n/a |
| `mo-qa`, `scoutqa-test` | momentic-ai/skills, github/awesome-copilot | 23k and 10k installs | Hand the job to a hosted QA agent | `mo-qa` sends the PR or a patch | Unknown (hosted) |

The skills.sh leaderboard top 30 has no QA or browser-testing skill apart from `agent-browser`. The skills that
teach *how to decide what to test* are less popular than the browser tools they run on. Most popular skills in
this space are tool manuals.

---

## Skills worth learning from

### 1. Every's `ce-dogfood`: flows first, then a matrix built from their branch points

Source: `skills/ce-dogfood/SKILL.md`, `references/phases.md`, `references/test-matrix-taxonomy.md`,
`references/dogfood-report-template.md` in everyinc/compound-engineering-plugin.

**What the text says.**
- It is "diff-scoped, not whole-app exploration". Phase 1 reads the full `git diff` against trunk and the product's
  persona documents.
- The phase order is fixed: "Scope -> analyze the diff -> map the flows -> derive the matrix -> serve -> execute ->
  fix loop -> report. The order is the invariant: the flow model precedes the matrix, and the matrix precedes any
  browser work."
- Phase 2a requires a Mermaid flowchart for every user-visible change, with the "entry point, each user action,
  branch points (success / validation error / empty / permission-denied), side effects (emails, jobs,
  notifications), and the true end state". It explains why: "A matrix built without a flow model tests pages in
  isolation and misses the journey."
- Phase 2b turns "every node and branch" of each flowchart into scenarios and loads them as a task list, one task
  per scenario, "ordered by flow … not by file".
- The taxonomy gives each journey five parts: **Entry** ("how does the user arrive? (link, redirect, notification,
  deep link)"), **Action**, **Result**, **Destination** ("the *right* item focused/scrolled into view, showing the
  *right* data") and **Aftermath** ("follow side effects to their real end state"). Its canonical example: "'an
  email sends' is not a pass."
- Edge states: empty; boundary; **Error** ("server error, validation failure, expired session, lost network —
  handled gracefully?"); **Concurrency / re-entry** ("double-submit, back button, refresh mid-flow, stale tab").
  Under cross-cutting it adds "Regression: adjacent journeys a change could plausibly have broken".
- A table maps changed files to routes. For example, a component maps to "every page that renders the component".
- Outside services (OAuth, email, payments) must go through the project's local stand-in first. A leg that no
  stand-in covers becomes `Blocked (needs human verify)`, and only when the branch changed that integration.
  "Note once … what the environment replaced and which claims that leaves unproven."
- Each scenario is judged twice: for correctness, and for "persona paper cuts" (small friction a functional test
  would not fail).
- Its evidence is a report built from a template and committed to the repo. It holds the flowcharts, a matrix row
  per scenario (Pass, Fixed, Skipped, or Blocked) with the commit SHA on each fix, root causes, and regression
  tests that "fail before … and pass after". The report is updated after every scenario, so a later run can
  resume from it.
- Tools: one browser, preferring the host's built-in browser over the `agent-browser` CLI. It never adds a third
  stack.

**Inference.** This skill comes closest to the defects we missed. Entry, destination and re-entry are the
dimensions that "another entry point" and "something already open" fall under. A flow diagram drawn from the diff
makes branch points visible before anyone looks at the screen. It also builds, fixes and commits, which a reviewer
must not do, so only its first half (diff → flows → matrix → drive → judge) carries over. Its error dimension is
one line. It does not say how to make a server error or lost network happen, so in practice those checks depend on
the agent's initiative. No eval of it was found.

### 2. Browserbase `ui-test`: three planning rounds, the second one adversarial

Source: `skills/ui-test/SKILL.md`, `references/adversarial-patterns.md`, `references/exploratory-testing.md`,
`README.md` in browserbase/skills.

**What the text says.**
- Its stance comes first: "Your job is to **try to break things**, not confirm they work."
- Before any browser work, the main agent must write three planning rounds in its own response:
  - Round 1, Functional: "action → expected result" for each core flow.
  - Round 2, Adversarial: "Re-read Round 1. What did you miss? Think about: different user types/roles, error paths,
    empty states, race conditions, edge inputs (empty, huge, special chars, rapid clicks)."
  - Round 3, Coverage gaps: accessibility, mobile, console, visual consistency.
  - The rounds are then deduplicated, numbered and grouped.
- Execution is delegated. "Sub-agents run assigned tests, not open exploration", each with an explicit step budget.
  When a sub-agent runs out of budget, the tests it did not reach are reported as `STEP_SKIP|<id>|budget reached`.
  They are never dropped.
- Assertion protocol: each step emits `STEP_PASS|<id>|<evidence>` or `STEP_FAIL|<id>|<expected> → <actual>|<screenshot>`.
  "Do not write freeform 'this looks good.'" Evidence is ranked from strongest to weakest: a deterministic `eval`
  result, a specific element in the accessibility tree, a before/after snapshot diff, and last a screenshot judged
  by eye.
- Every interaction follows the same loop: "snapshot, act, snapshot, compare".
- In the diff-driven workflow, a file-pattern table says what to test. For example, `*modal*`, `*dialog*` means
  "Open/close, escape, focus trap, cancel vs confirm". The skill also checks that the dev server is "serving the
  code from the diff — not a stale branch".
- The adversarial reference runs the full lifecycle of a modal: open, Escape, re-open and cancel, re-open and
  confirm, then check that the side effect occurred. Under error states it asks: "is the user's input preserved?
  Or was the form cleared?" The exploratory reference adds state persistence: "Fill a form halfway, navigate away,
  come back", "Create an item, refresh", and "expired session".
- Evidence: a screenshot of every failure taken "at the moment of failure", and a self-contained HTML report with
  failures first.

**Inference.** Round 2 is the cheapest fix for a reviewer that checks each item one way. It forces a second written
pass whose only question is "what did you miss?". The assertion protocol suits a reviewer, because a pass needs
named evidence. The weakness is that Round 2's prompts are generic categories, so the agent fills them with
generic ideas (XSS strings, 500 characters) more readily than with the app's own second entry point. It never
injects a failed or malformed response either. The only evidence that it works is the PR that added it
(browserbase/skills#56). The author reports that a smoke test against a Next.js app found that Escape did not close
modals and that touch targets were too small. That is an author anecdote, not an eval.

### 3. gstack `/qa`: a charter per behaviour and a hypothesis before every probe

Source: `qa/SKILL.md`, `qa/sections/exploratory.md`, `qa/sections/qa-patterns.md`, `qa/sections/scope.md`,
`qa/references/issue-taxonomy.md`, and `test/fixtures/qa-eval-*-ground-truth.json` in garrytan/gstack (qa/SKILL.md
last changed 2026-11-07).

**What the text says.**
- Scope comes first. On a feature branch the run is "diff-aware testing of changed and adjacent behavior". The
  agent maps changed controllers, routes, views and components to pages, and reads the commit or PR intent.
- Next it writes a **charter per behaviour**: "contract, risk, entrypoint, isolation, exit condition, source,
  commands and inputs". Every probe is checked against that charter.
- The stopping rule is about coverage, not time alone: "each field's documented input rule needs a probe that
  breaks only it and satisfies every other rule". Rules still uncovered when time runs out "go in limits". There
  are also time and probe caps (a 3-minute quick mode, a 15-minute full mode, and 5 minutes or 12 probes when
  called from review).
- The probe loop: first "demonstrate success: output AND durable effects". Before each next probe, publish a
  checkpoint file with the last command, its exact observed output, the **hypothesis** ("why nextCommand") and the
  next command. "Never batch probes." A failure must be replayed exactly "from the same initial fixture state"
  before it is reported: "Another input or a regression test is not that replay." After any fix, "every earlier
  capture is superseded" until it is rerun.
- "Missing prerequisites/expectations/observations, timeouts and refusal never pass."
- The browser technique pages (Phases 3–6, shared ancestry with Vercel's dogfood) cover several things. An injected
  hook records `console.error`, uncaught errors and unhandled promise rejections. Same-origin links get a HEAD
  check. Each page is explored for "empty/loading/error/overflow states". Under SPA guidance: "stale state on
  return, back/forward history". Next.js guidance includes "link-click routing (not just `goto`)", which is
  literally a second entry point.
- "**Never read source code during browser discovery.**" The diff chooses scope, but discovery is black-box.
- Evidence: a numbered issue list with step screenshots, a weighted health score, `baseline.json` for regression
  comparison, and per-probe checkpoint JSON.
- The skill is tested. gstack ships planted-bug fixtures with ground truth (a static page, an SPA and a checkout
  page, five bugs each). Among them: "Cart count persists across route changes", "Product list briefly loads then
  shows 'Error: Failed to fetch products'", and "Clearing the quantity field shows 'Total: $NaN'". The pass bar is
  `minimum_detection: 2` of 5.

**Inference.** The charter's **entrypoint** field and the "break only one rule at a time" rule are the two ideas
most worth borrowing. The hypothesis-before-probe log is the strongest guard I found against an agent that ticks
items off without thinking, but it is heavy (sentinel files, deadline guard binaries). The planted-bug eval is the
best evidence pattern in this space. Its bar (2 of 5) suggests that even this skill misses more than it finds, so
its existence is reassuring and its threshold is not. The charter has an entrypoint field but no rule that a
behaviour reachable from several entry points needs one probe per entry point.

### 4. OpenAI `playwright-interactive`: an inventory of claims × controls × states, written first

Source: `skills/.curated/playwright-interactive/SKILL.md` in openai/skills.

**What the text says.**
- Step 1 is "Write a brief QA inventory before testing", built "from three sources: the user's requested
  requirements, the user-visible features or behaviors you actually implemented, and the claims you expect to make
  in the final response." "Anything that appears in any of those three sources must map to at least one QA check
  before signoff."
- It lists "every meaningful user-facing control, mode switch, or implemented interactive behavior" and "the state
  changes or view changes each control … can cause". The checks are then keyed by "claim or control-state pair".
- "Add at least 2 exploratory or off-happy-path scenarios that could expose fragile behavior."
- For reversible controls: "test the full cycle: initial state, changed state, and return to the initial state."
- "`page.evaluate(...)` … may inspect or stage state, but they do not count as signoff input." Sign-off needs real
  input.
- After the scripted checks, "a short exploratory pass using normal input for 30-90 seconds". Anything new it finds
  goes back into the inventory.
- The sign-off section requires explicit coverage against the inventory, "call out any intentional exclusions", and
  "a brief negative confirmation of the main defect classes you checked for and did not find."

**Inference.** This is closest to what orchestrate does now, with a list written before looking. It is more
behavioural: control × state pairs, the full cycle of a toggle, and real input only. It shows that a list made in
advance is not itself the problem. The problem is what the list enumerates. A list of parts or controls tested one
way each will miss alternate routes. A list of control-state pairs that includes "return to the initial state" will
catch some of what we missed. It says nothing about network failure or about other entry points. No eval was found.

### 5. Vercel `dogfood`: the most-installed route, open exploration with repro-first evidence

Source: `skill-data/dogfood/SKILL.md`, `references/issue-taxonomy.md` in vercel-labs/agent-browser.

**What the text says.**
- "You are not following a test script -- you are exploring like a real user would." The run follows the main
  navigation, visits each section, and tests "interactive elements: click buttons, fill forms, open
  dropdowns/modals". It checks "edge cases: empty states, error handling, boundary inputs" and "realistic end-to-end
  workflows (create, edit, delete flows)".
- "If you find a cluster of issues in one area, investigate deeper."
- "**Never read the target app's source code.** … All findings must come from what you observe in the browser."
- Repro first: "verify the issue is reproducible with at least one retry". Interactive bugs get a video and a
  screenshot per step. Static bugs get one annotated screenshot. Each issue is appended to the report as soon as it
  is found.
- "Aim to find **5-10 well-documented issues**, then wrap up."
- The taxonomy's per-page checklist covers interactive elements, forms, navigation ("Breadcrumbs, back button, deep
  links"), states ("empty state, loading state, error state, full/overflow state"), console and responsiveness.
  Under Functional it lists "State not persisting (data lost on refresh, back button)" and "Race conditions
  (double-submit, stale data)".

**Inference.** Reach matters here. `agent-browser` (1.4M installs) tells agents to load `dogfood` for "exploratory
testing, dogfooding, QA, bug hunts". So this is the default QA method for a large share of agents. It suits a bug
bash and does not suit a reviewer. It is page-by-page, it stops at 5–10 issues rather than at coverage, it forbids
reading the code that would reveal the other entry points, and it finds errors only when they happen naturally. The
two good habits to keep are the retry before reporting and the evidence chosen per kind of issue.

---

## Thinner skills, and what each adds

- **Anthropic `webapp-testing`** (202k). It is entirely mechanics: a server helper, wait for `networkidle`, and
  "Reconnaissance-Then-Action" (screenshot or DOM, then selectors, then act). It does not say what to test,
  which states to try, or how to handle failures. It is popular because it is Anthropic's and it makes Playwright
  usable, not because of any testing method.
- **addyosmani `browser-testing-with-devtools`** (68k). It is mainly a debugging workflow, but its example test plan
  is a good shape. Each step has an expected result plus a console check and a **network check** naming the
  request and payload ("Network should show PATCH /api/tasks/:id with { status: \"completed\" }"). It also includes
  "Rapidly toggle the same task 5 times … final state is consistent". The skill has an eval, and that eval checks
  that "Findings are grounded in observed runtime data … not static code reading alone" and that "The report
  distinguishes what was observed from what is inferred".
- **ECC `browser-qa`** (11k, a 301k-star repo). It is a fixed checklist (smoke, interaction, visual regression,
  accessibility) ending in a SHIP, SHIP WITH FIXES or DO NOT SHIP verdict. One rule is worth keeping: "no baseline ⇒
  report INCONCLUSIVE, never a silent PASS".
- **Playwright `playwright-test-planner`**. It explores, then writes scenarios covering "Happy path …, Edge cases and
  boundary conditions, Error handling and validation". Each scenario states its starting state ("always assume
  blank/fresh state") and must be independent. That fresh-state assumption is exactly what hides defects that need
  something already selected or open. Practitioner write-ups found no published metrics.
- **petrkindlmann `exploratory-testing`** (1.8k). Classic session-based test management (Bach) brought to agents:
  charters ("Explore [target] with [resources] to discover [information]"), HICCUPS oracles, and time-boxes. Its
  state-transition list matches our missed defects most directly: "skip a step? (Direct URL to step 3 of a
  wizard)", "go backward?", "interrupt? (Close tab mid-operation, lose network)", "repeat? (Double-click submit,
  refresh during save)", "What is the state after an error? (Can you retry? Is data corrupted?)". Its error list
  includes "Send malformed API responses (modify with browser DevTools)" and "Trigger server errors". It is the only
  skill that tells the agent to *cause* a bad response. Low installs.
- **Microsoft `playwright-cli`** (213k). It has nothing on method, but `references/request-mocking.md` documents
  `route "**/api/users" --status=…`, `--body=…`, response modification and simulated network failures. It is the
  tool for the gap the method skills leave.
- **firecrawl-qa, mo-qa, scoutqa-test.** These are either thin (a report template plus fan-out by area) or hand the
  work to a hosted agent. One sentence in `mo-qa`'s brief guidance cuts the other way. It warns that prescribing
  "happy path, failure cases, edge cases, and page reloads for every flow … can lower Mo's results". That is a
  vendor's claim about its own agent, with no evidence given.
- **superpowers `verification-before-completion`** (272k). It is not about UI, but its gate ("NO COMPLETION CLAIMS
  WITHOUT FRESH VERIFICATION EVIDENCE") is what the assertion protocols above put into practice.

---

## What the best of them have in common

1. **Write the plan before touching the browser, and build it from behaviour, not from parts.** ce-dogfood draws
   flows, ui-test writes three rounds, gstack writes charters, and playwright-interactive lists claim × control ×
   state pairs. None of them enumerates parts to look at. Each enumerates *ways a user moves through the thing* and
   the states along the way.
2. **A second, adversarial pass over the plan.** ui-test's Round 2 ("What did you miss?"), playwright-interactive's
   "at least 2 off-happy-path scenarios" plus a free exploratory pass, and dogfood's "investigate deeper" where
   issues cluster.
3. **Re-entry and prior state are named explicitly.** These include back button, refresh mid-flow, stale tab,
   double-submit, re-open then cancel then confirm, the full toggle cycle, and "stale state on return". This is the
   "something already open" class.
4. **A pass needs evidence, and a failure is replayed before it is reported.** The forms differ: STEP_PASS with
   named evidence (ui-test), success shown by output and durable effects with exact replay from the same fixture
   (gstack), a retry before any report (dogfood), and "never a silent PASS" (ECC).
5. **The diff chooses scope.** ce-dogfood, ui-test and gstack all map changed files to the routes and components
   that render them, and add "adjacent" journeys.
6. **Console and failed requests are watched throughout**, by hooking `console.error`, uncaught errors and
   unhandled rejections, and by reading the network log.

## Where they differ

- **Reading the code.** Vercel dogfood and gstack's browser discovery forbid reading source and want a user's-eye
  view. ce-dogfood, ui-test and gstack's scope step read the diff. None reads the code to *enumerate entry points or
  request sites*. That is the step that would have caught our missed defects, and nobody does it (see below).
- **Script vs exploration.** ui-test hands sub-agents a fixed list and forbids exploring. dogfood and Browserbase's
  Workflow B are open roaming. ce-dogfood and gstack sit between them, with a fixed matrix or charter and freedom
  inside each item. playwright-interactive runs a fixed inventory, then a timed free pass.
- **When to stop.** Some stop at a count (dogfood, 5–10 issues), some at a time box (gstack modes, SBTM's 45–90
  minutes, mo-qa effort levels), and some at full coverage of the plan (ce-dogfood, playwright-interactive, gstack's
  "each documented input rule"). Only the coverage rule fits a reviewer.
- **Failure injection.** It is almost absent. Every popular skill *observes* errors that happen on their own.
  Causing a failed, slow or malformed response is mentioned in one line in ce-dogfood ("server error … lost
  network") and in petrkindlmann's heuristics. It is possible with `playwright-cli route`, but no method skill
  connects the two.
- **Weight.** It ranges from a one-page checklist (ECC) to a multi-file protocol with guard binaries (gstack).

## Inference for orchestrate's reviewer (my judgement, not in any skill)

The three defect classes map onto the literature unevenly.

- **Another entry point.** It is covered only as one field (gstack's charter "entrypoint") or one journey dimension
  (ce-dogfood's "Entry … link, redirect, notification, deep link"). No skill requires probing *each* entry point to
  the same behaviour. A reviewer that has the code can do better than every black-box skill here. Grep for every
  caller, route, menu item, shortcut and deep link that reaches the changed behaviour, and make each one a row.
- **Something already selected or open.** It is well covered as named heuristics: re-entry, the full toggle cycle,
  re-open then cancel then confirm, stale state, and skipping a step. The skills that put these into the plan
  itself (ce-dogfood's matrix, playwright-interactive's control-state pairs) are more reliable than those that leave
  them to a per-page checklist.
- **A request that failed or came back wrong.** This is a gap in the popular skills. The tooling exists
  (`page.route`, `playwright-cli route --status/--body`). A reviewer method would need to require, for each request
  the behaviour makes, a run where it fails, a run where it is slow, and a run where it returns an unexpected shape,
  and to check what the screen and the saved state do next.

A method that fits review-milestone would combine these pieces in order:

1. ce-dogfood's flow-from-diff step, with entry points taken from the code rather than guessed.
2. A matrix whose rows are entry point × prior state × response outcome.
3. ui-test's written adversarial second round.
4. ui-test's or gstack's evidence rule for every pass, plus gstack's exact replay for every failure.
5. A short free exploratory pass at the end, as in playwright-interactive.

Planted-bug fixtures, as gstack uses, would be the way to test whether the new method catches the three classes.

## Sources

- skills.sh leaderboard and search API: https://skills.sh, https://skills.sh/api/search?q=qa (and `e2e`, `playwright`, `exploratory`, `dogfood`, `browser testing`)
- https://github.com/vercel-labs/agent-browser/blob/main/skill-data/dogfood/SKILL.md and `references/issue-taxonomy.md`; https://github.com/vercel-labs/agent-browser/blob/main/skills/agent-browser/SKILL.md
- https://github.com/anthropics/skills/blob/main/skills/webapp-testing/SKILL.md
- https://github.com/garrytan/gstack/tree/main/qa (SKILL.md, sections/exploratory.md, sections/qa-patterns.md, sections/scope.md, references/issue-taxonomy.md); https://github.com/garrytan/gstack/tree/main/test/fixtures (qa-eval-*-ground-truth.json)
- https://github.com/browserbase/skills/tree/main/skills/ui-test (SKILL.md, references/adversarial-patterns.md, references/exploratory-testing.md, README.md); PR #56 description via search result
- https://github.com/everyinc/compound-engineering-plugin/tree/main/skills/ce-dogfood (SKILL.md, references/phases.md, references/test-matrix-taxonomy.md)
- https://github.com/openai/skills/blob/main/skills/.curated/playwright-interactive/SKILL.md
- https://github.com/microsoft/playwright/blob/main/examples/todomvc/.claude/agents/playwright-test-planner.md; packages/playwright/src/agents/playwright-test-coverage.prompt.md
- https://github.com/microsoft/playwright-cli/tree/main/skills/playwright-cli (SKILL.md, references/request-mocking.md)
- https://github.com/addyosmani/agent-skills/blob/main/skills/browser-testing-with-devtools/SKILL.md; evals/cases/browser-testing-with-devtools.json
- https://github.com/affaan-m/ecc/blob/main/skills/browser-qa/SKILL.md
- https://github.com/firecrawl/firecrawl-workflows/blob/main/skills/firecrawl-qa/SKILL.md
- https://github.com/momentic-ai/skills/tree/main/claude/skills/mo-qa (SKILL.md, references/brief.md, references/source-context.md)
- https://github.com/github/awesome-copilot/blob/main/skills/scoutqa-test/SKILL.md
- https://github.com/petrkindlmann/qa-skills/tree/main/skills/exploratory-testing (SKILL.md, references/heuristics-and-automation.md)
- https://github.com/obra/superpowers/blob/main/skills/verification-before-completion/SKILL.md
- Practitioner write-ups on Playwright Test Agents (no metrics): https://dev.to/valentijngit/i-tested-playwrights-new-ai-agents-against-ai-native-testing-platforms-heres-what-i-found-3lm6, https://dev.classmethod.jp/en/articles/claude-code-playwright-test-agents/
