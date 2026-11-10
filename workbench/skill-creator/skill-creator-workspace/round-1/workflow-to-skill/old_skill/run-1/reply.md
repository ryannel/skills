I've written the skill as a draft. It isn't installed or tested yet, and both of those need a yes from you.

The draft is `tidepool-release/SKILL.md` in this folder. It's one file, about 70 lines, and it passes the format
checks (valid frontmatter, name and description within the limits).

## What it does

It walks the agent through the release in the order from your notes, and it says the release is finished only when
`tidepool --version` prints the new version from a fresh environment. Each of your four corrections is a rule with
its reason attached:

- **Version:** it changes both `pyproject.toml` and `__version__` in `src/tidepool/__init__.py`.
- **Changelog date:** it uses the UTC date in the heading, because the release bot compares it with the tag.
- **TestPyPI:** it checks whether the version is already there before uploading, and checks the upload time
  afterwards, instead of trusting "success".
- **Tag:** it pushes the tag only once the CI run for the release commit on main is green. It then pushes without
  asking, as you said it could.

It also tells the agent that changelog wording and the venv tool are its own choice.

I added three things that aren't in your notes:

- **Date check before tagging:** the agent re-checks the UTC date just before it tags. If midnight UTC passes while
  CI runs, the heading and the tag would differ and the bot would fail the release.
- **Version already on TestPyPI:** the agent tells you and lets you decide, and doesn't report the rehearsal as
  passed.
- **Failed publish job:** the agent reports it and stops. It doesn't move or delete the tag on its own.

Say if any of these is wrong and I'll take it out.

## Installing it for you and Priya

Claude Code and Codex read the same skill format, so one copy in the tidepool repository serves you both:

1. Copy the `tidepool-release` folder to `.claude/skills/tidepool-release/` in the tidepool repository. Claude Code
   reads that folder.
2. Add a symlink at `.agents/skills/tidepool-release` that points to `../../.claude/skills/tidepool-release`. Codex
   reads that folder and follows symlinks.
3. Commit both.

I haven't done this, because it's a shared repository and I was working only in this folder.

## Testing

Nothing has been run. `test-plan.md` has three prompts and what a good result must contain for each. The prompts
are:

1. "ok lets ship tidepool 0.9.1. changelog should mention the --depth flag fix and the 3.14 wheels. go"
2. "priya started the 0.9.1 release yesterday and got pulled onto something else, can you finish it? i think the
   version bump is already committed"
3. "can you bump tidepool to 0.10.0 and write the changelog entry, i'll do the rest tomorrow"

Do these sound like what you and Priya would type? The runs have to happen in a throwaway copy with a fake remote
and a fake upload, never the real repository, because a real run would push a tag. They also use your model quota,
so I'll start them only when you say so.

One thing I noticed while checking the TestPyPI address: TestPyPI has no project called `tidepool` today, and the
`tidepool` on pypi.org is at 0.1.3 and looks like a different project. If your package is published under another
name or on a private index, the commands in the skill need that name.

## Questions

1. What runs tidepool's CI (GitHub Actions or something else)? I left "check the CI run for that commit" to the
   agent. Once I know, I can name the exact command, and build the fake CI for the tests.
2. How does the release commit get onto main: a direct push, or a pull request? The skill says "the way this
   repository normally takes changes".
3. When the version is already on TestPyPI, what do you want to happen? The draft has the agent stop and ask you.
4. Where does the TestPyPI upload token come from? The skill doesn't mention credentials.
5. Should the skill load by itself when you say "release tidepool", or only when you type `/tidepool-release`? I
   left it loading by itself, because a release started without it repeats the mistakes you wrote down. The other
   setting is safer against a release nobody asked for.
6. If you don't give a version number, the agent asks for one. Would you prefer it to propose one from the changes?
7. Is Priya on macOS or Linux? A symlink committed to git needs extra setup on Windows, so she'd get a copy there
   instead.
8. The skill can only advise. If an agent still pushes the tag early with it loaded, the stronger fix is a small
   script or hook that refuses the push until CI is green. Do you want that now, or only if it happens again?
