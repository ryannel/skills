---
name: release-notes
description: Writes the release notes for a new version of this repository. Collects the pull requests merged since the last version tag, groups them by their feat / fix / chore label, adds a user-facing entry to CHANGELOG.md, and adds lines to docs/migration.md for changes under api/public/. Use when asked to write or draft release notes, update the changelog for a release, or do the Friday release notes.
---

# Release notes

Every release gets an entry in `CHANGELOG.md`, written for the people who use the product, and a line in `docs/migration.md` for every change under `api/public/`. This is the weekly procedure for producing both.

Run everything from the repository root. The work ends with those two files edited and left uncommitted, plus a short report. Do not commit, tag or push unless the person asks, because they review the wording before it goes out.

The procedure needs `git` and an authenticated `gh`. If `gh` fails, stop and say so. Labels cannot be recovered from pull request titles, so there is no fallback worth using.

## 1. Find the range, the version and the date

**Last version.** Run `git fetch --tags`, then `git describe --tags --abbrev=0 --match 'v*'` to get the most recent version tag. Check that it matches the top `## v…` heading in `CHANGELOG.md`. If they disagree, stop and ask: either a release was tagged without notes or notes were written without a tag, and the range is uncertain either way.

**New version.** Run `scripts/next-version.sh` and use exactly what it prints. Do not work the number out from the changes yourself, even when it seems obvious. The script is the only source for it, and a plausible guess is how a wrong version gets published. If the script fails or wants arguments, read it to see how it is meant to be called. If you still have no version, stop and report what happened.

**Date.** Run `date +%F` for today's date, and write it in whatever format the existing headings use.

## 2. List the merged pull requests

```bash
git log --merges v<last>..HEAD --format='%H %s'
```

Each merge commit is one pull request, and its number is in the subject (`Merge pull request #482 from …`). If a subject carries no number, find the pull request from the commit:

```bash
gh pr list --state merged --search <sha> --json number,title
```

If nothing was merged in the range, say so and stop. Do not write an empty entry.

## 3. Find each pull request's label

```bash
gh pr view <N> --json number,title,body,labels,closingIssuesReferences
```

The label that matters is one of `feat`, `fix` or `chore`.

**Pull requests merged by the merge bot have no such label.** For those, the label is on the linked issue. So whenever a pull request has none of the three labels, take the issue numbers from `closingIssuesReferences` and read the label there:

```bash
gh issue view <M> --json number,title,body,labels
```

Never treat an unlabelled pull request as a chore, and never skip it. That is how real features go missing from the notes, and it is the mistake every new person makes.

If neither the pull request nor its linked issues carry a label, or the labels conflict, place the change by what its description and diff show it does. Then name it in the final report as placed by judgement, so the person can correct it and fix the label.

## 4. Decide what goes in

- **`feat` and `fix`** go in the changelog.
- **`chore`** is left out of the changelog. It is still checked in step 6.
- **Breaking changes** go first, whatever their label. A change is breaking when someone who upgrades has to change something to keep working: an API field, endpoint, option, flag or config key that was removed or renamed, a default that changed, or validation that got stricter. Signs to look for are a breaking label on the pull request or issue, `!` or `BREAKING CHANGE` in the title or body, and removals or renames under `api/public/`. When you cannot tell whether users must act, ask the person. Do not decide quietly in either direction.

## 5. Write the changelog entry

Add a new section at the top of `CHANGELOG.md`, above the previous version's heading and below any title or introduction the file has.

```markdown
## v2.8.0 (2026-11-13)

**Breaking**
- Exports no longer accept `format=xml`. Request `format=json` or `format=csv` instead.

<features, then fixes>
```

- The heading is `## vX.Y.Z (date)`.
- Breaking changes come first, under a `**Breaking**` line. Each one says what to do about it as well as what changed. A breaking change appears only there, not again under features or fixes.
- Features follow, then fixes. Use the same group headings and bullet style as the previous entries in the file. On any detail of layout, such as whether lines carry pull request numbers, the existing entries win over the sketch above.
- Leave out any group that is empty, including `**Breaking**`.

**Write for users, not from pull request titles.** A title describes what a developer did to the code. A note describes what changed for the person using the product. Read the pull request body and the linked issue to find that effect, then say what the user can now do or what no longer goes wrong.

| Pull request title | Release note |
| --- | --- |
| `fix: null check in ExportJob.run` | Exports no longer fail for projects that have no members. |
| `feat: add bulk endpoint + UI for tag ops` | You can now add or remove a tag on many items at once. |

- Use the names users see in the product and its documentation, not class, function or table names.
- Write one line per change a user would notice. Several pull requests that build one feature become one line.
- If a `feat` or `fix` has no effect a user could notice, leave it out and list it in the report.

## 6. Add migration notes for `api/public/`

Check every merged pull request in the range, chores included. First see whether anything under the path changed at all:

```bash
git diff --name-only v<last>..HEAD -- api/public/
```

If that prints nothing, no migration lines are needed. Otherwise find which pull requests are responsible, one merge commit at a time:

```bash
git diff --name-only <merge-sha>^1 <merge-sha> -- api/public/
```

Each pull request that touches `api/public/` gets a line in `docs/migration.md` under the new version, following the layout the file already uses. The line tells someone calling the API what changed and what they need to do, naming the old form and the new one.

This rule goes by path, not by judgement. A pull request that touches `api/public/` gets a line even when it is labelled `chore` or looks harmless, because callers depend on those files and the migration document is where they look. For a change that needs no action, the line says what changed and that no action is needed.

A `chore` that touches `api/public/` still stays out of `CHANGELOG.md`. The exception is a chore that turns out to be breaking: it is mislabelled, so put it under `**Breaking**` and say so in the report.

## 7. Check and report

Before finishing, confirm that:

- the version in the heading is the one `scripts/next-version.sh` printed;
- every `feat` and `fix` pull request in the range is either covered by a line or on your left-out list;
- `**Breaking**` comes first, and each of its lines says what to do;
- every pull request that touches `api/public/` has a line in `docs/migration.md`.

Then tell the person:

- the version, and the range it covers;
- how many pull requests went into each group, and how many chores were left out;
- any pull request you placed by judgement because it had no usable label;
- any `feat` or `fix` you left out, and why;
- any open question, such as a change that might be breaking;
- that both files are edited and nothing is committed.
