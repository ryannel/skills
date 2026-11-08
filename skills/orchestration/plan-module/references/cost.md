# Cost as a design property

Make best-practice decisions for performance up front, build with tripwires, and tune later. Don't invent numeric
budget gates. Record before-and-after figures, and keep the experience intact. The project's own performance policy,
if the profile lists one, takes precedence.

## Design for cost from the start

- **Write a cost account before choosing representations:** counts, frequency, scale and bytes; working set and
  critical path; network round trips, transfers and waits; frequently repeated cheap work as well as obvious hot spots.
  A new module doesn't need a slow implementation first to justify a fast design.
- **Heavy by design is a design defect.** If the mechanism needs redundant fetches, full re-renders, repeated
  serialisation or round trips to reach the experience, the design isn't finished.
- **Specialise where it pays,** when the benefit is real and checkable. Keep the invariants, a fallback and an
  independent check explicit. A simple public interface can hide sophisticated internals.

## Tripwires, not budgets

Investigate when you see: a visible stutter, hitch or delay; about 25% regression against a comparable baseline;
unexpected scaling with input size; growth over a long run in memory or resources.

## Measure honestly

- **Measure an existing path before claiming a gain,** on a representative end-to-end workload. Record build, inputs,
  device or environment, warm-up and conditions. Report tails, not only medians.
- **Shared machines are noisy.** Label contended timings, repeat identical builds before attributing a change, and run
  decisive timings alone (the profile's exclusive resources).
- **Compare fairly:** paired, matched runs, alternating order when drift matters. Several simultaneous changes limit
  attribution.
- **Rerun after integrating.** Isolated benchmarks explain attribution; only the assembled product shows the effect.

## Remove work before weakening quality

Look for exact savings first: reuse with complete invalidation, batching, removing duplicate work. When reducing
fidelity, state what's simplified, the work saved, what the user might notice, and rank reductions by least visible
loss per saving.
