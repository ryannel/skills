---
name: tidepool-release
description: Releases a new version of the tidepool Python package, from the version bump and changelog entry through TestPyPI, the tag and the install check. Use when asked to release, publish, tag or cut a version of tidepool.
---

# Releasing tidepool

This skill releases a version of tidepool to PyPI. Below, `<version>` is the version being released, such as
`0.9.0`, and the release commit is the commit that holds the version change and the changelog entry.

The release is finished when `pip install tidepool==<version>` succeeds in a fresh virtual environment and
`tidepool --version` in that environment prints `<version>`. Run both and give their output in your report.

Pushing the tag is the real release. CI publishes to PyPI as soon as a `v<version>` tag is pushed, and PyPI
never lets a version be uploaded twice. So push the tag only after the CI run on `main` for the release commit
has finished green. Look at the run for that exact commit, not the newest run on `main`. Once it is green, push
the tag yourself. That needs no go-ahead, and neither does any other step here. The one place to stop for the
person is the case described in step 5.

Waiting is part of the job, both for that CI run and for the publish job after the tag. Don't end your turn with
the tag or the install check left for the person to do.

## The steps, in order

1. Set the version in two places: `version` in `pyproject.toml` and `__version__` in `src/tidepool/__init__.py`.
   They must match, or `tidepool --version` reports the wrong version.

2. Add the entry to `CHANGELOG.md`, with its heading in the same form as the entries already there. The date in
   the heading is the UTC date, from `date -u +%Y-%m-%d`, not the local date. The release bot compares that date
   with the UTC timestamp of the tag and fails the release if they differ. For the same reason, if the UTC date
   has changed by the time you are ready to tag, correct the heading first and wait for CI on the new commit.
   How you word the entry is up to you.

3. Run `make check`. It runs the linter and the unit tests and takes about 40 seconds.

4. Build with `uv build`.

5. Upload to TestPyPI, and confirm the upload yourself, because the command's output can't be trusted. If
   `<version>` already exists on TestPyPI, the upload prints "success", exits 0 and uploads nothing.

   - Before uploading, run `pip index versions tidepool --index-url https://test.pypi.org/simple/` and note
     whether `<version>` is already listed.
   - Upload with `uv publish --publish-url https://test.pypi.org/legacy/`.
   - Afterwards, read the upload time of the files at `https://test.pypi.org/project/tidepool/<version>/`. The
     same time is the `upload_time_iso_8601` field at `https://test.pypi.org/pypi/tidepool/<version>/json`. The
     upload happened only if that time is from the last few minutes.

   If `<version>` was already listed before your upload, TestPyPI holds files from an earlier build and will
   not take yours under the same version. Stop before the tag and tell the person, because this step has then
   tested nothing, and only the person knows whether an earlier attempt explains it.

6. Get the release commit onto `main`, the same way earlier release commits in the history got there. Wait for
   its CI run to finish green.

7. Tag the release commit `v<version>` and push the tag.

8. When the publish job that the tag started has finished, make a fresh virtual environment with whichever tool
   you like, and run `pip install tidepool==<version>` and then `tidepool --version` in it.
