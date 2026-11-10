# Checks for workflow-to-skill

The request, in the person's words:

> 
> can you turn what we did for the tidepool release into a skill so next time I don't have to correct the same things? my notes are in release-notes.md. I use claude code, my teammate Priya uses codex

Checks:

1. The output holds one skill folder whose SKILL.md has a name equal to the folder's name and a description, and scripts/check_skill.py reports no problems for it.
2. The description says what the skill does and when to use it, in terms of releasing or publishing the tidepool package. It does not claim general Python or packaging work.
3. The body says the version must be changed in both pyproject.toml and src/tidepool/__init__.py.
4. The body says the changelog heading uses the UTC date, and gives the reason (the release bot compares it with the tag's timestamp).
5. The body says a TestPyPI upload of an existing version reports success while uploading nothing, and says how to tell.
6. The body says the tag is pushed only after the CI run for the release commit on main is green, states this as one rule with its condition inside it, and says the agent may then push without asking.
7. The body says what finished looks like with a check the agent can run, such as installing the new version in a fresh environment and reading its version.
8. The body has no section about when to use the skill.
9. The skill's text has no word in capitals for emphasis (IMPORTANT, CRITICAL, MUST, NEVER, ALWAYS).
10. The frontmatter uses only name, description, license, compatibility, metadata and allowed-tools.
11. The skill sets no rule about changelog wording or which virtual-environment tool to use.
