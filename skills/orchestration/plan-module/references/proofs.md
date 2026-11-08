# Ways to prove work

Every done-when item is proved in one of three ways, set in its `proof` field:
- **`oracle`:** a command whose exit code decides. The loop reruns it before it accepts a claim.
- **`inspection`:** the evaluator judges captures of the running product against the item and the milestone's `bar`.
  Each inspection item names one quality you can observe. Together, a milestone's inspection items are its inspection
  list.
- **`review`:** the evaluator judges by reading code, a contract or a design.

The kinds below are starting points. Choose whichever kind would catch the plausible wrong version of the work, and
combine kinds when one alone wouldn't catch it. A project adds its own kinds in its profile, in the same shape.

| Kind | Proof | What to write | How it's judged | Too weak when |
|---|---|---|---|---|
| Automated test | oracle | The behaviour, plus the command that runs the test | Exit code on the target | It tests the mock, or only the happy path |
| Property or fuzz | oracle | The invariant, the input space and the run length | Exit code; failing inputs kept as fixtures | The input space misses the inputs that actually occur |
| Golden output | oracle | The output to compare against, the tolerance, and why it's right | Exit code | The golden file was generated from the code under test without being checked |
| Benchmark tripwire | oracle | The measurement, the target, and a threshold from the purpose doc or a recorded baseline | Exit code; the figures go in the evidence | The budget was invented, or it's run on a busy or different machine |
| Visual inspection | inspection | One visual quality per item, and the captures that show it, including edge conditions | Captured stills or frame sequences, judged against the bar in words, never against a target image | Only a beauty shot, or captures from a different build |
| Behaviour plausibility | inspection | The motion or behaviour (physics, animation, simulation) and the scenario that shows it | A frame sequence over the window in question, at real speed and scale | Judged from a single still, or a slowed or close-up capture |
| Interaction walkthrough | inspection | A user journey and its states: empty, loading, error and resize for a UI; bad arguments, piped input and exit codes for a CLI | A screenshot sequence or transcript per step | Only the happy path |
| Code or contract review | review | The question to answer, such as "is every consumer updated for the new contract?" | Reading producers and consumers together | It asks the reviewer for an opinion rather than a question |

Agents can't watch live video, so anything that moves is captured as a sequence of frames. Golden screenshots are
regression tripwires, never done-when items for how something looks.
