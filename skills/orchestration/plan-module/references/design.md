# The design

One design governs each module. The plan, the done-when file and the evaluator check against it, so keep it reading as
what is true now: revise sections in place rather than appending amendments, and leave history to git. Keep it as short
as the module allows; detail can live in linked research notes.

A design for a substantial module usually covers:

- **Purpose and scope:** what it's for, its consumers, what's commissioned now and what's deferred.
- **Experiences:** what the user must see, feel or get, each with its operating range (data sizes, devices, network
  conditions, speeds, input variety) and the quality bar it's judged against, in words.
- **Techniques and evidence:** the chosen mechanisms, the alternatives considered, what shipped products and current
  research show, and the check that each mechanism produces its behaviour across the range. Say what would change each
  decision.
- **The system as it runs:** state and its single owner, representations, data flow and update order, handoffs and
  contracts with neighbours, and one normal use walked through in order with its cost.
- **Risks:** the likeliest ways this fails, the early sign of each, and the plausible wrong substitute for each key
  behaviour (what could look right while missing it).
- **Cost:** the cost account, tripwires and how cost is measured ([cost](cost.md)), where performance matters.
- **Open questions:** what's undecided, and the experiment or milestone that will settle it.

## Getting there

- **Research first.** Find how the best shipped products and current published work do this, and why. Prefer current
  state-of-the-art over older techniques that merely have code available.
- **Prove the mechanism can make the behaviour** before planning on it. A short reproduction outside the product (a
  script, a spike, the core algorithm with real inputs) often settles in minutes what building settles in days.
- **Design the whole module, then cut milestones.** Milestones taken from a build order of effects tend to grow without
  a criterion that moves.
