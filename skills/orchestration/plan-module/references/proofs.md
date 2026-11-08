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

Unplanned looking is random and stays on the surface, so write the list before capturing anything. This works the
same for 3D scenes, 2D images, UI and motion:

1. **Break the subject into its parts and behaviours.** A 3D boat has a bow, a stern, mast placement, rigging, guns
   and a hull at the waterline. A bow wave has a crest at the stem, spray, a foam trail, a join with the hull, and a
   change with speed. A cloud image has silhouettes and edges, the lit and shadowed sides, the sun's glow and silver
   lining, the thin wisps, the layering against the sky, and the horizon. A screen has its regions and states.
2. **Say how each part has to be seen.** For 3D, that's the angles (front, side, three-quarter, above, below the
   waterline). For a 2D image, it's the views: the whole frame, crops of each region at full resolution, and the
   size it's actually seen at. Then add:
   - the distances or zoom levels, from close-up to far away;
   - the conditions (calm, storm, low sun, night, every time of day the clouds must hold up in);
   - for motion, the moments (at rest, accelerating, turning; a cloud forming, drifting and dissolving).

   One view hides what another shows. A bow wave that looks right from the side can clip through the hull from the
   front. A cloud that reads well in a thumbnail can show banding or tiling in a full-resolution crop.
3. **Capture each entry, then judge each one** against the item's statement and the `bar`, and record a verdict per
   entry.

The list goes in the review file, or in the evidence for the generator's own look, so anyone can see what was
covered and what wasn't. The planner's `inspect` field names the quality to judge and may seed parts; whoever
inspects completes the list.

## Mixing

Behaviour often needs a measurement and a look, because each catches what the other misses:
- **Buoyancy:** a property test that energy never grows (`check`), plus a frame sequence of a boat in a storm swell
  (`inspect`). The test catches drift the eye misses. The eye catches motion that is stable but looks wrong.
- **A sign-up flow:** a Playwright test of the journey (`check`), plus a mobile screenshot sequence of every
  validation state (`inspect`).
- **A contract change:** the shared test suite (`check`), plus "does every consumer handle the new error case?"
  (`ask`).
- **A CLI command:** golden output for the standard cases (`check`), plus a transcript of bad arguments, a piped
  stream and Ctrl-C (`inspect`).

Agents can't watch live video or hear audio, so anything that moves is captured as frames, and anything an agent can't
perceive is judged by a measurement or reported as `cant_tell`. Golden screenshots are regression tripwires, never
the proof of how something looks.
