# Anthropic: Improving skill-creator (test, measure and refine Agent Skills)

- URL: https://claude.com/blog/improving-skill-creator-test-measure-and-refine-agent-skills
- Published 3 March 2026. Read in Chrome on 2026-11-10. Paraphrased.
- It predates Opus 5.5 and Fable 5.2 by months, but it is where Anthropic explains why its skill-creator tests
  skills the way it does.

## Two kinds of skill

| Kind | What it is | Why you test it |
|---|---|---|
| Capability uplift | Teaches the model to do something it can't do, or can't do consistently. Anthropic's document skills are examples | A newer model may no longer need it. If the test cases pass without the skill loaded, the skill's techniques have become the model's default behaviour. "The skill isn't broken; it's just no longer necessary" |
| Encoded preference | The model can do each piece already. The skill puts the pieces in the order a team uses, such as reviewing an NDA against the team's criteria | It lasts longer, but is only worth as much as it matches the real workflow. Tests check that match |

## What the tests are for

1. Catching a regression. A skill that worked last month may behave differently on a new model or a changed
   harness.
2. Learning that the model has outgrown the skill (the capability-uplift case above).

## What skill-creator added

- Test cases: a prompt, files if needed, and a description of what good looks like.
- A benchmark that records pass rate, time and tokens, to re-run after a model update or an edit.
- Independent agents for the runs, each in a clean context with its own token and time counts, so one run's
  context doesn't leak into the next.
- Comparator agents for a blind comparison of two versions, or of skill against no skill. They judge without
  knowing which output is which.
- Description tuning against sample prompts, to cut both false triggers and misses. They report better triggering
  on five of their six public document skills.

## Their forecast

Today a `SKILL.md` is "essentially an implementation plan". As models improve, a plain description of what the
skill should achieve may be enough, with the model working out the rest. The test cases already describe the
"what", and may eventually be the skill.
