# Diagnose a fault at its system boundary

Use this when a wrong result, mismatch, weak behaviour or unstable interaction might come from the model, the representation,
ownership or integration rather than from a local bug. The outcome is a correction at the responsible layer that
restores the intended behaviour, verified across its consumers. A local bug can still have a local fix.

## Find the cause before changing parameters

- **Reproduce first.** Use known inputs and a known build. Hold inputs, data and environment constant where
  that helps, and compare intermediate state, not only the final output. Separate a local fault from a system-wide
  stall.
- **Ask whether the model can produce the missing behaviour at all.** Reproduce the core equations outside the engine,
  for example in a short script with the real inputs and constants, and compare the result with the expected behaviour
  and a reference. This often settles in minutes what iteration in the product doesn't settle in hours.
- **Trace the path.** Follow it from source through state, transforms and composition to every important
  consumer. Ask who owns the quantity and whether another path derives a conflicting version. A visible
  fault can start upstream in timing, encoding, caching, sampling or resource lifecycle.
- **Look for one shared cause.** When several symptoms appear together, such as stale data, missing updates after
  navigation and a flicker on load, look for a common cause before fixing each one: a frozen input, a cache that never
  invalidates, a filter cancelling the signal, or state that stops updating after an error.
- **Classify the failure:**
  - an implementation mistake;
  - a missing or incompatible mechanism;
  - missing input or content;
  - calibration;
  - a representation or scale error;
  - a presentation fault;
  - a lifecycle fault (stall, reset, resize, reconnect, device or session loss).

  Correct it at that layer. Damping a response, turning a term off or adding noise can isolate a defect or hide it;
  keep such a change only if it restores the intended contract.
- **Bound the next experiment.** After a negative result, choose a bounded experiment that can change the responsible
  decision; it counts toward the [stop rule](../SKILL.md#staying-on-course). Don't run a more expensive version of the
  same test. More resolution can't supply an absent mechanism or
  fix another quantity's calibration.

## Make shared representations explicit

For each quantity that crosses a boundary, state:
- its source or band;
- units and frame of reference;
- spatial and temporal support;
- physical time;
- encoding;
- composition rule;
- each consumer's fidelity.

Where consumers must agree, use one authority. Others may approximate it within a stated bound.

- **Derived quantities follow their source.** A cached or derived value must invalidate when its source changes.
- **Never count a contribution twice,** or amplify a weak signal until it resembles the target.
- **Shared resources live where they're reused,** for example as a shared service or cache, not allocated by
  every instance.

## Verify the correction

- **Test against a reference.** Write tests that expose the broken relationship, with an analytic or independent
  reference where one is meaningful. Two evaluators that share an omission can't bound it.
- **Exercise the conditions.** Cover edge inputs, timing, mixed contributions, size changes,
  failures and fallback paths.
- **Look again.** Re-inspect the ordinary output, in motion where it moves, and the adjacent consumers, and measure the
  cost.
- **Record what you learnt.** Record what the ablation established, why the repair preserves the design, and what
  remains unproved.
