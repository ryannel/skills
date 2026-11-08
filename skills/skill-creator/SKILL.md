---
name: skill-creator
description: Creates, rewrites and tests agent skills (a SKILL.md with optional references, scripts and assets) for Claude Code, Codex and other agents, written in plain, explanatory prose. Use when someone wants to make a skill, turn a workflow into one, improve or trim an existing skill, fix one that triggers badly or gets ignored, write its description, or test it against realistic tasks. Not for one-off goals, briefs or AGENTS.md files (instructing-agents).
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

Read [writing](references/writing.md) before you write a word. It covers the folder layout, the description, how
much to put in the body and what to move into references, and the voice.

The short version is this. Write plain, explanatory prose, the way Randall Munroe explains things in "What If?". Use
short sentences and concrete examples, and give the reason with every rule. Start with as little as you can, because
today's models are capable and extra instructions often make them worse. Add a line only for a mistake you've seen
the agent make, or one the person has told you about.

When the draft exists, read it again as if you were the agent seeing it for the first time. Cut anything that agent
already knows, and anything it would do anyway.

## 3. Test it on real tasks

Write two or three prompts a real user would actually type, with the messy details real requests have. Show them to
the person and ask if they're right. Then run each one twice, in fresh subagents: once with the skill, and once
without it (or with the old version, if you're improving a skill). Fresh contexts matter, because anything left over
from this conversation hides gaps in the skill.

While the runs work, write down what a good result must contain, as statements someone could check. Some skills make
things you can check, like a file, a number or a format. Others make things only a person can judge, like writing,
design or advice. Don't force checkable statements onto the second kind. Just show the person the results.

[Testing](references/testing.md) has the folder format for test cases, how to grade runs, and how to test whether the
description triggers.

## 4. Review with the person, then improve

Show the person each prompt with both outputs side by side, plus anything you graded. Ask what they think before you
start fixing things, because their eye is the real test.

When you revise, fix the cause, not the test case. The skill will run on thousands of prompts you'll never see, so a
patch that only makes these three pass is worthless. Read the transcripts as well as the outputs. If every run wasted
time on something, find the line in the skill that sent it there and remove it. If every run wrote the same helper
script, put that script in `scripts/` so the next run doesn't have to.

Then run the tests again, and repeat until the person is happy or the changes stop helping.

## 5. Check the description and package it

The description decides whether the skill ever gets used, so test it on its own. Write about twenty realistic
prompts, with roughly half that should fire the skill and half near misses that shouldn't. Check the description
against them, as [testing](references/testing.md#does-the-description-trigger) explains, and tighten it until the
misses are rare.

Finally, check the folder. Is the frontmatter valid, does every link resolve, and does any script run? Then install
it where the person's agents will find it, as [writing](references/writing.md#where-skills-live) describes.

## What you may do without asking

You can research, read the person's files, write drafts, run tests in subagents, and edit the skill's own folder.
Ask before installing it somewhere shared, publishing it, or running anything that costs money. For example, some
test tools bill every run through the API, and it's worth checking that first.
