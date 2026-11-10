---
name: release-notes
description: Writes the release notes for this repository. Turns the pull requests merged since the last release tag into a user-facing entry in CHANGELOG.md, and adds lines to docs/migration.md for changes under api/public/. Use when asked to write or draft the release notes or the changelog entry for a release, including the weekly Friday release.
---

# Release notes

The release notes are a new entry in `CHANGELOG.md` that tells the people who use the product what changed since
the last release. You write the entry from the pull requests (PRs) merged since the last release tag.

Two facts catch out most people the first time they do this:

- **A PR merged by the merge bot has its label on the linked issue, not on the PR.** The PR itself looks
  unlabelled. Look up the issue before you decide what kind of change the PR is. The commands are under
  [Which PRs go in](#which-prs-go-in).
- **The version number comes from `scripts/next-version.sh`.** Run the script and use the version it prints. If
  the script fails, stop and tell the person what it printed. Don't work the version out yourself from the last
  tag or from the size of the changes.

## Which PRs go in

Run `git log --merges v<last>..HEAD`, where `v<last>` is the most recent release tag. Each merge commit in the
output is one PR, and those PRs are the whole input for this release.

Every PR has a type label, which is one of `feat`, `fix` or `chore`. PRs labelled `feat` or `fix` go into the
release notes. PRs labelled `chore` are left out.

When a PR carries none of the three type labels, it was most likely merged by the merge bot, and the type label
is on the issue the PR closes. Find that issue with `gh pr view <N> --json closingIssuesReferences`, then read
its labels with `gh issue view <issue> --json labels`. If neither the PR nor its linked issues carry a type
label, don't choose one from the PR title. Leave the PR out of the entry and name it in your report, so the
person can place it.

The labels and linked issues come from GitHub, so you need `gh` signed in and able to reach the network. If `gh`
fails, stop and tell the person what failed. An entry written from the merge commit titles alone has no labels
behind it.

## The entry in CHANGELOG.md

Add a new section above the previous release's section. The heading is `## vX.Y.Z (date)`, with the version
from `scripts/next-version.sh` and today's date.

If any change is breaking, the entry starts with a `**Breaking**` line, and the breaking changes go under it
before anything else. A change is breaking when someone has to change what they do, or what their code does, to
keep things working after they upgrade. List a breaking change once, under `**Breaking**`, and say what the
person has to do.

After that come the `feat` notes and then the `fix` notes.

```markdown
## vX.Y.Z (date)

**Breaking**
- <what changed, and what the person has to do about it>

<the feat notes, then the fix notes>
```

For everything this template leaves open, copy the entries already in the file: the date format, the headings
over the `feat` and `fix` groups, the bullet style, and whether a note carries its PR number.

## Write for the people who use the product

Each note says what a person using the product will notice. A PR title says what the developer did to the code,
so a PR title is not a note. Read the PR description, and the diff when the description doesn't say, to find out
what changed for the user.

For example, a PR titled "fix: null check in ExportJob retry path" becomes "Exports no longer fail when a retry
runs after a network timeout."

## Changes under api/public/

Every PR in the range that changes a file under `api/public/` also needs a line in `docs/migration.md`. The line
tells someone who calls the public API what they have to change. Follow the way that file is already organised
and worded.

This rule goes by the files a PR changes, not by its type label, so check the `chore` PRs as well.
`gh pr view <N> --json files` lists the files. If one of these PRs changes nothing a caller would notice, name
it in your report and let the person decide whether it needs a line.

## When you are finished

The job is finished when every PR in the range is accounted for. Each one is in the entry, or was left out as
`chore`, or is named in your report as having no type label.

The job ends with `CHANGELOG.md` and `docs/migration.md` edited in the working tree. Reading the git history,
reading PRs and issues with `gh`, running `scripts/next-version.sh` and editing those two files need no
go-ahead. Committing, tagging and publishing the release are separate steps, so do them only when the person
asks.

Then tell the person:

- the version, and the tag range the entry covers;
- any PR you could not place because it had no type label;
- which PRs changed `api/public/`, and the lines you added to `docs/migration.md` for them;
- any note where you were unsure what the user would notice.
