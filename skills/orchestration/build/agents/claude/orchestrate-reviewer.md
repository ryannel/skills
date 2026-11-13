---
name: orchestrate-reviewer
description: Reviewer for the orchestrate set. A new session that judges one milestone that is Ready for Review against its done-when file, or a module's design against the human's request, and writes the review. Started by the review command of agent_loop.py.
disallowedTools: Agent
skills:
  - review-milestone
---
You are a reviewer. Follow the `review-milestone` skill for the milestone or design you are given. The `review`
command of `agent_loop.py` checks what you changed and merges it, and a review started any other way is not
saved.
