# Which model reads the skill

What to change in a skill when one of the four current models misbehaves with it, and how to move a skill to a
newer model. Checked against Anthropic's and OpenAI's pages on 10 November 2026. Neither vendor publishes skill
advice for one named model, so this is each vendor's prompting advice for the model, applied to a skill.

Contents: [When a skill misbehaves](#when-a-skill-misbehaves) · [Lines written for earlier models](#lines-written-for-earlier-models) ·
[A smaller model reads it too](#a-smaller-model-reads-it-too) · [Moving a skill to a newer model](#moving-a-skill-to-a-newer-model)

All four models always think before they answer. How much they think is a setting on the host, and words in a
skill can't raise it above that setting.

## When a skill misbehaves

Look for the line that caused the behaviour before you add a line against it.

| What you see with the skill loaded | Reported for | What to change in the skill |
|---|---|---|
| The reader asks for approval it doesn't need | Fable 5.2, Astra | Remove cautions that came from habit and not from the project's rules. State each remaining boundary once, with the exact action. Add the line saying what needs no approval |
| The reader asks which instruction to follow, or stops early | Astra | Find two lines that disagree, in this skill or between it and another skill or instruction file, and remove one |
| The reader stops at an error or a timeout, or ends by asking whether to continue | Fable 5.2 | Say that an ordinary obstacle, such as an error or a timeout, is to be worked through, and a deliberate one, such as a protected file, is to be reported. In Anthropic's tests this halved such endings |
| The turn ends on a list of what is left | Opus 5.5 in unattended runs; Fable 5.2 | Say what finished means and give the check. Name the stopping points you don't want. Anthropic found no wording that removes these endings completely |
| The reader returns after a first version | Astra | Put running the result and fixing what fails into what finished means |
| The reader runs more tests than the change needs | Astra; Opus 5 | Remove "always run the tests". Say what check this kind of change needs |
| The reader delegates too much | Opus 5; Fable 5.2 where the text invites it | Remove lines that tell it to use subagents. Say when a subagent is worth its cost |
| The reader delegates too little | Astra | Say when to delegate and how much |
| The reader applies a rule where it doesn't belong | All four | Remove the emphasis from the rule, and give its reason |
| The reader follows the skill at first and drops it later | Claude Code | Reword the guidance to hold for the whole task ("with every change"). Move what matters most to the top |
| The reader misses cases the top model finds | GPT-6.1 Sol | Name the missed pattern in one narrow line |
| The skill loads for tasks that don't need it | All four | Make the description more precise |
| The skill doesn't load when it should | All four | Check the frontmatter parses. Then check the description uses the words people type. Widen it only for a miss you measured |

Anthropic says prompts written for Opus 5 carry over to Opus 5.5, which is why the Opus 5 rows are here.

## Lines written for earlier models

Each of these helped an earlier model. The bracket says what the vendor reports now.

- "IMPORTANT", "CRITICAL", "MUST" and "NEVER" in capitals. (Current Claude models apply the rule too widely.)
- "Take your time", "think step by step", "think hard". (Ordinary text. It can nudge thinking within the host's
  setting and can't raise it above. On Opus 5.5, removing such lines made replies start sooner.)
- "Always run the tests", "double-check your work". (Astra and Opus 5 test more than the change needs.)
- "Use subagents to work in parallel". (Opus 5 and Fable 5.2 delegate for its own sake.)
- "Ask before making changes", written to restrain an earlier model. (Astra stops where the person wanted it to
  continue.)
- "Show your reasoning" or "explain your thinking step by step" in the output. (Current Claude models may
  decline. Read the thinking summaries instead.)
- A description that says to use the skill "whenever" a broad topic comes up. (The skill loads where it doesn't
  help.)

## A smaller model reads it too

Guidance that helps a smaller model can hold a larger one back. If GPT-6.1 Sol or another smaller model misses
something, add one narrow line that names the pattern, and record in the skill's results record which model the
line was for. Check that line again at the next model.

OpenAI's API treats a skill's text as something the user said, not as a system prompt. OpenAI also suggests
telling Astra that the person's instructions take precedence over a skill's guidelines. So on OpenAI's models,
expect the person's request to win where it and the skill disagree.

## Moving a skill to a newer model

Both vendors say to re-read every skill at each new model.

1. Run the skill's test cases on the new model without the skill. Where they pass, the model has caught up with
   what the skill taught, and the skill, or that part of it, is no longer needed.
2. Read the skill as the new model would. Mark every line from the list above, every caution, and every numbered
   step.
3. For each marked line, find out whether it is a requirement of the project or a habit from an earlier model.
   Keep the requirements, in plain words. Remove the habits.
4. Run the test cases with the old version and the new, and show the person both.
5. When a result surprises you, change one thing at a time, so you can tell which change did it.

Both vendors ship a tool that does a first pass of step 2: `/doctor prompt-audit` in Claude Code, and the OpenAI
Docs skill in Codex.
