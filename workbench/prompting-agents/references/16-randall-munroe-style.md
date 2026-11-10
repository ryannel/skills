# The writing style: Randall Munroe's "What If?", without the jokes

- Source read: https://what-if.xkcd.com/1/ ("Relativistic Baseball"), in Chrome on 2026-11-10.
- Second source: the corrections the owner of this repository gave while the orchestration README was being
  rewritten (10 November 2026). They are the working definition of the style here.
- Nothing below quotes the article beyond a few words.

## What the article does

1. It states the setup and its assumptions before anything else. One sentence sets aside the question it won't
   answer (how the ball got that fast).
2. It gives the answer in general terms early, then says what follows is a walk through it.
3. It walks through in time order. Each paragraph is the next thing that happens. Nothing is referred to before it
   has been introduced.
4. Every sentence has a named actor doing something: the ball, the air molecules, the gamma rays, the batter.
   Almost no passives, and no "it is expected that".
5. It explains by contrast with the ordinary case: normally air flows around a moving thing; here the molecules
   have no time to move.
6. Numbers come with a familiar comparison: air molecules move at a few hundred miles an hour, the ball at 600
   million.
7. One analogy where a mechanism is hard to picture (the ball as a rocket flying backwards), then straight back
   to the literal account.
8. Cause is linked to consequence in plain words: "This means that…".
9. Ordinary words. A technical term appears only when it is the name of the thing, and the sentence around it
   says what the thing does.
10. Sentences vary in length. Most are short. None is clipped into fragments.
11. It moves the reader's viewpoint when that helps ("Suppose you're watching from a hilltop").
12. It ends on a concrete last fact, not a summary.

## The owner's rules (each came from a rejected draft)

- Define every term before using it.
- Walk a process as numbered steps, and name who does each step. "The lead runs the `plan` command", never "the
  plan is produced".
- Skip no steps. If the planner cuts a module into milestones, say so; don't begin at "each module is cut into
  milestones".
- Drop no concepts to make the example simpler. A one-module example hid modules.
- A script is not an agent. An agent runs a command; nobody "tells the script to".
- Prefer an explicit, familiar name to a short coined one ("Ready for Review", not "claimed"). But a name is a
  name: a status is a short Title Case label with an information line, not a sentence.
- Shorter is not better. Clear is better.
- A table of labels is not an explanation.

## Why this style suits a prompt

- The reader of a prompt is like the reader of "What If?": intelligent, willing, and without the writer's context.
- Anthropic's final-report advice asks for nearly the same thing: write for an intelligent reader with little
  context, short sentences, one idea each, active voice, the same word for the same thing, no terms made up
  during the work (note 02).
- OpenAI's writing prompt for Astra asks for "familiar words, concrete examples, and precise verbs", active
  voice, the main point early, and no invented compound labels (note 08).
- A named actor in every sentence answers the question an agent most often gets wrong: who is supposed to do this,
  me or someone else?
- A term defined before use is a term the receiving agent does not have to guess.

## What "without the jokes" removes

- The footnote asides, the absurd premise, the comic last line. The clarity does not depend on them.
