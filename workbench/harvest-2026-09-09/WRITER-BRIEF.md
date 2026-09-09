# Writer brief — 2026-09-09 update pass

You are the writer for ONE published skill in this repo. Only writers edit skill files. Research is done; your inputs are listed in your prompt.

## Read first (in this order, before any edit)
1. `workbench/uniformity/STANDARD.md` — sections 6 (apparatus: provenance markers, marker density, the two-bar section, dating, cross-links, readability 6.8a) and 7 (justified deviations). Sections 2–5 if you need the shape or depth targets.
2. `.agents/skills/media-model-skill/SKILL.md` — the prose style and the section anatomy (skim; it is long).
3. The skill itself: `SKILL.md` and every file in `references/`.
4. Your inputs (freshness JSON, harvest reports) — read them in full.

## Rules
- **Repair every finding in your freshness JSON, major and minor, inline.** The user asked for the skills to be updated, so this pass overrides the protocol's default of staging major findings. If a finding's `reality` cannot be trusted from the evidence given (e.g. the URL contradicts it, or it was itself reversed by a later finding), say so in your report and leave the text as it stands.
- **Add a new technique only when it earns its place**: `already_covered: false`, and source class `official` or `community-consensus`. A `single-report` item goes in only if it fills a real gap, and then it carries a `[community]` or `[flagged]` marker per STANDARD §6.2. Trivial single reports are omitted; say which in your report.
- **Every new fact traces to evidence.** A URL and date for web findings; `[live-use]` plus the run/dataset and date for media-lab findings. No invented numbers, no smoothing a contested claim into a settled one. If two inputs disagree, present the disagreement and mark it `[contested]`.
- **Provenance discipline.** Keep the two-bar confidence section current: a fact verified from an official source today may move up a bar; keep `[community]` / `[flagged]` where the source class has not changed. Update "verified" / "as of" date stamps you touch to 2026-09-09. Do not remove markers.
- **House voice.** Plain language, short sentences, explain the why. Match the existing prose around your edit. Read STANDARD §6.8a before writing a paragraph.
- **Shape.** Do not add or rename reference files unless the brief for your skill says so. Do not change the frontmatter `name`. Adjust `description` only if the skill's capability changed. Stay within the word bands in STANDARD §5 unless §7 lists a deviation for this skill.
- **Links.** Cross-skill links are `../sibling/` or `../../sibling/reference.md` only. Never link outside `skills/generative-media/`.
- **Do not edit** `freshness.json`, `marketplace.json`, the README, or any other skill's files. The orchestrator handles state; if another skill needs a matching edit, say so in your report.
- **Do not fetch the web** except to confirm a specific evidence URL when a finding looks wrong. Research is done.

## Report
Write `workbench/harvest-2026-09-09/writes/<skill>.md`:
- One line per edit: file, section, what changed, evidence (URL or `[live-use]` source).
- Findings resolved, by `id`. Findings declined, by `id`, with a one-sentence reason.
- Techniques added / omitted, by `id`.
- Watchlist recommendations: which watchlist items are now resolved, which to add, one line each.
- Any edit another skill needs to stay consistent.
Keep the report under 600 words. Your final message is a 5-line summary.
