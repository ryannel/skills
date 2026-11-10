# existing-project-new-feature, with skill

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

---

Ended: the owner approved the brief with one correction, and the agent merged it and started a planner. Taken from the session file, because the run went on past this point (see end-to-end).
