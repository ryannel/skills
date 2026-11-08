# The project profile: `ORCHESTRATE.md`

Every orchestrate skill reads this file first. It holds everything that differs between projects, so the skills
themselves stay generic. Keep it to about a page, and link to longer project docs rather than copying them in.
`agent_loop.py` parses the lines marked *(loop)*, so keep their `- **Label:** value` shape. Running
`agent_loop.py profile` checks them.

```markdown
# Orchestrate profile: <project>

- **Purpose:** <link to the doc saying what the project is for and what finishes the current goal>
- **Quality bar:** <the standard visual and interaction items are judged against, in words, naming shipped examples>
- **Plans:** docs/modules  *(loop)*
- **Evidence:** docs/evidence  *(loop: review files and evidence pages; graded examples in graded-examples.md)*
- **Check:** <the command that must pass before integrating, e.g. `npm run check`>
- **Branch:** main  *(loop: integrate by rebasing, checking and pushing here without force)*
- **Remote:** origin  *(loop)*
- **Codex generator:** gpt-6.1-sol medium  *(loop)*
- **Codex sandbox:** workspace-write  *(loop: or danger-full-access)*
- **Writable roots:** <paths the build writes outside the worktree, e.g. ~/.cargo, ~/.npm>  *(loop)*

## Targets

| Target | What it is | Run | Capture | Edge conditions |
|---|---|---|---|---|
| <web-chrome> | <Chrome, desktop> | <`npm run dev`> | <Playwright screenshots and trace> | <empty, loading, error, slow network, resize> |
| <cli> | <the built binary> | <`cargo run -- …`> | <transcript and exit code> | <bad arguments, piped stdin, Ctrl-C> |

## Rules
- **Exclusive resources:** <things one run at a time may use, e.g. "simulator", "gpu: timing runs"; or none>
- **Owner decides:** <e.g. changing the goal; spending; publishing or deploying; irreversible actions>
- **Licences and paths not to touch:** <e.g. no GPL code; never modify ../other-repo>

## Project guidance
- <domain rules each level reads, e.g. "Building: .agents/skills/<project>-engineering">
```
