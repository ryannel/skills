# APPOINTMENT_PAGE design review

Result: **DESIGN OK**. No Must Fix findings; three Suggestions.

## Basis and scope

Reviewed the integrated checkout at `bb1ebc7`, using the supplied review-milestone skill's “Reviewing a design” procedure. Read `ORCHESTRATE.md` first, the complete `briefs` array in `APPOINTMENT_PAGE-ACCEPTED.json` (one original task, no retry or re-plan tasks), then `BRIEF.md`, `ARCHITECTURE.md`, `GLOSSARY.md`, the module design, plan and every done-when item. Also read the BOOKINGS design and items to check the boundary, and the existing source and package scripts to distinguish planned mechanisms from existing behavior.

There is no previous design review or project graded-examples file in this checkout. Used the skill's starting graded examples. This is a design review: no implementation tests or browser demonstrations were run, and no captures were needed. The current source is only the booking constructor and email subject; the planned page, store and demo are not yet delivered. Approval here does not certify those implementations.

## Findings

### 1. Suggestion — identify the public phone-number source for an unknown link

Verified documentation ambiguity: `APPOINTMENT_PAGE.md:22` requires the unknown-link screen to give the phone number, while `ARCHITECTURE.md:31` returns nothing for an unknown token. The successful lookup carries the salon details, but the unknown lookup cannot supply them.

Before building, clarify how the server obtains public salon metadata independently of an appointment, for example by supplying the configured salon name and phone at server startup. An unknown token should still show the configured phone number and no appointment details. This is a small wiring clarification, not a blocker: the existing boundary restricts appointment reads and writes and makes BOOKINGS the sole settings writer; it does not prohibit passing public settings into page rendering. No change to appointment access is needed.

### 2. Suggestion — make the HTTP journey proof explicitly follow the rendered forms

At `APPOINTMENT_PAGE-DONE.json:49`, the statement already requires moving “through the page alone,” and M2.4 requires real BOOKINGS integration. Make the intended test method explicit: obtain each action and submitted value from the returned HTML, follow the confirmation form without JavaScript, then re-open the private link to verify the stored result. Exercise both the default stylist and an explicitly selected alternative.

This would make it harder for a test to post directly to a working endpoint while the page's actual form has a wrong action or missing field. It sharpens an already judgeable requirement; such a broken form would violate the current statement and should also be found when driving the real page during M2.5/M2.6.

### 3. Suggestion — spell out the slow-network inspection and reproducible refusal fixtures

`ORCHESTRATE.md` includes slow network among the web-mobile edge conditions. M2.5 lists all ten designed page states, but its inspection text does not name the delayed-response scenario. Explicitly include a delayed confirmation response and repeated taps/back-navigation, checking that the customer can understand the outcome and retrieve the current appointment.

Also document how the demo reaches “time just taken,” no free times and cancelled states, using isolated demo data rather than production appointments. The demo currently promises seeded appointments and an inside-cut-off example (`APPOINTMENT_PAGE.md:42`). These additions would make later inspection easier to repeat. They do not add a new acceptance rule: the profile already requires the slow-network edge, and M2.5 already requires the refusal states.

## Request and mechanism assessment

- The accepted request is customers moving their own appointment instead of phoning. The approved brief supplies the private email link, optional stylist change, cut-off, emails and history. The design retains these decisions rather than narrowing the request to a single preferred example.
- A normal customer outside the cut-off can choose a new time with the current stylist; choosing a different stylist is deliberate and visible at confirmation. A customer with no free times is given the phone number rather than silently switched to another stylist.
- A page opened outside the cut-off can remain open until it crosses the boundary. Delegating the final move to BOOKINGS, whose design rechecks elapsed time within the transaction, handles this ordinary stale-page case. Exactly 24 hours remains allowed by the BOOKINGS contract.
- A time can be taken after it was displayed. The refusal returns fresh choices and changes nothing; the BOOKINGS transaction and unique constraint supply the enforcement. The page does not need its own competing availability rule.
- Cancelled and unknown links have explicit states. The design keeps appointment details out of an unknown-link response. Empty availability and other refusal reasons are handled rather than treated as success.
- GET is read-only and confirmation uses POST, so opening the private link in a mail preview does not move an appointment. Server-rendered forms are a credible mechanism for the required no-account, no-JavaScript journey. The specified response headers support privacy on the customer pages.
- Email creation, repeat-move links, immediate slot release and move history belong to BOOKINGS. Its design and done-when items cover those obligations; APPOINTMENT_PAGE M2 waits for BOOKINGS M2 and checks real integration. The page promises a queued email rather than owning a second email implementation.
- Look options precede implementation, and the owner selects the reference. The final ease-of-use decision is attended on the owner's phone. Publishing, a paid sender and sending real customer email remain owner decisions. The design adds no conflicting product scope.

## Done-when assessment

These are assessments of whether the planned proofs can judge the requirements, not milestone verdicts.

| Item | Assessment |
| --- | --- |
| M1.1 | Judgeable: the file-existence check is paired with inspection at native phone width and enlarged, using the same sample appointment. The bar rejects three colour variants of one layout. |
| M1.2 | Judgeable through the recorded owner answer; an agent's own preference cannot satisfy it. |
| M2.1 | Judgeable HTTP journey covering default and deliberately changed stylist with no JavaScript. M2.4 rules out stand-in storage and M2.5/M2.6 cover the actual controls. Suggestion 2 clarifies how to implement the HTTP proof. |
| M2.2 | Judgeable refusal paths: inside-cut-off visibility/no move, unknown-link privacy, and a contested time with no mutation and fresh choices. BOOKINGS supplies transaction-level refusal checks. |
| M2.3 | Judgeable: GET requests can be checked for persistent side effects and all private-page responses for the three specified headers. A mutating confirmation GET would fail the statement. |
| M2.4 | A concrete code-boundary question. Reading the page callers and test setup can establish that they use the real BOOKINGS operations/store. This rejects a page whose apparent success comes only from a mock. |
| M2.5 | Judgeable on the real web-mobile target: the inspection names every designed state, the demo entry point, viewport and chosen reference. The project profile adds the target edge conditions. A screenshot of only the successful state cannot satisfy it. |
| M2.6 | Judgeable inspection of both choosing and confirming; it catches a UI that silently preselects another stylist even if the backend's omitted-stylist behavior is correct. |
| M2.7 | Correctly attended: the owner must use the page on their phone and supply the recorded judgment. An automated test or reviewer opinion cannot substitute for that answer. |

M1 can proceed independently of BOOKINGS. M2 is gated by the module build order on both BOOKINGS M2 and the owner's look choice. The quality bars and combined automated, code-reading, real-browser and attended proofs are sufficient to begin building. Suggestions above improve clarity and repeatability without holding up the build.

DESIGN OK
