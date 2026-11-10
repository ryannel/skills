# Notes from releasing tidepool 0.9.0 (with the agent, 4 Nov)

What we did, in the order it ended up working:

- bumped the version. Agent changed pyproject.toml only. Had to tell it: the version is ALSO in
  src/tidepool/__init__.py (`__version__`) and the two must match or `tidepool --version` lies.
- wrote the CHANGELOG.md entry. Agent used today's local date. Correction: the date in the heading is the UTC
  date, because the release bot compares it with the tag's UTC timestamp and fails the release if they differ.
- ran `make check` (lint + unit tests, about 40s). fine.
- built with `uv build`.
- uploaded to TestPyPI first: `uv publish --publish-url https://test.pypi.org/legacy/`.
  Gotcha we hit: if that version already exists on TestPyPI the upload prints "success" and exits 0 but uploads
  nothing. The only way to know is `pip index versions tidepool --index-url https://test.pypi.org/simple/` and
  looking at the upload time on the project page. We lost 20 min to this.
- agent then tagged v0.9.0 and pushed the tag straight away. Wrong: a pushed tag triggers the real PyPI publish
  in CI, and main's CI run for the release commit was still going. Rule: don't push the tag until the CI run for
  that commit on main is green. I'm fine with it pushing the tag itself once that's true, it doesn't need to ask.
- after the publish job finished: `pip install tidepool==0.9.0` in a fresh venv and `tidepool --version`.

Things I don't care about: how it words the changelog, which venv tool it uses.
