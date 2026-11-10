# Grades for workflow-to-skill

Graded blind on 10 November 2026. Evidence is quoted from `A/tidepool-release/SKILL.md` and
`B/tidepool-release/SKILL.md` unless another file is named. Line numbers are the file's own.

| # | A | B | Evidence for A | Evidence for B |
|---|---|---|---|---|
| 1 | pass | pass | One folder, `A/tidepool-release/`. Line 2: "name: tidepool-release". Line 3 is a description. `check_skill.py` printed "ok", exit 0, no notes. | One folder, `B/tidepool-release/`. Line 2: "name: tidepool-release". Line 3 is a description. `check_skill.py` printed "ok", exit 0, no notes. |
| 2 | pass | pass | Line 3: "Releases a new version of the tidepool Python package to PyPI ... Use when asked to release, publish, ship, tag or cut a tidepool version, or to do one of those steps alone, such as bumping the version or pushing the tag." Nothing about general Python or packaging. | Line 3: "Releases a new version of the tidepool Python package, from the version bump and changelog entry through TestPyPI, the tag and the install check. Use when asked to release, publish, tag or cut a version of tidepool." Nothing about general Python or packaging. |
| 3 | pass | pass | Line 18: "Set the version in two places: `version` in `pyproject.toml` and `__version__` in `src/tidepool/__init__.py`." | Line 25: "Set the version in two places: `version` in `pyproject.toml` and `__version__` in `src/tidepool/__init__.py`." |
| 4 | pass | pass | Lines 21-23: "The date in the heading is today's date in UTC (`date -u +%F`), not the local date. The release bot compares that date with the UTC timestamp of the tag, and fails the release if they differ." | Lines 28-30: "The date in the heading is the UTC date, from `date -u +%Y-%m-%d`, not the local date. The release bot compares that date with the UTC timestamp of the tag and fails the release if they differ." |
| 5 | pass | pass | Lines 33-34: "If the version already exists on TestPyPI, `uv publish` prints "success" and exits 0 but uploads nothing". How to tell, lines 37 and 43-47: "run `pip index versions tidepool --index-url https://test.pypi.org/simple/`" before, and after "look at the upload time ... The step has passed when the version is listed and its upload time is from the last few minutes." | Lines 38-39: "If `<version>` already exists on TestPyPI, the upload prints "success", exits 0 and uploads nothing." How to tell, lines 41-46: "run `pip index versions tidepool --index-url https://test.pypi.org/simple/` and note whether `<version>` is already listed" and "The upload happened only if that time is from the last few minutes." |
| 6 | pass | pass | Lines 51-53: "Push only when both of these are true: - The CI run for the release commit on `main` has finished and passed." Line 59: "When both are true, push the tag yourself. The person has said you don't need to ask first." The rule is a single "push only when" with its condition inside it. A second condition (the UTC date still matches) is joined to it; see the notes below. | Lines 15-17: "So push the tag only after the CI run on `main` for the release commit has finished green. ... Once it is green, push the tag yourself. That needs no go-ahead". One rule, condition inside it. |
| 7 | pass | pass | Lines 8-9: "The release is done when `pip install tidepool==<version>` works in a fresh virtual environment and `tidepool --version` prints the new version." | Lines 11-12: "The release is finished when `pip install tidepool==<version>` succeeds in a fresh virtual environment and `tidepool --version` in that environment prints `<version>`. Run both and give their output in your report." |
| 8 | pass | pass | The only heading is line 6, "# Releasing tidepool". The checker printed no "when to use" note. | Headings are line 6 "# Releasing tidepool" and line 23 "## The steps, in order". The checker printed no "when to use" note. |
| 9 | pass | pass | Checker count of words in capitals: none (no note printed). My own search for runs of capitals found only CHANGELOG, CI, SHA and UTC, which are names. | Checker count: none. My own search found only CHANGELOG, CI and UTC. |
| 10 | pass | pass | Frontmatter is lines 2-3: `name` and `description` only. | Frontmatter is lines 2-3: `name` and `description` only. |
| 11 | pass | pass | Line 23: "The wording of the entry is up to you." Lines 62-63: "make a fresh virtual environment with whatever tool you like". Line 21's "heading in the same form as the earlier entries" is about the heading's format, not the entry's wording. | Line 32: "How you word the entry is up to you." Lines 57-58: "make a fresh virtual environment with whichever tool you like". |

Passes: A 11 of 11, B 11 of 11.

## Which I would hand to the person

A, by a small margin. The two skills are nearly the same on the four corrections, so the checks don't separate them.
A covers three situations B leaves open: the CI run for the release commit fails (A line 59-60: "If the CI run failed,
don't push the tag. Fix the cause in a new commit"), the publish job fails (A lines 65-66: "Don't delete or move the
tag to try again without asking, because that starts another publish"), and a request for one step only (A line 16, and
the description's "or to do one of those steps alone"), which matters because the first correction in the notes was
a bare version bump. A's reply also carries a finding the person needs before the first run: there is no `tidepool`
project on TestPyPI and the `tidepool` on pypi.org is a different project at 0.1.3. I checked both on 10 November 2026
and they are true (test.pypi.org/pypi/tidepool/json returns 404; pypi.org reports 0.1.3, "Deploy full-featured web
apps in minutes"). B is the tidier read and its reply is shorter, with four questions against A's eight.

## What the checks don't cover

- **B widens the person's permission.** B line 17: "That needs no go-ahead, and neither does any other step here."
  The notes waive asking for one thing only, the tag push. B's sentence also covers putting the release commit on
  `main` (step 6), and B's own reply asks the person whether that is allowed (`B/reply.md` question 2: "Is the agent
  allowed to do that step without asking?"). The skill answers yes before the person has. A doesn't say this.
- **B has no branch for a red CI run or a failed publish job.** B line 52-53 says "Wait for its CI run to finish green"
  and line 20-21 says "Don't end your turn with the tag or the install check left for the person to do". Together those
  leave an agent with a failed run and an instruction not to stop.
- **B uploads to TestPyPI even when it already knows the upload will do nothing.** B lines 41-43 note that the version is
  listed, then upload anyway, then stop (lines 48-50). A stops before the upload (A lines 37-39). Harmless, but it is
  the 20-minute confusion from the notes done on purpose.
- **Both add things the notes don't contain, and both say so in the reply.** The same three in each: re-check the UTC
  date before tagging, stop and tell the person when the version is already on TestPyPI, and a JSON address for the
  upload time (`upload_time_iso_8601`, which does exist on TestPyPI's JSON pages; I checked). A person may not want
  the stop on an existing TestPyPI version, since it is the only place either skill hands back.
- **A's skill carries history an agent doesn't need.** Line 34-35: "seen on the 0.9.0 release, where it cost 20
  minutes; the uv version wasn't recorded", and line 45-46: "endpoint checked 10 November 2026". Line 15 dates the
  release "4 November 2026" where the notes say only "4 Nov". None of it is wrong, but it is the author's
  record-keeping inside the instructions.
- **A moves the commit to `main` ahead of the build and the TestPyPI upload** (A step 4, before steps 5 and 6). The notes
  don't say when the commit landed, and A's order lets CI run during the rehearsal, so this is defensible. B keeps the
  notes' order. Neither says how the commit reaches `main`, and both ask.
- **Neither skill was run.** Both replies say so plainly. A ships `A/test-plan.md` with three cases and the stand-ins a
  safe run needs; B describes two cases in its reply. Neither tested whether the description makes the skill load.
- **The install advice differs and neither was tried.** A puts the real folder in `.claude/skills/` and links
  `.agents/skills/` to it; B does the reverse. Either works if both agents follow symlinks, and A alone raises the
  Windows case (`A/reply.md` question 7).
