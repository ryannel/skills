---
name: skill-creator
description: Creates, rewrites and tests agent skills for Claude Code, Codex and other agents, in plain explanatory prose. Use when someone wants to make a skill, turn a workflow into one, improve, trim or fix one that triggers badly, or test one on realistic tasks. Not for one-off goals, briefs or AGENTS.md files (instructing-agents).
license: Apache-2.0. Adapted from Anthropic's skill-creator; see LICENSE.txt.
---

# Skill creator

A skill is a folder of instructions an agent loads when a task calls for it. A good one makes the agent noticeably
better at that task, and costs as little attention as possible. This skill helps you make one, from the first
conversation to a tested, installable folder.

The process has five parts. You won't always need all of them, so start wherever the person is. Someone with a
finished draft wants testing, not an interview. Someone who says "just vibe with me" wants a draft and a chat, not
benchmarks.

## 1. Understand what the skill is for

Find out what the agent should be able to do, when the skill should fire, and what a good result looks like. If the
conversation already contains the workflow ("turn what we just did into a skill"), take the answers from it: the
steps that worked, the tools used, and the corrections the person made along the way. Those corrections are the most
valuable part, because they're the mistakes the agent makes without help.

Ask about the edge cases, the inputs, and how the person would tell a good result from a bad one. Then fill the gaps
yourself. Look at how others have solved the same problem, and check whether a similar skill already exists.

## 2. Write the draft

Read [writing](references/writing.md) before you start. It covers the folder, the description, what goes in the body
and what moves to references, the voice, and the host facts that change.

Draft the skill somewhere agents don't scan for skills, like a scratch folder, until testing is done. Otherwise the
draft leaks into runs that are supposed to go without it.

When the draft exists, read it again as if you were the agent seeing it for the first time. Cut anything that agent
already knows, and anything it would do anyway.

## 3. Test it on real tasks

Write two or three prompts a real user would actually type, with the messy details real requests have. Show them to
the person and ask if they're right. Then run each one with the skill and without it (or against the old version, if
you're improving a skill), in fresh subagents. Fresh contexts matter, because anything left over from this
conversation hides gaps in the skill.

The run without the skill has to really be without it. A subagent can load any installed skill on its own, so turn
the skill off for that run and check its transcript afterwards. One run of each is a smoke test. When you're
comparing two versions, run each two or three times, because results vary.

While the runs work, write down what a good result must contain, as statements someone could check. Some skills make
things you can check, like a file, a number or a format. Others make things only a person can judge, like writing,
design or advice. Don't force checkable statements onto the second kind. Just show the person the results.

[Testing](references/testing.md) covers the test-case format, isolation, grading, the results record, and how to
test whether the description triggers.

## 4. Review with the person, then improve

Show the person each prompt with the outputs side by side, plus anything you graded. Ask what they think before you
start fixing things, because their eye is the real test.

When you revise, fix the cause, not the test case. The skill will run on thousands of prompts you'll never see, so a
patch that only makes these three pass is worthless. Read the transcripts as well as the outputs. If every run wasted
time on something, find the line in the skill that sent it there and remove it. If every run wrote the same helper
script, put that script in `scripts/` so the next run doesn't have to.

Then run the tests again, and repeat until the person is happy or the changes stop helping.

## 5. Check the description and package it

The description decides whether the skill ever gets used, so test it on its own, in real sessions where the skill is
installed. [Testing](references/testing.md#does-the-description-trigger) explains how.

Then run `python3 scripts/check_skill.py <skill-folder>` from this skill's folder. It checks that the frontmatter is
valid YAML, the name and description limits, every relative link and anchor, and contents lists on long references.
Without PyYAML installed its YAML check is a strict scan rather than a parser, so also run `claude plugin validate`
where you have it. These are the mistakes that
make a skill fail silently: a skill whose frontmatter doesn't parse still loads, but with no description, so it never
fires. Install it where the person's agents will find it, as [writing](references/writing.md#where-skills-live)
describes.

## What you may do without asking

You can research, read the person's files, write drafts, run tests in subagents, and edit the skill's own folder.
Ask before installing it somewhere shared, publishing it, or starting headless model runs such as `claude -p` or
`claude plugin eval`. Those use the person's quota or credits.
