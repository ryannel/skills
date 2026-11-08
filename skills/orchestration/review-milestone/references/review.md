# Independent review

Review catches what the author can't see. Design, code correctness, visual and interaction quality, and performance
claims are different questions; say which one a review answered and which revision it inspected. Choose depth by
consequence and uncertainty, not by a quota.

## Brief reviewers so they stay independent

Give a fresh reviewer the original requirements, the use cases and the raw artifacts (code, design, captures,
measurements). Don't give it your preferred technique, expected verdict or research conversation: an agent handed a
hypothesis tends to confirm it. Ask neutral questions. Self-checks are not independent review. If a reviewer
contributes a new mechanism, another reader verifies it. Reviewers don't claim a full read of scope they didn't inspect.

Ask for everything that fails the criteria, ranked, each finding marked verified (file and line, a reproduction or a
capture) or suspected. Act on verified findings; investigate suspected ones before relying on them.

## The two reviews that matter most

- **The design and plan, before building on them.** Give the reviewer the brief (what the module is for, its
  consumers, the required experiences and constraints, without your design) and have it derive what the module must do,
  then compare with the design and plan: omissions, unsupported additions, mechanisms not shown to produce their
  behaviour, milestones that wouldn't show it, a milestone too large to reach a user soon, and proof that pursues
  precision beyond what changes what the user experiences.
- **Each milestone, on its target.** Give the reviewer the done-when file and the raw captures and logs for one build,
  not your summary. A reviewer that can't play video gets a frame or screenshot sequence over the window in question.
  It says, per item, pass, fail or can't tell, and whether it saw motion or stills.

A verdict applies only to the revision or build it saw.

## What to challenge

- **Technique choice,** when the choice is made, not after days of building on it. Can the mechanism produce every
  defining behaviour across the operating range? Which current alternatives were missed? Is it heavy or dated by
  design?
- **Coverage.** Derive the capabilities and interactions from the brief first, then compare. Keep omissions,
  unsupported additions and incompatible couplings separate. An explicit, safe deferral isn't an omission.
- **Composition.** Walk a normal use and a coupled interaction through the actual producers and consumers. Where would
  an implementer still have to invent a mechanism, query or ordering?
- **Plausible wrong substitutes.** Does the mechanism produce the requested behaviour, or only its appearance (a
  spinner for loading, canned data for a real query, an animation for a state change)? Could it pass the author's
  checks while missing the goal?
- **Range and shortcuts.** Fixed sizes, hard-coded values, single-environment assumptions, happy-path-only handling.
- **Code across boundaries.** Read callers, shared data, fixtures, lifecycle and tooling together. Look for duplicate
  producers, mismatched clocks or encodings, dead alternative paths, unbounded retries, needless round trips and
  repeated work.
- **Visual and interaction output.** Inspect captures directly; state what you saw, at what size and from which build.
  Judge each indispensable behaviour separately against the inspection list and bar; good looks don't compensate for
  wrong behaviour. Cover transitions, where faults hide. Diagnose the responsible layer
  ([diagnosis](../../build-milestone/references/diagnosis.md)) rather than prescribing cosmetic fixes.
- **Performance claims.** Challenge benchmark identity and fairness, tails, equivalence claims, actual saved work and
  contention on shared machines ([cost](../../plan-module/references/cost.md)).

## Close the loop

A finding names the affected decision or location, the defect or unsupported claim, the evidence, the consequence, and
what would resolve it. Mark objections you can't yet prove as suspected, and say why each changes the decision.

The author then revises, supplies evidence, rejects the finding with reasons, or records a genuine open decision with a
discriminating experiment. Fix the class a finding belongs to, not only the instance: search the change for the same
kind of fault. A resubmission answers each point of the latest verdict. Narrowing a claim removes an overclaim; it
doesn't deliver the excluded experience. Agreement on a design is not evidence of running behaviour, quality or cost.

## Calibration: failures that pass an author's own checks

Look for these first. The project's graded examples add its own.

- **Tuning a mechanism that can't produce the behaviour.** Hours of parameter work on something a short reproduction
  would have shown was the wrong model.
- **Correct but imperceptible.** Technically right, but unreadable or unnoticeable where the user actually is.
- **Judged in the lab.** Looks right on a fast machine, a close-up or a slowed capture, and fails at real speed, size or
  network.
- **A plan that only grows.** Amendments pile up and no criterion moves.
- **Trials without a governing question.** Many attempts that hold the plausible causes fixed.
- **Swinging between cost-only and quality-only work,** producing designs that are heavy by design.
- **Attractive output without the behaviour.** The appearance of a feature standing in for the feature.
- **Paperwork displacing the defect.** Notes grow while the visible defect stays.
- **Verdicts from descriptions.** Techniques endorsed from their write-ups, or another reviewer's pass relayed as fact.
