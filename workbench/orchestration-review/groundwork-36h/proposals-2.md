# Proposed orchestrate changes, second draft

Drafted by the lead session on 2026-11-11 after `review-completeness.md`. Replaces `proposals.md`.

1. **The planner names the ways each item can be reached.** Beside each item in the done-when file, the planner
   writes the routes into it, the states the screen can be in, and the outcomes of the request (success, failure,
   malformed data).
2. **The builder tests every combination on that list before setting the milestone ready for review.** When a fix
   changes a mechanism other things depend on, the builder also tests everything that uses it, and keeps each
   earlier failed review's reproduction as a check that must still pass.
3. **The reviewer covers the whole list, adds anything the planner missed, and writes which combinations it
   tried,** so a later round can tell a situation nobody tested from one that broke after being tested.
4. **When a replan brings in a new mechanism, the planner lists how that mechanism can fail,** and the design
   review checks the list is there.
