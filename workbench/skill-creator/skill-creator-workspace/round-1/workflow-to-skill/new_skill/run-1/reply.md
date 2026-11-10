I've written the skill as a draft at `tidepool-release/SKILL.md` in this folder. It is not installed and has not been tested on a real request; the format check (`check_skill.py`) passes.

## What it holds

It is one file with the eight release steps in order. Each of your corrections is in it:

- **Version:** it goes in both `pyproject.toml` and `src/tidepool/__init__.py`, and the two must match.
- **Changelog date:** the heading uses the UTC date, because the release bot compares it with the tag.
- **TestPyPI:** the upload can print "success" and upload nothing. The agent checks whether the version is already listed before uploading, and checks the upload time afterwards.
- **Tag:** the agent pushes it only after the CI run on main for the release commit is green. It then pushes without asking, and it waits for CI instead of handing the tag back to you.
- **Finish:** the release is done when `pip install tidepool==<version>` works in a fresh venv and `tidepool --version` prints that version.

It leaves changelog wording and the venv tool to the agent, as you said.

## Three things I added that your notes don't say

- **UTC date rolls over:** if the UTC date changes between writing the changelog and tagging, the agent corrects the heading first. This follows from the release bot rule.
- **Version already on TestPyPI:** the agent stops before tagging and tells you. Your notes don't say what you did next, so this is the one place it asks.
- **Getting the release commit onto main:** the agent does it "the same way earlier release commits got there", because the notes don't say whether that is a direct push or a pull request.

## Installing it for you and Priya

Both Claude Code and Codex read the same skill format. In the tidepool repository, keep one real copy and link it for Claude Code:

```bash
mkdir -p .agents/skills .claude/skills
cp -R <this folder>/tidepool-release .agents/skills/
ln -s ../../.agents/skills/tidepool-release .claude/skills/tidepool-release
```

Codex reads `.agents/skills/` and Claude Code reads `.claude/skills/`. Once committed, Priya's agent loads it too, so I have left that step to you.

## Testing

I'd test with two requests, each run once with the skill and once without, so four runs:

1. "release tidepool 0.9.1, changelog is just the retry fix"
2. "cut 0.10.0 — heads up I think I already pushed 0.10.0 to testpypi last week when I was messing around"

The checks, written before any run:

- Both version files show the new version.
- The changelog heading has the UTC date.
- No tag is pushed before the release commit's CI run on main is green.
- Once it is green, the tag is pushed without asking you.
- In request 2, the agent notices the existing TestPyPI version and stops before tagging.

These runs can't happen in the real repository, because the run without the skill may push a tag and publish. They need a copy of the repository with stand-ins for the push and the uploads, which I'd need your help to set up. The other option is to skip them and watch the next real release.

## Questions

1. When the version is already on TestPyPI, should the agent stop and tell you (as drafted), or carry on to the tag?
2. Does the release commit go straight to main or through a pull request? Is the agent allowed to do that step without asking?
3. Do you want the test runs, in a copy of the repository, or will you try the skill on the next release?
4. Should the tag rule be enforced by CI as well? A skill is advice the agent weighs. A check in the publish workflow that refuses a tag whose commit has no green run on main would hold for both agents and for people. I can't see your CI setup, so I haven't written one.
