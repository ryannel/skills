"""Every prompt the script sends, rendered from fixed data and kept as a text file in prompts/, so a change to a
template or to the text the script adds shows as a readable diff for the human to review.

When a change is intended, write the new copies with
    ORCHESTRATE_WRITE_PROMPTS=1 python3 -m unittest tests.orchestration.test_prompts
and commit them with the change."""

import os
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import Clean, agent_loop  # noqa: E402

PROMPTS = Path(__file__).resolve().parent / "prompts"
LOOP = Path("/skills/orchestration/build/scripts/agent_loop.py")
PROF = {"plans": "docs/plans", "evidence": "docs/evidence", "merge": "push", "remote": "origin", "branch": "main",
        "test_command": "./dev check", "exclusive resources": "gpu: timing runs and captures",
        "bounds": {"Licences and paths not to touch": "no GPL code", "Owner decides": "spending and publishing"}}
MILESTONE = {"id": "M2", "items": [
    {"id": "M2.1", "status": "pass"},
    {"id": "M2.2", "status": "open", "needs": {"type": "human_feedback", "what": "does the tile animation read as smooth"}},
    {"id": "M2.3", "status": "open", "needs": {"type": "hardware", "what": "an iPhone connected over USB"}}]}
FEEDBACK = [{"at": "2026-11-10T08:37:00Z", "items": ["M2.2"], "asked": "Is the resize smooth enough to ship?",
             "said": "Looks good to me, but the corners flicker once."}]
ROUND = {"verdict": "fail", "at": "2026-11-09T21:00:00Z", "counts": True,
         "review": "docs/evidence/APPLE-TILE/M2-review.md",
         "findings": [{"name": "corner flicker on resize", "item": "M2.2"},
                      {"name": "log written to the worktree", "repeat": True}]}


def build_prompt(host: str, headless: bool, lead: str, feedback: bool, earlier: bool, needs: bool,
                 resources: bool, rules: list[str]) -> str:
    """A builder's first prompt, as the script builds it."""
    prof = {**PROF, "exclusive resources": PROF["exclusive resources"] if resources else ""}
    note = agent_loop.handoff_note(agent_loop.handoff_rel(prof, "APPLE-TILE", "M2"), "M2") if earlier else ""
    return agent_loop.build_prompt(host, headless, prof, "APPLE-TILE", "M2", MILESTONE if needs else None, lead=lead,
                                   feedback=FEEDBACK if feedback else None, earlier=note, rules=rules)


def prompts() -> dict[str, str]:
    """name -> the prompt, for every kind of prompt the script sends."""
    out = {}
    out["build-codex-headless-full"] = build_prompt(
        "codex", True, "The human said at 08:37 they would be away until noon. The lock on gpu is held by the "
        "APPLE-PRESENTATION builder's capture; that is normal.", True, True, True, True, ["never modify Broadsides"])
    out["build-claude-visible-plain"] = build_prompt("claude", False, "", False, False, True, False, [])
    out["build-resumed-restatement"] = agent_loop.binding(
        PROF, "build", "M2", MILESTONE, "docs/plans/APPLE-TILE/DONE.json", rules=["never modify Broadsides"])[0]
    out["build-resumed-after-the-lead-wrote"] = "The console is unlocked now.\n\n" + agent_loop.binding(
        PROF, "build", "M2", MILESTONE, "docs/plans/APPLE-TILE/DONE.json", lead_spoke=True)[0]
    with mock.patch.object(agent_loop, "git", lambda *a: mock.Mock(stdout="9f3c2a1 (\"Cache decoded tiles by zoom\")")), \
            mock.patch.object(agent_loop, "worktree_jobs", lambda *a, **k: [
                {"id": "20261112-071500-4242", "age": "1h05m", "command": "./dev capture valley --realtime",
                 "log": "/repo/.git/orchestrate/jobs/20261112-071500-4242.log"}]):
        out["build-resumed-after-turn-limit"] = "Continue the objective." + agent_loop.open_items(MILESTONE) + " " + \
            agent_loop.resume_facts(Path("/repo"), MILESTONE, 124, 2.0)
        # what a new session that takes over from a full or old one is told, in the first prompt's {earlier}
        out["build-new-session-note"] = agent_loop.earlier_session_note(Path("/repo"), MILESTONE, 124, 2.0,
                                                                        "origin/main", "M2")
    out["build-not-ready"] = agent_loop.not_ready_message(
        "`./dev check` exited 1: error: tile_cache.rs:88: index out of bounds",
        Path("/repo/.git/orchestrate/verify/APPLE-TILE"))
    # what `merge` prints, and what a builder's first prompt says, when a builder's commits set the state, which only
    # the script sets since 2.1.0
    set_state = [("docs/plans/APPLE-TILE/DONE.json", "M2", "ready_for_review")]
    out["merge-refused-state"] = agent_loop.state_refusal(set_state)
    out["build-old-branch-note"] = agent_loop.state_refusal(set_state, old_branch=True)
    out["review"] = agent_loop.review_prompt(
        "claude", PROF, "APPLE-TILE", "M2", "a6101020", "docs/plans/APPLE-TILE/DONE.json",
        "docs/evidence/APPLE-TILE/M2-review.md",
        {"id": "M2", "items": [{"id": "M2.1", "check": "./dev test tiles"}, {"id": "M2.2"}]},
        {"ready_for_review": {"checked": "b7c2e91d04aa"}, "reviews": [ROUND]}, FEEDBACK,
        [{"why": "the reviews judged the capture tooling, not the tiles", "at": "2026-11-10T12:00:00Z"}])
    out["review-restatement"] = agent_loop.binding(PROF, "review", done="docs/plans/APPLE-TILE/DONE.json",
                                                   review="docs/evidence/APPLE-TILE/M2-review.md")[0]
    out["design-review"] = agent_loop.review_prompt(
        "claude", PROF, "APPLE-TILE", "design", "HEAD", "docs/plans/APPLE-TILE/DONE.json",
        "docs/evidence/APPLE-TILE/design-review.md", None, {}, None, [],
        context="Since the last design review (docs/evidence/APPLE-TILE/design-review.md), M2.2 changed.",
        design=True)
    out["plan"] = agent_loop.PLAN_TEMPLATE.format(
        task="Plan module APPLE-TILE. The human said on 9 November: \"tiles should load as you scroll, never "
             "all at once\".", skill=agent_loop.skill_note("plan-module", "claude"), loop=LOOP)
    with mock.patch.object(agent_loop, "review_history", lambda *a, **k: agent_loop.history_lines({"reviews": [ROUND]})), \
            mock.patch.object(agent_loop, "review_files", lambda *a, **k: (
                ["docs/evidence/APPLE-TILE/M2-review-1.md", "docs/evidence/APPLE-TILE/M2-review.md"], False)):
        out["planner-diagnosis-task-repeated-finding"] = agent_loop.diagnosis_task(
            "APPLE-TILE", "M2", {"failed_reviews": 4, "failed_reviews_with_repeat": 4}, PROF, Path("/repo"))
        out["planner-diagnosis-task-new-findings"] = agent_loop.diagnosis_task(
            "APPLE-TILE", "M2", {"failed_reviews": 6, "failed_reviews_with_repeat": 1}, PROF, Path("/repo"))
    out["planner-after-design-changes"] = agent_loop.design_review_next(
        {"verdict": "DESIGN CHANGES", "review": "docs/evidence/APPLE-TILE/design-review.md",
         "line": "DESIGN CHANGES: 2 must_fix findings"}, "APPLE-TILE", Path("/repo"), PROF)["command"]
    blocked = {"reason": "needs_dependency", "what": "CORE has no save API yet",
               "handoff": "docs/evidence/APPLE-TILE/M2-handoff.md",
               "work": {"branch": "build/apple-tile", "commit": "7911c75b" + "0" * 32}}
    out["planner-needs-dependency"] = agent_loop.next_for(
        {"module": "APPLE-TILE", "milestone": "M2", "status": "blocked", "reason": "needs_dependency",
         "blocked": blocked}, Path("/repo"), PROF)["command"]
    out["claude-review-or-plan-turn-note"] = agent_loop.CLAUDE_TURN_NOTE
    out["findings"] = agent_loop.FINDINGS_TEMPLATE.format(milestone="M2", module="APPLE-TILE",
                                                          evidence="docs/evidence")
    return out


class PromptCopies(Clean):
    def test_every_prompt_matches_its_saved_copy(self):
        with mock.patch.object(agent_loop, "LOOP", LOOP):
            # the skill files' folder, written the same on every machine
            rendered = {k: v.replace(str(agent_loop.SKILLS), "/skills/orchestration") for k, v in prompts().items()}
        if os.environ.get("ORCHESTRATE_WRITE_PROMPTS"):
            PROMPTS.mkdir(exist_ok=True)
            for old in PROMPTS.glob("*.txt"):
                if old.stem not in rendered:
                    old.unlink()
            for name, text in rendered.items():
                (PROMPTS / f"{name}.txt").write_text(text.rstrip("\n") + "\n")
        for name, text in rendered.items():
            saved = PROMPTS / f"{name}.txt"
            self.assertTrue(saved.exists(), f"{saved} is missing; write it with ORCHESTRATE_WRITE_PROMPTS=1")
            self.assertEqual(saved.read_text(), text.rstrip("\n") + "\n",
                             f"{name} changed; review the diff, then rewrite the copies with ORCHESTRATE_WRITE_PROMPTS=1")


if __name__ == "__main__":
    unittest.main()
