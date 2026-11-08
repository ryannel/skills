# The project profile: `ORCHESTRATE.md`

Every orchestrate skill reads this file first. It holds everything that's different about this project, which is
what lets the skills themselves stay generic. Keep it to about a page, and link to longer docs rather than copying
them in.

`agent_loop.py` reads the lines marked *(loop)*. Keep them in the `- **Label:** value` shape, with nothing on the line
but the value and an optional `*( )*` note, because the loop takes the whole line as the value. Run
`agent_loop.py profile` to check they parse.

```markdown
# Orchestrate profile: <project>

- **Purpose:** <link to the doc saying what the project is for and what finishes the current goal>
- **Quality bar:** <the standard inspected items are judged against, in words, naming shipped examples>
- **Plans:** docs/modules  *(loop)*
- **Evidence:** docs/evidence  *(loop: review files and evidence pages)*
- **Graded examples:** docs/evidence/graded-examples.md  *(past verdicts the owner agreed with or overturned)*
- **Check:** npm run check  *(loop: the exact command that must pass before integrating)*
- **Integrate:** push  *(loop: push = rebase onto Remote/Branch and push without force; local = commit to Branch only)*
- **Branch:** main  *(loop)*
- **Remote:** origin  *(loop)*
- **Codex generator:** gpt-6.1-sol medium  *(loop)*
- **Codex sandbox:** workspace-write  *(loop: or danger-full-access)*
- **Writable roots:** <paths the build writes outside the worktree, e.g. ~/.cargo, ~/.npm>  *(loop)*

## Starting from a clean clone
<how a fresh worktree gets to a running product: setup command, seed data and test accounts, services it needs,
where secrets come from, and how parallel worktrees avoid sharing a port or database>

## Targets

| Target | What it is | Run | Capture | Edge conditions |
|---|---|---|---|---|
| <web-chrome> | <Chrome, desktop> | <`npm run dev`> | <Playwright screenshots, console and network log> | <empty, loading, error, slow network, resize> |
| <cli> | <the built binary> | <`cargo run -- …`> | <transcript and exit code> | <bad arguments, piped stdin, Ctrl-C> |

## Rules
- **Exclusive resources:** <things one run at a time may use, e.g. "simulator", "gpu: timing runs"; or none>
- **Large captures:** <where frame sequences and other bulky evidence go if not committed, and how a reviewer gets them>
- **Owner decides:** <e.g. changing the goal; spending; publishing or deploying; irreversible actions>
- **Licences and paths not to touch:** <e.g. no GPL code; never modify ../other-repo>

## Project guidance
- <domain rules each level reads, e.g. "Building: .agents/skills/<project>-engineering">
```

`Integrate: push` is standing permission to push verified work to the branch. Only set it if the owner has given that
permission. Without it, use `local`, and the owner merges.
