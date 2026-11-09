# Ways to prove work

Every done-when item needs some way to prove it. There are three, and an item can use any mix of them:

- `check` is a command. If it exits with 0, it passed. The builder runs it, and the loop runs it again before it
  believes the builder.
- `inspect` says what to look at. The reviewer runs the product, captures it, and judges what it sees against the
  item and the milestone's quality bar.
- `ask` is a question the reviewer answers by reading code, a contract or a design.

An item passes only when everything it uses passes. Which milestones need a reviewer is set out in
[the done-when file](done-when.md#module-donejson).

A quality bar for something that isn't visual works the same way: name a shipped example. "Help text as clear as
ripgrep's" gives a reviewer something to judge against. "Clear help text" doesn't.

Pick whatever would catch a convincing fake. Often one proof isn't enough, because each kind misses different
things. Take a boat bobbing in waves. A test that the energy never grows will catch slow drift that no one would
notice by eye. Watching a frame sequence of the boat in a storm will catch motion that's perfectly stable and still
looks wrong. So that item gets both.

## Kinds to start from

These are starting points, not a fixed list. A project can describe its own kinds in its profile, in the same shape.

| Kind | Uses | What to write | It's too weak if |
|---|---|---|---|
| Automated test | check | The behaviour, and a command that tests it end to end | It tests a mock, or only the happy path |
| Property or fuzz test | check | The rule that must always hold, what inputs to throw at it, and for how long | The inputs miss the cases that happen in real use |
| Golden output | check | The expected output, how close is close enough, and why it's right | The golden file was made by the code it's testing, and nobody checked it |
| Benchmark tripwire | check | What to measure, and a threshold from the purpose doc or a recorded baseline | Someone made the number up, or it ran on a busy or different machine |
| Determinism | check | The same input, run twice, gives the same output (frames, files, results) | It only compares a run with itself in one process, or ignores timing and threads |
| Visual quality | inspect | One quality, and the views that show it | It's one flattering shot, or captures from a different build |
| 2D image | inspect | The parts of the image, each seen whole, cropped at full resolution, and at the size it's shown | It was only judged as a thumbnail, or in one condition |
| 3D asset | inspect | The parts of the model, each seen from several angles and distances, in its real lighting | It's one hero angle, or the turntable never shows the underside |
| Motion or behaviour | inspect | What moves (physics, animation, simulation), and a scenario that shows it, as a frame sequence | It's one still, or a slowed-down or close-up capture |
| User journey | inspect | The steps and their states: empty, loading, error and resize for a screen; bad arguments, piped input and exit codes for a CLI | Only the happy path was tried |
| Code or contract | ask | A question with a real answer, such as "does every consumer handle the new error case?" | It asks for an opinion |

## How to inspect

Before you look at anything, write down what you're going to look at.

This sounds too obvious to need saying. But agents that skipped it looked at whatever caught their eye, decided it
looked fine, and missed the broken parts. So break the thing into pieces first. For a boat, that might be the bow,
the stern, where the mast sits, and the guns. For a cloud, it might be the edges, the lit side, the shadowed side, and
the glow around the sun. For a command-line tool, the pieces are its subcommands, flags, output and failure messages.
For a screen, they're its states and controls.

Then decide how you need to see each piece. A 3D model needs a few angles. An image needs close crops as well as the
whole frame, so use a crop or zoom tool rather than judging a scaled-down copy. Most things need a few conditions,
like different times of day, or the edge conditions the profile lists for the target. Anything that moves needs the
moments where it changes.

You need more than one view because every view hides something. A bow wave can look perfect from the side while
cutting straight through the hull from the front. A cloud can look great as a thumbnail and turn into stripy bands
when you zoom in.

Then go through the list and judge each entry. Keep the list in the review or the evidence, so anyone can see what
was checked and what wasn't.

What you can perceive depends on your tools. Most agents today can't watch live video or hear sound, so capture
anything that moves as a sequence of frames. Prove anything you can't perceive with a measurement, or call it
`cant_tell`. Golden screenshots are good for catching regressions, but
they never prove that something looks right.
