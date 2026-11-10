---
name: tidepool-release
description: Releases a new version of the tidepool Python package to PyPI, from the version bump and changelog entry through the TestPyPI upload and the release tag to the install check. Use when asked to release, publish, ship, tag or cut a tidepool version, or to do one of those steps alone, such as bumping the version or pushing the tag.
---

# Releasing tidepool

The release is done when `pip install tidepool==<version>` works in a fresh virtual environment and
`tidepool --version` prints the new version. Until you've seen that yourself, say the release isn't finished and
name the step it reached.

You need the new version number from the person. If they didn't give one, ask before you change anything.

Do the steps in this order. Steps 1, 2, 6 and 7 each carry a rule that an agent got wrong on the 0.9.0 release
(4 November 2026) and the person had to correct. Follow those rules even where another way looks reasonable. If the
person asks for one step only, such as "bump the version" or "push the tag", do that step with its rule.

1. Set the version in two places: `version` in `pyproject.toml` and `__version__` in `src/tidepool/__init__.py`.
   They have to match. If only one changes, `tidepool --version` reports the wrong version.

2. Add the entry to `CHANGELOG.md`, with its heading in the same form as the earlier entries. The date in the
   heading is today's date in UTC (`date -u +%F`), not the local date. The release bot compares that date with the
   UTC timestamp of the tag, and fails the release if they differ. The wording of the entry is up to you.

3. Run `make check`. It runs the linter and the unit tests and takes about 40 seconds. Fix what it reports before
   going on.

4. Commit the changes and get the commit onto `main` the way this repository normally takes changes. This is the
   release commit. Note its SHA, because step 7 depends on the CI run for exactly this commit.

5. Build with `uv build`.

6. Rehearse the upload on TestPyPI, and don't trust what the upload prints. If the version already exists on
   TestPyPI, `uv publish` prints "success" and exits 0 but uploads nothing (seen on the 0.9.0 release, where it cost
   20 minutes; the uv version wasn't recorded). So check before and after.

   Before: run `pip index versions tidepool --index-url https://test.pypi.org/simple/`. If the new version is
   already listed, an upload would do nothing. Tell the person that TestPyPI already has this version and the
   rehearsal can't test this build, and let them decide what to do. Don't report the step as passed.

   Upload: `uv publish --publish-url https://test.pypi.org/legacy/`.

   After: run the `pip index versions` command again, and look at the upload time on
   `https://test.pypi.org/project/tidepool/<version>/`. The same time is the `upload_time_iso_8601` field at
   `https://test.pypi.org/pypi/tidepool/<version>/json`, which is easier to read than the page (endpoint checked
   10 November 2026). The step has passed when the version is listed and its upload time is from the last few
   minutes.

7. Tag the release commit as `v<version>`, but hold the push. Pushing the tag is what makes CI publish to the real
   PyPI, and a version published there can't be replaced. On the 0.9.0 release the agent pushed the tag while CI for
   the release commit was still running. Push only when both of these are true:

   - The CI run for the release commit on `main` has finished and passed. Look at the run for that SHA, not at
     whichever run is newest. If it's still running, wait for it.
   - `date -u +%F` still gives the date in the changelog heading. If midnight UTC passed while you waited, the
     release bot's comparison from step 2 would fail. Correct the heading in a new commit, and treat that commit as
     the release commit.

   When both are true, push the tag yourself. The person has said you don't need to ask first. If the CI run failed,
   don't push the tag. Fix the cause in a new commit, which becomes the release commit, and wait for its run.

8. Wait for the publish job that the tag started. When it has finished, make a fresh virtual environment with
   whatever tool you like, then run `pip install tidepool==<version>` and `tidepool --version`. The environment has
   to be fresh, because one that already holds tidepool from the working copy would print the right number without
   proving anything about PyPI. If the publish job fails, report what failed and stop. Don't delete or move the tag
   to try again without asking, because that starts another publish.

In your final message, give the evidence: the TestPyPI upload time, the CI run you waited for, and the output of
`tidepool --version`.
