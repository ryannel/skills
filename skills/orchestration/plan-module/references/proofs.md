# Ways to prove work

An item is proved by any mix of three things. Give it whichever fields would catch the plausible wrong version of the
work, and add more when one alone wouldn't:
- **`check`:** a command whose exit code decides. The generator runs it, and so does the loop before it accepts a
  claim.
- **`inspect`:** what to capture and look at. The evaluator drives the running product, captures it, and judges the
  result against the statement and the milestone's `bar`.
- **`ask`:** a question the evaluator answers by reading code, a contract or a design.

An item passes only when every field it has passes. A milestone with any `inspect` or `ask` is closed by the
evaluator. One with only `check` items is closed by the checks.

## Kinds to draw on

Combine these freely. A project adds its own kinds in its profile, in the same shape.

| Kind | Field | What to write | Too weak when |
|---|---|---|---|
| Automated test | check | The behaviour, and the command that tests it end to end | It tests the mock, or only the happy path |
| Property or fuzz | check | The invariant, the input space and the run length | The inputs miss what actually occurs |
| Golden output | check | The expected output, the tolerance, and why it's right | The golden file came from the code under test without being checked |
| Benchmark tripwire | check | The measurement and a threshold from the purpose doc or a recorded baseline | The budget was invented, or it ran on a busy or different machine |
| Visual quality | inspect | One quality, and the stills that show it, including edge conditions | Only a beauty shot or one angle, or captures from another build |
| 2D image | inspect | The image's regions and features, each seen whole and as a full-resolution crop, and at the size it's shown | Judged only as a thumbnail, or one condition |
| 3D asset | inspect | The asset's parts, each seen from several angles and distances in its real lighting | One hero angle, or the turntable skips the underside |
| Motion or behaviour | inspect | The motion (physics, animation, simulation) and the scenario that shows it, as a frame sequence | One still, or a slowed or close-up capture |
| User journey | inspect | The steps and states: empty, loading, error and resize for a UI; bad arguments, piped input and exit codes for a CLI | Only the happy path |
| Code or contract | ask | A question with an answer, such as "is every consumer updated for the new contract?" | It asks for an opinion |

## How to inspect

Write the inspection list before capturing anything: the subject's parts, and the views each needs. Views are angles
for 3D, crops and the display size for 2D, plus conditions, and moments for anything that moves. Without a list,
inspection has been random and surface-level. One view also hides what another shows: a bow wave that looks right
from the side can clip through the hull from the front, and a cloud that looks fine as a thumbnail can show banding
in a full-resolution crop. Judge each entry, and keep the list in the review or evidence so the coverage is visible.

## Mixing

Behaviour often needs a measurement and a look, because each catches what the other misses. For buoyancy, a property
test that energy never grows catches drift the eye misses. A frame sequence of a boat in a storm swell catches motion
that is stable but looks wrong.

Agents can't watch live video or hear audio, so anything that moves is captured as frames, and anything an agent can't
perceive is judged by a measurement or reported as `cant_tell`. Golden screenshots are regression tripwires, never
the proof of how something looks.
