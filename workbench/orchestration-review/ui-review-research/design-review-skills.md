# How popular agent skills review a user interface's design

Research for replacing the graphics-inspection method (`plan-module/references/proofs.md`, rows "2D image" and "3D asset", and "How to inspect") that orchestrate's reviewer uses today when the milestone is a web interface.

Seen on 11 November 2026. All skill text was read from the repositories over `gh` or a shallow clone into a scratch folder. Nothing was installed and no script was run. Popularity figures come from skills.sh pages and the GitHub API on that date. skills.sh shows rounded figures and does not say whether they are all-time counts.

Scope: skills that review or audit a UI's design, usability, accessibility or consistency. Skills that only test behaviour are left to the other researcher. The exceptions are gstack's `design-review` and OpenAI's `playwright-interactive`, which do both.

Text in quotation marks is copied from the skill. Anything under "Assessment" is my inference and is not in the skill.

---

## 1. What is popular

| Skill | Source | Popularity (11 Nov 2026) | Kind |
|---|---|---|---|
| `web-design-guidelines` | vercel-labs/agent-skills | 848.6K installs, rank ~62 on skills.sh. Repo has 33.9K stars | Rule checklist applied to code |
| `impeccable` (with `critique`, `audit`, `polish`) | pbakaus/impeccable | 400.0K installs for the main skill. The standalone `critique` has 82.6K, `audit` 81.9K and `polish` 85.2K. Repo has 107.8K stars | Heuristic rubric, personas, deterministic detector and browser |
| `design-review`, `plan-design-review` | garrytan/gstack | 141.1K stars. skills.sh shows only 590 and 516 installs, but gstack is installed by git clone, so skills.sh undercounts it | Checklist, letter grades, browser, then a fix loop |
| `design-review` agent and slash command | OneRedOak/claude-code-workflows | 3.9K stars. Copied widely: ui-ux-pro-max ships a near copy as `stack/.claude/agents/design-review.md` | Phased live-browser review with a triage matrix |
| `accessibility` and `web-quality-audit` | addyosmani/web-quality-skills | 69.2K and 36.4K installs. Repo has 3.1K stars | WCAG 2.2 guide with a Lighthouse-first workflow |
| `design-critique` and `accessibility-review` | anthropics/knowledge-work-plugins (design plugin) | 5.9K and 4.4K installs. Repo has 35.4K stars | Short critique framework and WCAG quick reference |
| `accessibility-audit` | accesslint/skills | 1.3K installs. Repo has 120 stars | WCAG-EM audit that grades evidence |
| `review-animations`, `emil-design-eng`, `break-ui` | emilkowalski/skills | 298.9K installs for review-animations and 437.0K for emil-design-eng. Repo has 55.9K stars | Motion standards with an approve or block verdict |
| `playwright-interactive` | openai/skills (curated Codex skills) | 28.7K stars for the repo. No skills.sh figure | Functional QA plus a separate visual QA pass, with signoff |

The ones I checked that are not review skills:

- **Anthropic's `frontend-design`** (anthropics/skills, 1.1M installs) is a build skill. Its only review content is "Critique your own work as you build, taking screenshots to review if your environment supports it". `anthropics/claude-plugins-official` has no design-review plugin, only `frontend-design`.
- **`ui-ux-pro-max`** (445.5K installs, 148K stars) is a searchable design-rule database with a priority table of ten rule categories. Its review content is that table and a pre-delivery checklist for native apps.
- **`design-taste-frontend`** (leonxlnx/taste-skill) is a build skill. It absorbed the retired `redesign-existing-projects` in version 2.1.1. It does contain an automated "finish gate", described in section 3.
- **`design-mobile-apps`, `ui-taste` and `uizze-ui`** are top-20 on skills.sh, but all three generate designs.

Below the leaders, skills.sh holds many small accessibility-audit skills, each with under 1K installs. accesslint is the only one with a method worth learning from.

---

## 2. The skills worth learning from, one by one

### 2.1 Vercel `web-design-guidelines`

- **What it tells the agent:** The SKILL.md body is about 150 words. It tells the agent to fetch fresh rules on every run from `raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md`, read the files it was given, and "Check against all rules in the fetched guidelines". The fetched file is about 190 lines of terse rules in 17 groups: Accessibility, Focus States, Forms, Animation, Typography, Content Handling, Images, Performance, Navigation & State, Touch & Interaction, Safe Areas, Dark Mode, Locale, Hydration, Hover, Content & Copy, and Anti-patterns.
- **Method:** A checklist, applied as static analysis of source code. It never renders the page.
- **Tools:** WebFetch and file reads. It needs no browser, screenshots or viewport sizes.
- **What it looks at:** Only the files the user names. "If no files specified, ask the user which files to review."
- **What counts as a defect:** Any rule broken. Examples are `outline-none` with no replacement focus style, an icon button with no `aria-label`, `transition: all`, `...` written instead of `…`, and a date format hardcoded instead of using `Intl.*`. It assigns no severity.
- **Evidence:** One line per finding in `file:line` form, grouped by file, with `✓ pass` for a clean file. "State issue + location. Skip explanation unless fix non-obvious. No preamble."
- **Assessment:** It is the most-installed review skill by far, probably because it is cheap, fast and specific. But it judges the code, not what the user sees. It cannot catch hierarchy, layout, contrast as rendered, or a broken mobile layout. Fetching its rules at run time means a change upstream changes the reviewer without notice. skills.sh's Socket audit shows "Warn" for it.

### 2.2 Impeccable `critique`, `audit` and the finish reviewer (pbakaus)

This is the most developed design-review method in the popular set. It has two evaluation commands that are kept deliberately apart.

**`critique`** is a UX review. Its reference file is about 7,400 words.

- **Independent assessments:** It runs "two independent assessments". Assessment A is an LLM design review. Assessment B is a deterministic detector plus browser evidence. They "MUST run as two isolated sub-agents" and "must not see each other's output", because "Detector output is deterministic, but it still anchors judgment." If they run in one context, the report must open with `⚠️ DEGRADED: single-context (<reason>)`, since "A silent degraded critique is a failed critique."
- **Assessment A:** The reviewer "think[s] like a design director". It reads source and looks at the live page. In order, it covers:
  - a **design-specificity verdict**, made first, before any detector output: could an unrelated product use this design unchanged?
  - holistic design
  - an 8-item **cognitive-load checklist**, where a decision point with more than 4 visible options is flagged
  - the emotional journey (peak-end rule)
  - **Nielsen's 10 heuristics, scored 0–4** against a written per-score rubric. "Be honest with scores. A 4 means genuinely excellent. Most real interfaces score 20-32 out of 40." A heuristic that cannot apply is scored `n/a` and the total is renormalised.
- **Personas:** The reviewer takes 2–3 of five fixed personas and walks the primary action as each one. The personas are Alex, an impatient power user; Jordan, a confused first-timer; Sam, who depends on accessibility tools; Riley, a stress tester; and Casey, a distracted mobile user. A table picks personas by interface type: "Dashboard / admin → Alex, Sam". The instruction is "Name the exact elements and interactions that fail each persona. Don't write generic persona descriptions; write what broke for them."
- **Assessment B:** It runs `impeccable detect --json` (62 deterministic rules) on the source. For a viewable page it also injects the detector into a fresh browser tab, on "3-5 representative pages" for a multi-view target.
- **Synthesis:** "Do not simply concatenate". The report notes where the review and the detector agree, what the detector caught that the review missed, and which detector findings are false positives.
- **Severity:** P0 Blocking ("Prevents task completion entirely"), P1 Major, P2 Minor ("workaround exists") and P3 Polish. The tie-breaker is: "Would a user contact support about this?" If yes, the issue is at least P1.
- **Output:** In order: a method header, the heuristic table with a total and rating band, the specificity verdict, an overall impression, 2–3 strengths, **3–5 priority issues** (each with what, why it matters, fix, and suggested command), persona red flags, minor observations, and questions. The report is saved under `.impeccable/critique/` with a score trend across the last 5 runs. "Prioritize ruthlessly. If everything is important, nothing is."

**`audit`** is a technical check. Its reference file is about 1,600 words.

- **What it checks:** "Check what's measurable and verifiable in the implementation." It does not fix anything. It covers five dimensions, each scored 0–4 with written anchors: Accessibility, Performance, Theming, Responsive Design, and Implementation Integrity (the detector).
- **Severity:** P0–P3 again, with P1 defined to include "WCAG AA violation".
- **Evidence:** Each finding records Location, Category, Impact, the WCAG standard broken, a recommendation and a command.
- **Touch gestures:** The rule for these is careful: "a rendered viewport proves layout, not the gesture". The report must state what produced the evidence and what stayed untested.
- **Other rules:** It flags systemic patterns separately, and says "Keep P3s few: a long tail of minor issues buries the ones that matter."

**`impeccable-finish-reviewer`** is a subagent. It is the nearest analogue to orchestrate's reviewer.

- **Inputs:** It works with no browser ("Never render, screenshot, start a server"). It judges captures the parent made.
- **Check 0, evidence:** It first checks that the required captures exist and are valid, for example `desktop.png` and `mobile.png` with no blank regions and content that matches the filename. "a viewport nobody captured is a viewport nobody inspected, and it cannot ship". If any capture fails, the disposition is `recapture` and the review stops.
- **Anchoring:** It inventories the approved mockup's elements in its own words "before reading the direction contract or any builder-authored summary". It then classifies every salient element as match, acceptable adaptation, missing, contradicted, or added without approval. Rows for TYPE, MATERIAL and GROUND are mandatory.
- **Verdict:** Four derived dispositions, `recapture`, `rebuild`, `fix` and `ship`: "The word is derived, never felt." It calibrates against the bar, "never against the effort visible in the build". Its fix list holds at most eight items.
- **Verdict pass:** On re-review it scores each earlier fix as resolved, partial or unresolved, and reports at most three regressions: "The parent's narration of what was fixed is not evidence".

- **Evidence that it works:** The README carries a before-and-after comparison ("Same model (Fable 5.1), same brief") and a linked case study. The test suite covers the detector, the CLI and the browser tooling, not the quality of the critique. There is no published evaluation of critique accuracy.
- **Assessment:** Splitting `critique` (judgement) from `audit` (measurement), and keeping the detector away from the judge until the judge has finished, are the two ideas most worth copying. Much of the length is product bookkeeping (snapshots, trends, slash-command routing) that orchestrate would not need.

### 2.3 gstack `design-review` (Garry Tan)

It is "Design Audit → Fix → Verify". The SKILL.md runs to about 12,000 words, with sections loaded on demand.

- **Posture:** "You are a senior product designer AND a frontend engineer. Review live sites". It grounds user behaviour in Krug: "they scan, they don't read, so each screen is a billboard with one obvious next step".
- **What it looks at:** It sets depth by mode. Quick covers the homepage plus 2 pages, Standard 5–8 pages, and Deep 10–15. Diff-aware mode maps the branch diff to the affected routes and audits only those. Regression mode compares against a stored `design-baseline.json`.
- **Phases:**
  1. **First Impression** comes before any analysis. The agent takes a full-page screenshot, then writes "The site communicates…", "I notice…", "The first 3 things my eye goes to are…" ("If not, the visual hierarchy is lying") and a one-word verdict, plus a **Page Area Test** (name every area's purpose within 2 seconds).
  2. **Design System Extraction** runs scripts in the page to gather fonts, colours, the heading scale, touch targets under 44px, and navigation timing. It flags more than 3 font families, more than 12 non-grey colours, and skipped heading levels. It extracts what is rendered, "not what a DESIGN.md says".
  3. **Page-by-page audit** takes an accessibility snapshot of the interactive elements, an annotated screenshot and the console errors. It captures **mobile 375, tablet 768 and desktop 1440**. It runs a **Trunk Test** on every page: what site is this, what page, what are the sections, what are the options, where am I, and how do I search? Three or fewer of the six is a high-impact fail "however polished the page looks". It then works through a **10-category, ~80-item checklist**: hierarchy, typography, colour and contrast, spacing, interaction states, responsive, motion, microcopy, "AI slop" (named template patterns), and performance as design.
  4. **Interaction Flow Review** walks 2–3 key flows, snapshot-diffing the page before and after each action. It keeps a **Goodwill Reservoir** meter starting at 70, with listed drains (for example "interstitials … −15") and fills.
  5. **Cross-Page Consistency** checks the navigation bar, footer, component reuse, tone and spacing rhythm across pages.
  6. **Report.** Each category starts at grade A. Each high-impact finding drops it one letter and each medium finding drops it half a letter. Polish findings do not affect the grade. The weighted categories give a Design Score, and the AI-slop grade is reported as a separate headline.
- **Classifying the surface first:** "name the mode before you judge a pixel". The modes are PERSUADE (marketing), OPERATE (app UI), READ (docs), EXPERIENCE (portfolio) and HYBRID, which is classified per section. Each mode has its own rules. Seven litmus yes/no checks (for example "Page understandable by scanning headlines only?") are used to score agreement between models.
- **Rules:** "Screenshots are evidence. Every finding needs at least one". "Never read source code. Evaluate the rendered site, not the implementation." "Be specific and actionable: 'change X to Y because Z', never 'the spacing feels off.'" "Depth over breadth: 5-10 well-documented findings beat 20 vague ones." "Think like a designer, not a QA engineer."
- **Outside voice:** An optional second model (Codex) reviews independently, the two reviews are synthesised, and the agent then moves to triage and a fix loop.
- **`plan-design-review`** applies the same principles to a plan before anything is built. It rates each design dimension 0–10 and says "explain WHAT would make it a 10". Its principles include "Empty states are features" and "Trace every judgment to a broken principle; never 'this feels off' without one."
- **Evidence that it works:** gstack has a very large test directory (1,485 files). The design tests I found check the deterministic detector against fixtures with planted defects, "checked by id, grade and line". They do not evaluate the reviewer's judgement.
- **Assessment:** It has the richest set of *observation prompts*: first impression, page areas, trunk test and goodwill. Those force the agent to look at the rendered screen and say concrete things. The checklist values are opinionated house style (a type-scale ratio, a banned-fonts list), not standards.

### 2.4 OneRedOak `design-review` agent (Patrick Ellis)

It is short, at about 700 words, and it is the template many others copy.

- **Principle:** "Live Environment First": assess the interactive experience before any static analysis or code.
- **Phases:**
  - 0, Preparation: read the PR and the diff, open a Playwright preview at 1440×900.
  - 1, Interaction: run the primary flow and check hover, active and disabled states.
  - 2, Responsiveness: check 1440, 768 and 375, with "no horizontal scrolling or element overlap".
  - 3, Visual polish.
  - 4, Accessibility (WCAG 2.1 AA): tab order, focus, Enter/Space, contrast 4.5:1.
  - 5, Robustness: invalid input, overflowing content, and loading, empty and error states.
  - 6, Code health: component reuse and design tokens.
  - 7, Content and console.
- **Severity:** A "Triage Matrix" with four levels: `[Blocker]`, `[High-Priority]` (fix before merge), `[Medium-Priority]` (follow-up), and `[Nitpick]` with a "Nit:" prefix.
- **Communication:** "Problems Over Prescriptions". Instead of "Change margin to 16px", say "The spacing feels inconsistent with adjacent elements". Use screenshots for visual issues, and "always start with positive acknowledgment".
- **Standard:** A project-supplied principles file. The example is a 1,400-word "S-Tier SaaS Dashboard Design Checklist" that `CLAUDE.md` points to.
- **The ui-ux-pro-max copy** adds 1024 and 1920 viewports and a **Verdict** of "Ship / Ship with fixes / Needs work". It also adds "Every finding is backed by something you saw (a screenshot, a console message, a measured value), never by assumption", "Read code only to explain a defect you already observed", and "Distinguish 'broken' from 'I'd prefer.' Only Blockers/High should gate merging."
- **Assessment:** It is a clean and portable skeleton, and its spread suggests people find it usable. It is thin on *how* to judge visual quality: "Assess layout alignment and spacing consistency" is the whole instruction.

### 2.5 accesslint `accessibility-audit`

It has low popularity but the most rigorous evidence model of any skill read.

- **Method:** WCAG-EM, done in order: Scope, Explore (routes, templates, stateful UI), **Sample**, Evaluate and Report. The sample is "a structured set (entry page, each key flow end to end, every page with a new template or complex widget, and the important states) and a small random set. Say what's in each and why."
- **Two tiers:** An automated tier (a rule engine) and a "semi-automated manual tier" (keyboard, focus, state, reflow), with "dedup by SC ownership before driving, not after". Each sampled page goes to its own subagent.
- **Two separate grades per finding:**
  - **Evidence basis:** "● verified (deterministic, with cited proof) · ◐ flagged (evidence captured, a person decides) · ○ human-required". "When unsure between two grades, use the lower one." When a deterministic fact is stacked on an interpretive call, the finding takes the lower grade.
  - **Severity:** critical ("blocks a core task, with no workaround"), serious, moderate and minor.
- **Conformance in three states:** pass or fail are allowed only for ● criteria. Everything else, including "every SC no page exercised", is *undetermined*. "Don't let a not-exercised SC read as a pass." "One sampled page failing an SC fails it for the whole scope". "A checkpoint list is a denominator to cite, not a script to execute".
- **No proxy for humans:** "No personas, no synthetic sessions, no predicted behavior. The a11y tree shows machine state, not announcement or lived experience." Usability enters only as a labelled ◐ heuristic.
- **Evidence budget:** "uncertainty must be cheaper than certainty". A ◐ finding gets one selector and one screenshot, then stop.
- **Output:** Scope, Sample, a per-criterion conformance ledger (counts and bare SC numbers), findings by severity tagged by evidence basis, and a human handoff for each ○ item that names the ability, the assistive technology and the flow. "State what wasn't covered … Omitting it reads as 'all clear'."
- **Assessment:** Its evidence model fits a reviewer whose verdict others act on. It directly contradicts impeccable's personas, and that disagreement is useful (section 3).

### 2.6 Addy Osmani `accessibility` and `web-quality-audit`

- **Workflow:** It is "Evidence-led". The agent runs a live Lighthouse accessibility audit first (`lighthouse_audit` in Chrome DevTools MCP), then uses the failed nodes "to localize the relevant component", then inspects "a rendered accessibility-tree snapshot for names, roles, states, landmarks, and heading structure" and exercises the flow by keyboard. After fixing, it re-runs the same audit. "a score of 100 is not WCAG conformance".
- **Content:** WCAG 2.2 organised by POUR, with code examples. It includes 2.4.11 Focus Not Obscured and 2.5.8 Target Size at 24×24. The manual checklist covers keyboard, a screen reader, 200% zoom, high contrast and reduced motion. Its severity buckets are Critical (missing labels, missing alt text, contrast, keyboard traps, no focus indicator), Serious and Moderate.
- **`web-quality-audit`:** "Keep measured findings separate from hypotheses found only in code" and "Report what is verified and what still needs field or human validation."
- **Assessment:** It is the best plain account of *tool order*: run the automated audit, localise from its failures, then do manual checks. It is not about visual design.

### 2.7 Anthropic `design-critique` and `accessibility-review` (knowledge-work-plugins, design)

- **`design-critique`:** Five sections: First Impression ("2 seconds", "What draws the eye first? Is that correct?"), Usability, Visual Hierarchy, Consistency and Accessibility. Severity is 🔴 Critical, 🟡 Moderate or 🟢 Minor. The output has a "What draws the eye first" line, a reading-flow line, an inconsistency table, "What Works Well" and three priority recommendations. "Match the stage: Early exploration gets different feedback than final polish."
- **Inputs:** A Figma link, a screenshot or a description. It does not use a browser.
- **`accessibility-review`:** A WCAG 2.1 AA quick reference covering 14 criteria and a "Testing Approach" ("Automated scan (catches ~30% of issues)", keyboard-only, screen reader, contrast, "Zoom to 200%"). The output has tables for contrast, keyboard navigation and screen-reader announcements.
- **Assessment:** These are well-formed but shallow. They are aimed at designers critiquing mockups, not agents verifying a running app. One error: the skill lists "2.5.5 Touch target >= 44x44" as an AA criterion, but 2.5.5 is AAA. The AA target-size criterion is 2.5.8 at 24×24 in WCAG 2.2.

### 2.8 Emil Kowalski `review-animations` (and `emil-design-eng`)

- **Scope:** Motion only. "Default to flagging. Approval is earned."
- **Standards:** Ten "Non-Negotiable Standards". Among them: justified motion; frequency-appropriate motion ("Keyboard-initiated and 100+/day actions get **no** animation"); ease-out, never ease-in; UI animation under 300ms; popovers scaling from their trigger; interruptibility; animating transform and opacity only; reduced motion; asymmetric enter and exit; cohesion.
- **Triggers and fixes:** A list of "Aggressive Escalation Triggers", and a "Remedial Preference Hierarchy" that starts with "Delete the animation".
- **Output:** A required table with Before, After and Why columns, then findings grouped into six impact tiers, then an explicit **Block** or **Approve**, with the criteria for each written out.
- **`break-ui`:** Feeds plausible worst-case data ("Plausible or schema-backed, never random") through the component's real data boundary and reports what broke. It overlaps with the other researcher's area.
- **Assessment:** It is the strongest example of a narrow review with explicit pass criteria. It works from code, so it cannot see motion. Its own advice is to review "in slow motion / frame-by-frame".

### 2.9 OpenAI `playwright-interactive` (Codex curated skills; does both)

- **Inventory first:** "Write a brief QA inventory before testing". Build it from three sources: the requirements, the features actually implemented, and "the claims you expect to make in the final response". "Anything that appears in any of those three sources must map to at least one QA check before signoff." "If a requirement is visually central but subjective, convert it into an observable QA check".
- **A separate visual QA pass:**
  - "do not assume a functional pass proves a visual claim".
  - "Inspect the initial viewport before scrolling".
  - "inspect the densest realistic state you can reach".
  - Run a pass at the minimum supported viewport.
  - "Distinguish presence from implementation: if an intended affordance is technically there but not clearly perceptible because of weak contrast, occlusion, clipping, or instability, treat that as a visual failure".
  - "Judge aesthetic quality as well as correctness".
  - "Prefer viewport screenshots for signoff. Use full-page captures only as secondary debugging artifacts".
  - Before signoff, the agent asks "what visible part of this interface have I not yet inspected closely?" and "what visible defect would most likely embarrass this result if the user looked closely?"
- **Signoff:** Functional correctness, viewport fit and visual quality "must each pass on their own". "visible clipping in screenshots is a failure to resolve, not something metrics can overrule". "Include a brief negative confirmation of the main defect classes you checked for and did not find."
- **Assessment:** This is the closest in spirit to orchestrate's current "decide what you will look at before you look" rule, translated to UI terms. Its inventory-from-claims idea maps directly onto a done-when file.

---

## 3. Other mechanisms worth noting

- **Deterministic gates beside the judge.** taste-skill's `gate.mjs` runs a headless-Chrome checker at 1440 and 390 width, with checks such as `tap-size`, `off-viewport`, `empty-area` (a section more than 50% empty fails), heading order and a Tab walk. It counts fix rounds. False positives are waived in a JSON file, and each waiver needs a target and a reason of at least 12 characters. Impeccable's detector (62 rules) and gstack's detector (about 30 rules) play the same role. All three keep the mechanical tells out of the LLM's judgement.
- **Classify the surface before judging it.** Impeccable and gstack share Persuade, Operate, Read and Experience. The rules differ by mode: a dashboard is judged on scanability and consistency, a landing page on composition and brand.

---

## 4. What the best of them have in common

1. **They look at the rendered interface, not the code.** gstack: "Never read source code." OneRedOak: "Live Environment First." ui-ux-pro-max: "Read code only to explain a defect you already observed." Impeccable's critique requires the browser for any viewable target. Only Vercel and Emil review code alone, and they are scoped to rules that are visible in code.
2. **They use fixed viewport sizes.** 375, 768 and 1440 is the near-universal set (OneRedOak, gstack, ui-ux-pro-max adds 1024 and 1920). Impeccable's finish reviewer requires desktop and mobile captures, and taste-skill uses 1440 and 390. OpenAI adds "the minimum supported viewport" and "initial viewport before scrolling".
3. **They name the states and flows to visit.** Every strong skill requires the primary flow plus interaction states: hover, focus, active and disabled; loading, empty, error and long content. gstack and OneRedOak walk 2–3 flows. accesslint samples by template, key flow and state, plus a random set. gstack's diff-aware mode scopes the review to the routes the change touched.
4. **They form a first impression before working through a checklist.** gstack ("The first 3 things my eye goes to are…"), Anthropic ("What draws the eye first? Is that correct?") and Impeccable (the specificity verdict before the detector output) all do this. It is how they get hierarchy judged at all.
5. **They anchor judgement to named principles.** Nielsen's 10 (Impeccable), Krug's trunk test and goodwill (gstack), WCAG success criteria (all the accessibility skills), cognitive-load limits (Impeccable: no more than 4 options). gstack says "never 'this feels off' without one".
6. **They separate severity from evidence, and both from taste.** Most use a 4-level, impact-based severity tied to the user's task: blocks a task, major difficulty, workaround exists, polish. They differ in wording, from P0–P3 to Blocker, High, Medium and Nit. The strongest add a second axis for *how well the finding is supported*. accesslint uses ● ◐ ○. ui-ux-pro-max says "Distinguish 'broken' from 'I'd prefer'". Addy Osmani says "Keep measured findings separate from hypotheses".
7. **They require evidence for every finding.** A screenshot (gstack: "Every finding needs at least one"), a selector or accessibility-tree fact, a measured value, or `file:line`.
8. **They cap the findings and rank them.** "3-5 priority issues" (Impeccable), "5-10 well-documented findings beat 20 vague ones" (gstack), "at most eight" material fixes (finish reviewer), "Keep P3s few".
9. **They end with a verdict.** Ship, ship with fixes, or needs work (ui-ux-pro-max). Block or approve (Emil). Recapture, rebuild, fix or ship (Impeccable's finish reviewer). The verdict follows from the findings ("derived, never felt").
10. **They report what they did not cover.** accesslint: "Omitting it reads as 'all clear'". OpenAI: "negative confirmation of the main defect classes you checked for and did not find". Impeccable: a degraded-run banner.

## 5. Where they differ

| Question | One side | Other side |
|---|---|---|
| Simulated users? | Impeccable walks 2–3 named personas through the primary action and reports what broke for each | accesslint forbids it: "No personas, no synthetic sessions, no predicted behavior". Usability is a labelled ◐ heuristic at most |
| Score or no score? | Impeccable scores Nielsen out of 40 and each audit dimension 0–4. gstack gives A–F letter grades by deduction. gstack's plan review rates 0–10 and says what would make it a 10 | OneRedOak, accesslint and Vercel give no score, only triaged findings and conformance per criterion |
| Prescribe the fix? | gstack: "change X to Y because Z". Emil: Before/After/Why with exact values | OneRedOak: "Problems Over Prescriptions", which means describe the impact, not "Change margin to 16px" |
| Whose standard? | House taste: gstack's banned fonts, type-scale ratios and "AI slop" list; Emil's 300ms rule; Impeccable's craft floor | The project's own: OneRedOak's principles file, Impeccable's PRODUCT.md and DESIGN.md, the finish reviewer's approved mockup. Or a public standard: WCAG |
| Can the reviewer fix things? | gstack and taste-skill run fix loops | Impeccable's critique and audit, accesslint and the finish reviewer only assess ("Don't fix issues; document them") |
| Code or rendered page? | Vercel, Emil and Impeccable's `audit` read code | gstack, OneRedOak and OpenAI read the render. Impeccable's critique and Addy Osmani do both, in a stated order |
| One context or several? | Most run inline | Impeccable isolates judge and detector in separate subagents. accesslint runs one subagent per sampled page. gstack adds a second model's opinion |

## 6. What this suggests for orchestrate's reviewer (inference, not from any skill)

- **Replace the rows for UI milestones with a UI inspection list.** The current method ("break it into pieces, decide how to see each piece") carries over well. It already matches OpenAI's inventory and accesslint's sample. What needs replacing for a UI is the *views*. Instead of crops at full resolution and several angles, the views are:
  - each listed screen at 375, 768 and 1440 (or the project's minimum supported size), starting with the first viewport before scrolling
  - each state: default, hover and focus, loading, empty, error, long or dense content
  - each key flow, walked step by step
  - an accessibility-tree snapshot and a keyboard pass
- **Have the reviewer write a first impression before the checklist.** gstack's three-things-the-eye-goes-to line and its trunk test are cheap, and they are the only prompts in the set that reliably make an agent judge hierarchy.
- **Keep mechanical findings away from judgement until judgement is done.** An axe or Lighthouse run, and any project detector, should run after the reviewer's own look, or in a separate pass, then be reconciled (Impeccable).
- **Give each finding two grades: severity and evidence basis.** accesslint's ● ◐ ○ maps onto orchestrate's `cant_tell` already. A taste call is ◐ and should never fail a milestone on its own. A WCAG failure with a selector is ●.
- **Judge against the project's own standard first.** Use the done-when file, the brief, and any design file. Bring in house-style lists only as labelled heuristics.
- **Make the verdict derived, and list what was not inspected.**
