# Changing the project settings

The lead writes a line in `ORCHESTRATE.md` when the user asks for one: how they want the agents to work before the
first build, or a model or an effort for one kind of agent later. The forms are in
[the settings reference](../../planner/references/profile.md).

`adopt` won't merge a changed `ORCHESTRATE.md`, because the settings carry the user's permissions. So commit it with
git in the main working copy, on the main branch, and push it when the settings say `Merge: push`.

A worktree or module branch whose copy is only behind the main branch's then runs on the main branch's settings,
and its result says so in `settings_read_from`. A branch that changed its own copy keeps reading that copy. `ready`
lists a working copy whose settings differ from the main branch's under `settings_differ`.

Each result's `ran_on` says what the script asked the host for, and the records save what the host ran on as
`observed`. A turn that ran on something else stops with `WRONG_MODEL_OR_EFFORT`. Check `ran_on` in the next result
before you tell the user a change has taken effect.
