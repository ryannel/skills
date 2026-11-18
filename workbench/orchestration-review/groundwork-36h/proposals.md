# Proposed orchestrate changes after the groundWork 36-hour record

Drafted by the lead session on 2026-11-11 from `delivery-record.md` and the orchestrate 1.7.1 source.

1. **Fix the class, not the instance.** Each Must Fix carries a `class` (for example "views read different
   revisions"). Before the next claim, the builder lists every place in the code where that class could occur and
   records the sweep as evidence. The script counts a matching class as a repeat, so a run like INTEGRATION-ROLLUPS
   M2 reviews 5–8 (all shared pointer targets) reaches the replan step at once instead of looking like new findings.
2. **Builder self-review before claiming.** The builder starts a fresh subagent that runs the items' edge
   conditions before it sets Ready for Review, because a formal review costs about 7–9M tokens plus another
   builder round.
3. **Ask the owner about cost at the replan.** When a planner rewrites a milestone, it names the requirement
   driving the failures and asks the owner to keep, cut or change it. SHARED-UI M3's mounted-state preservation
   was kept at the replan and relaxed by the owner about 3 hours later.
4. **Rotate builders after two claims.** A fresh session gets the latest review and the class sweep, instead of
   one session growing to 35–69M cached tokens.
5. **Operational hardening.** A stall timeout that kills and restarts a stage with no output for N minutes; refuse
   a resume while another session writes to the thread; the script formats its own ledgers; no file-layout
   migration while a module is mid-milestone.
6. **Record cost in the ledger.** Every verdict and session gets session id, version, start and end time and
   tokens, and a `report` command produces the delivery record.
