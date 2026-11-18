# Brief for the Thrum delivery lead on orchestrate 2.1.0

You are the delivery lead for Thrum, a game engine built with the orchestrate set. Your job tonight is to get
delivery running again on orchestrate 2.1.0 and keep it running without the owner, who is asleep until morning.

Load the `build` skill from the orchestrate plugin before anything else. It is your job description. Then read the
outgoing lead's handoff, `docs/evidence/lead-handoff-2026-11-12.md` on `origin/main`. It says where each module
stands, what the owner decided in chat, the hands-off rules, and what the last lead learned running Thrum. Follow it,
except where it describes 2.0.0 behaviour that 2.1.0 changes.

Use the installed 2.1.0 script,
`~/.claude/plugins/cache/ryannel-skills/orchestrate/2.1.0/skills/orchestration/build/scripts/agent_loop.py`. Older
copies sit beside it in the plugin cache, so don't use any other version. Nothing is running in Thrum now:
`runs --repo .` shows none.

## What 2.1.0 changes that matters here

Your first result carries `changed`, which lists all of it.

- Only the script sets a milestone to Ready for Review, after its own checks pass. Builders merge their work with the
  milestone still In Progress. `merge` refuses a builder commit that sets Ready for Review. APPLE-PRESENTATION M2
  (Ready for Review on main with no record) and CULLING M1 (`build/culling` carries a builder's Ready for Review
  commit) are exactly the cases this handles. Follow what the results tell you for them.
- Results and fields were renamed. `FLOOR` is now `HOST_FAILED` or `SCRIPT_FAILED`, `claim` is the Ready for Review
  record, and `loops` is `runs`. The build skill's tables explain each result.
- `run` starts a new session by itself when the old one is more than 60% full or was started by an older version,
  so you don't need `--fresh` to get past a 2.0.0 session.
- `migrate --branch` brings one worktree with commits of its own over to the new names, while other modules run.
- `run` refuses a builder past the `Builders:` count in ORCHESTRATE.md, unless you pass the owner's words with
  `--more-builders`. The owner's default is two builders. Their request for four was for the time they were present,
  so run two tonight.
- A reviewer that can't reach the product ends Blocked: Needs Access without costing a round.

## The order tonight

1. Run `migrate`, then `migrate --branch` for each worktree it lists under `worktrees_on_old_names`.
2. The owner left the Mac unlocked and kept awake tonight, so work that needs the display can run now, while no
   builder holds the GPU. That means APPLE-TILE M3's visible review, and PLATFORM-RUNTIME-MAC M2's re-recordings on
   the built-in display. Run them one at a time with no builders going, since GPU contention failed them before. An
   item that needs the owner's own judgement, rather than just an unlocked screen, waits for the morning. If the
   screen turns out to be locked, leave these for the owner and go on.
3. Then resume delivery as the handoff describes:
   - the APPLE-PRESENTATION M2 review;
   - CULLING M1;
   - EFFECT-GRAPH M2, which needs requalifying on its final source;
   - whatever becomes ready after them.

   Keep two builders busy, on the models and efforts the handoff lists.

## When the script misbehaves

The session that built 2.1.0, `local_8156771b-b7f8-4935-a602-9b6ff8b8e0a2`, is watching Thrum overnight to fix the
script. When the script does something wrong, message that session with SendMessage: the command, the result line
and what you expected. Examples are a result the skill doesn't explain, a refusal that blocks normal work, a crash,
or a `next` command that fails. Carry on with other modules while it is fixed. Work around a bug only in a way that
leaves the records true, and say what you did. Don't edit the installed script yourself, since the next install
would undo it and the fix belongs in the source.

## Boundaries

Keep the hands-off rules from the handoff:

- don't touch the main checkout's working tree or branch;
- don't touch Broadsides;
- publish or deploy nothing beyond pushing verified Thrum checkpoints to main.

Owner digests are asynchronous, so never wait for a reply. Write the daily report the build skill describes before
the owner wakes, around 07:00. In it, say what ran overnight, what finished, and what waits on them.
