# existing-project-new-feature: the run that went on to plan and build

## Owner

for the salon app I want customers to be able to move an appointment themselves instead of phoning us. brief is fine to write up, I use claude and codex both

## Agent

Here's what I understood: customers should be able to move their own appointment to a different time without phoning the salon. You're happy for me to write this up as a brief, and you build with both Claude and Codex.

I read the repo, and three things are worth knowing before we go further:

- **There is very little to build on.** The code can create a booking (customer, stylist, slot, status "confirmed") and produce an email subject line, and that's all.
- **Nothing customer-facing exists in this repo.** There are no pages, no login, and no record of which slots are free. For a customer to move an appointment, the feature needs a way for them to reach it and a way to know what's available, so this is bigger than adding a "move" button.
- **Three words are in use for one thing.** You say "appointment", the code says `booking`, and the email says "reservation". I'll use "appointment" everywhere customers see it, including fixing the email, and leave the code's name alone.

One question first, because the answer shapes most of the rest: what is the trouble with the phone calls today?

## Owner

The front desk spends about an hour a day on the phone moving bookings.

## Agent

That gives the feature a clear target: it works if the front desk gets most of that hour back, which means a customer has to find moving an appointment easier than phoning. I've started a draft brief with your reason in it, at `docs/modules/BRIEF.md`.

The decision that changes the build most is how a customer gets to their appointment in order to move it. Nothing in the app does this today, so it's a free choice:

| Option | How it works | What it costs |
|---|---|---|
| **A. Link in the email** (recommended) | The confirmation email carries a private link. The customer taps it, sees their appointment and picks a new time. No account, no password. | Smallest build. Anyone who has the email can move the appointment. |
| **B. Look-up page** | The customer goes to a page and types something they know, such as their phone number and the appointment date. | A little more to build. Works without the email, but is easier for someone else to guess. |
| **C. Customer accounts** | The customer signs in and sees all their appointments. | By far the biggest build. Every forgotten password is a reason to phone instead. |

I recommend A because it's the least effort for the customer, which is what takes calls off the front desk, and nothing about it stops you adding accounts later.

Shall I go with the link in the email?

## Owner

Yes, go with the link in the email.

## Agent

The link in the email is now decision 2 in the draft brief.

Next is a question only you can answer, and it covers the cases nobody has mentioned yet: what would make this a failure even if it works as described? That includes anything about how the salon runs today that must not change.

## Owner

A moved appointment must keep the same stylist unless the customer picks a different one.

## Agent

The brief is written and saved at `docs/modules/BRIEF.md`; your stylist rule is decision 3, in your words. Nothing is committed yet. When you approve it, I'll commit the brief and the glossary to `main` and start a planner, so your yes covers both.

Four things I decided without asking are where your attention is most needed:

- **No cut-off (decision 5).** A customer can move an appointment right up to its start time, as often as they like, with no fee. I chose this because every limit sends people back to the phone. If you want a rule such as "not within 24 hours", say so.
- **Opening hours (Still open).** The app has no record of when the salon is open or which days each stylist works. The planner will assume one set of hours for the whole salon and that every stylist works all of them.
- **How the front desk hears about a move (Still open).** The planner will assume the salon gets an email for each move. There is no front-desk screen in this work.
- **The name.** You've said both "appointment" and "bookings". I've used "appointment" for everything customers see and left `booking` in the code.

# Project brief: customers move their own appointment

## The request
> for the salon app I want customers to be able to move an appointment themselves instead of phoning us. brief is fine to write up, I use claude and codex both

## Why
The owner, 2026-11-10: "The front desk spends about an hour a day on the phone moving bookings."

## Who it is for, and what they will be able to do
Customers of the salon. A customer who has an appointment can move it to a different time themselves, without phoning. The front desk benefits: the aim is to get back most of that hour a day.

## Decisions
1. Customers see the word "appointment" everywhere, including the email that today says "reservation". The code keeps the name `booking`. The agent's decision, because the owner's request uses "appointment". Not confirmed by the owner.
2. A customer reaches their appointment through a private link in the confirmation email, with no account and no password. Proposed by the agent, and agreed by the owner: "Yes, go with the link in the email."
3. A moved appointment stays with the same stylist, and the customer may choose a different one. The owner: "A moved appointment must keep the same stylist unless the customer picks a different one."
4. The customer is offered only times that are free: inside opening hours, in the future, and with no confirmed appointment for that stylist. Two customers can never end up in the same slot with the same stylist. The agent's decision, because a move that double-books causes a phone call instead of saving one. Not confirmed by the owner.
5. A customer may move an appointment at any point before it starts, and as many times as they like. There is no cut-off and no fee. The agent's decision, because every limit sends the customer back to the phone, which is the hour this is meant to save. Not confirmed by the owner.
6. When an appointment is moved, the old slot becomes free at once, and the customer gets an email confirming the new time. The link in it works for moving again. The agent's decision, because the customer needs proof of the new time without phoning to check. Not confirmed by the owner.
7. The appointment records that the customer moved it, and from which time. The agent's decision, because the front desk will need to answer "who changed this?". Not confirmed by the owner.

## Not part of this
- The owner: "A moved appointment must keep the same stylist unless the customer picks a different one." A move that changes the stylist by itself is a failure, even if everything else works.
- Customer accounts and sign-in. A look-up page where the customer types their details. Both were offered as alternatives to decision 2 and not chosen. The agent's reading. Not confirmed by the owner.
- Changing anything else about an appointment, such as the service. Making a new appointment online. Text-message reminders. A screen for the front desk. The agent's reading. Not confirmed by the owner.

## Must not change
- Creating and cancelling bookings work as they do today. The agent's reading. Not confirmed by the owner.
- The code's name for an appointment stays `booking`. The agent's reading. Not confirmed by the owner.

## How it will be judged
- A customer with only the confirmation email can move their appointment to a free time, with the same stylist by default, and gets an email with the new time. `npm test` passes, with tests covering decisions 3 to 6. The agent's reading. Not confirmed by the owner.
- Only the owner can judge two things: whether the page is easy enough that customers use it instead of phoning, and whether the front desk's hour a day actually shrinks once it is in use.

## Where it runs
The existing salon app: JavaScript on Node, checked with `npm test`. Customers use the page from the link on their phone's browser. Today the repository holds no customer-facing pages, no way of sending email, no opening hours and no record of free slots, so this work has to supply what a move needs of each. The agent's reading of the repository.

## How the owner wants to work
- The owner builds with both Claude and Codex. The owner: "I use claude and codex both"
- From `ORCHESTRATE.md`: plans in `docs/modules`, work integrated locally on `main`, the check is `npm test`.
- Agents don't push to a remote repository, and anything that spends money, publishes or can't be undone comes to the owner. The agent's decision, because it is the set's default. Not confirmed by the owner.

## Still open
- Which of Claude and Codex plans, builds and reviews. The planner chooses.
- The salon's opening hours and each stylist's working days. Not decided yet. Assume one set of opening hours for the whole salon, kept in one place the owner can edit, and that every stylist works all of them.
- How the front desk learns of a move. Not decided yet. Assume the salon gets an email for each move, saying who moved, from when, to when, and with which stylist.
- How the page looks. The owner will choose from options, so the first piece of work should produce them.

Is this right, and shall I commit it and start the planner?

## Owner

Decision 5 is wrong: they can't move it less than 24 hours before. The rest looks fine.

## Agent

Decision 5 now carries your 24-hour rule, the brief and glossary are committed to `main` (commit `32b9b33`), and planning has started.

What I changed in the brief:

- **Decision 5** now reads: a customer cannot move an appointment less than 24 hours before it starts, quoted from you.
- **Inside the 24 hours**, the link still shows the appointment and tells the customer to phone the salon. That part is my addition, marked as mine.
- **Outside the 24 hours**, they can still move as often as they like with no fee, also marked as mine since you named no other limit.
- **"How it will be judged"** now includes that a customer inside the 24 hours cannot move.
- **"The request"** has your correction added, dated today.

Planning can take a while. When the planner finishes, I'll tell you what it planned and what it assumed. To start the build after that, say "build it" or run `/build`.

## Note

(The script reported that a background command had finished.)

## Agent

The plan is finished and on `main`. Nothing is built yet, and both parts still get a design review, which runs first when you start the build.

## What was planned

The work is split into two parts:

1. **Bookings** (built on Codex), in two steps:
   - A salon settings file, a store that can't hold two appointments for one stylist in one slot, the list of free times, the private link and the confirmation email.
   - The move itself: the 24-hour rule, same stylist unless the customer picks another, the record of who moved it, the email to the customer and the notice to the salon.
2. **The appointment page** (built on Claude, because it needs a browser):
   - Three options for how the page looks, for you to choose from.
   - Then the working page on a phone.

Each part is reviewed by the other program.

The planner also corrected the old module list: it said cancelling was done, but there is no cancelling in the code. This plan does not add it.

## What the planner assumed

Say so if any of these is wrong:

- Every appointment takes one fixed-length slot, 30 minutes unless you change it.
- Customers can see free times up to 8 weeks ahead.
- The new time only has to be free and in the future, so a customer can move *to* a time less than 24 hours away.
- A move exactly 24 hours before the start is still allowed.
- Each customer record has a name and an email address.
- The appointments are stored in a single database file on one machine.
- The page works without JavaScript.

The slot length matters most if your services vary in length, because free times would then be wrong.

## Decisions that stay with you

- **Where your bookings live today.** The plan assumes this app's new store becomes the salon's record of appointments. If they are kept in another system, free times will be wrong until that system feeds this one.
- **Real email.** For now emails are written to a folder, not sent. Choosing and paying for an email provider is your call.
- **Going live.** Putting the page where customers can reach it is your call.
- **The look.** You pick one of the three options once they exist, and later try the working page on your own phone.

To start the build, say "build it" or run `/build`. Where are your bookings kept today?

## Owner

no idea, it's in the repo

## Agent

I checked the repo: it doesn't keep bookings anywhere. The code can make a booking, but nothing saves it, so there is no existing record for this feature to read.

That means the plan's assumption stands, and the plan doesn't need to change: the store this work adds becomes the salon's record of appointments. The consequence is that it starts empty. Any appointment the salon has today, wherever the front desk keeps it, won't be in the store, so:

- those customers won't have a link to move it, and
- their times will show as free to other customers until someone enters them.

I've recorded your answer in the brief under "Still open" as not yet decided, with that assumption, and committed it (`bb1ebc7`). It doesn't block the build. It needs settling before the page goes live to customers, and the front desk is probably who knows where today's appointments are written down.

Say "build it" or run `/build` when you want the build to start.

## Owner

Build it.

## Agent

The build has started. Both parts are in design review first, which is the step that has to pass before any code is written.

- **Running now:** two design reviews, one for Bookings and one for the appointment page. Both run on Codex, because Claude wrote the plan and each review goes to the program that didn't do the work.
- **After that:** Bookings is built on Codex and the appointment page on Claude, one builder each, at the same time. That is the split the plan set, since you named no numbers.
- **Where they run:** I'm running in Claude Code. The Codex sessions show as threads in the Codex app, where you can watch them.
- **Codex usage:** 57% of the weekly limit is used, and it resets Saturday 14 Nov at 10:28. There isn't enough history yet to forecast whether the four milestones fit in what's left.

One thing didn't go through: I was refused permission to add the builders' working folder, `.worktrees/`, to git's local ignore list. It shows as an untracked folder in the repo for now. It may stop a later planning step, which refuses to run with stray files present; if that happens I'll tell you.

The first thing I'll bring you is the three look options for the appointment page, for you to pick one. Until then you can ask me at any point for a status, to pause the build, or to change something in the plan.

## Note

(The script reported that a background command had finished.)

## Agent

The Bookings design review came back asking for changes, so no Bookings code has been written yet. A planner is now revising the design, and the design gets reviewed again after that. Neither finding needs a decision from you.

The reviewer (Codex) found two things that must be fixed:

1. **The private link could leak from the database.** The plan promised that a leaked database would give nobody a working link, but it also stored the outgoing emails, which contain the link, in that same database.
2. **Nothing tested what the page relies on.** The plan had no test that the Bookings part actually hands the page an appointment and its free times through the link. A build could pass every check and still show customers no times.

The appointment page's design review is still running.

## Note

(The script reported that a background command had finished.)

## Owner

[Image: original 2440x2510, displayed at 1945x2000. Multiply coordinates by 1.25 to map to original image.]

## Agent

The three look options for the appointment page are ready, and the page is now waiting on your choice. Its design review passed with no required changes.

Open this sheet to see them side by side at phone size:

`/private/tmp/claude-501/-Users-ryannel--claude-spares-spare-9ZHcrE/101c62dd-273c-4dbb-b8ea-4ac2a6b47ab8/scratchpad/convo2/existing-project-new-feature/with_skill/work/.worktrees/appointment_page/docs/evidence/APPOINTMENT_PAGE/options.png`

All three show the same sample appointment. "Studio Nine", the phone number and the names are placeholders.

| | A · Card and day list | B · Week strip | C · Plain letter |
|---|---|---|---|
| **Look** | Light grey with white cards and blue time buttons | Dark header with a terracotta date tile, white below | Cream page in a serif typeface, reads like a note from the salon |
| **Picking a time** | Every free day is listed with its times as a grid of buttons; the customer scrolls | The customer taps a day in a strip, then one of that day's times | The stylist's five soonest times as a list, with links for other days |
| **Changing stylist** | A row at the bottom, below the first screen | A "Change" button beside the stylist's name, near the top | A text link under the list |
| **Fits one phone screen** | No, the stylist row and phone number need a scroll | Yes | Just about |

Which one should be built: A, B, C, or a mix of parts? Your answer is recorded in your own words, so say it however you like.

The Bookings design is still with the planner for the two fixes.

## Note

(The script reported that a background command had finished.)

## Agent

The planner has revised the Bookings design to fix both findings, and the design is now being reviewed again. If it passes, the Bookings builder starts on Codex straight away.

- **The link leak:** emails waiting to be sent are now stored encrypted, with the key kept outside the database.
- **The missing test:** there is now a test that goes through what the page relies on: record an appointment, open its link, list free times, move it, and open the link again.

The planner says nothing in the revision needs a decision from you.

The appointment page is still waiting on your choice of look: A, B, C, or a mix.

## Note

(The script reported that a background command had finished.)

## Agent

The revised Bookings design passed its second review, and Codex has built the first Bookings step. That step is now being reviewed on Claude, and it isn't counted as done until the review passes.

The first step covers the salon settings file, the store that refuses double-booking, the list of free times, the private link and the confirmation email. The move itself, with the 24-hour rule, is the second step and starts after this review.

The appointment page is still waiting on your choice of look: A, B, C, or a mix.

## Note

(The script reported that a background command had finished.)

## Agent

The first Bookings step passed its review and is done. Codex is now building the second step: the move itself, with the 24-hour rule, the same-stylist rule, the record of who moved it, and the emails.

The review is at `docs/evidence/BOOKINGS/M1-review.md` if you want to check how strict the reviewer was.

The appointment page is still waiting on your choice of look: A, B, C, or a mix. Once Bookings is finished, that choice is the only thing holding up the rest of the build.

---

Ended: stopped by hand after 25 minutes, while the second milestone of BOOKINGS was being built.
