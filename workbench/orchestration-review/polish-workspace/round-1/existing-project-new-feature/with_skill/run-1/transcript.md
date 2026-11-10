# existing-project-new-feature, with skill

## Owner

for the salon app I want customers to be able to move an appointment themselves instead of phoning us. brief is fine to write up, I use claude and codex both

## Agent

I've read the repo. What I understood: customers should be able to move their own appointment to another time, without phoning the salon. I'll write the brief once the open points are settled, and it will note that you build with both Claude and Codex.

Things I found that you should know:

- **There is very little there today.** The code can create a booking (customer, stylist, slot) and build an email subject line, and that's all.
- **Cancelling isn't in the code.** `docs/modules/ARCHITECTURE.md` says creating and cancelling are done, but I can't find any cancelling.
- **Customers have no way to identify themselves.** There is no login and no link or code tied to a booking, so letting a customer move their own appointment means building that too.
- **Three words are in use for one thing.** You say "appointment", the code says `booking`, and the customer email says "reservation". I'll use "appointment" in the brief and leave the code's name alone.

One question before I propose anything, because the answer settles the cases nobody has mentioned yet: what is the trouble with customers phoning to move an appointment today?

## Owner

The front desk spends about an hour a day on the phone moving bookings.

## Agent

That settles one thing already: a move should take effect at once, with no approval step at the front desk, because an approval step would keep their time tied up. I've put that in the draft brief as my decision, so correct it if you want the desk to confirm each move.

The decision that changes the build most is how a customer proves an appointment is theirs, since there is no login today.

- **A private link in the confirmation email (my recommendation).** The customer taps the link and picks a new time, with nothing to remember. Anyone who has the email can move the appointment, which is the same level of trust as someone phoning and giving a name. It is the smallest build.
- **Customer accounts with a password.** This is stronger, and it gives you a base for things like appointment history later. It is a much bigger build, and customers who forget their password will phone anyway, which works against the hour a day you want back.
- **A code sent to their phone or email each time.** No password, and it is stronger than a link. It needs a text-message service that costs money per message, or a second email step.

Shall I go with the private link in the confirmation email?

## Owner

Yes, the private link in the confirmation email is fine.

## Agent

The private link is in the draft brief as agreed, in your words.

Next is how late a customer may still move an appointment. Nothing in the app records a rule for this, and it matters because a slot given up at the last minute is one the salon probably can't refill.

When someone phones at short notice today, is there a point where the front desk says no? If there is, I'd apply the same rule to the link and have it tell the customer to phone the salon after that point.

## Owner

They can't move it less than 24 hours before.

## Agent

The 24-hour rule is in, in your words. Here is the whole brief; it is saved as a draft in `docs/modules/BRIEF.md`.

Where I most need your eye:

- **Where it runs (I'm unsure I understood).** The repository has no web server and sends no email. I've written that both are part of this work. If the real salon app lives somewhere I can't see, tell me, because that changes the plan a lot.
- **Changing stylist (decision 7).** I decided a customer may pick a different stylist as well as a different time, since someone whose stylist is full would otherwise phone.
- **Inside the 24 hours (decision 4).** I decided the link tells the customer to phone the salon, and that the front desk can still move any appointment by phone at any time.
- **Other decisions I made without asking.** Moves are unlimited, need no approval, and send a new confirmation email. Customer cancelling and a front-desk screen are left out as later work.
- **Names.** You said "appointment" and later "bookings". I've used "appointment" for what customers read and left `booking` in the code.

When you approve, I'll commit the brief and the glossary to `main` and start a planner, so your yes covers both.

---

# Project brief: customers move their own appointment

## The request
> for the salon app I want customers to be able to move an appointment themselves instead of phoning us. brief is fine to write up, I use claude and codex both

(2026-11-10)

## Why
The owner, 2026-11-10: "The front desk spends about an hour a day on the phone moving bookings."

## Who it is for, and what they will be able to do
Customers of the salon who already have an appointment. From the confirmation email they open a private link, see their appointment, pick another free time, and get an email confirming the new time. They do it without phoning and without the front desk doing anything.

## Decisions
1. A move takes effect at once, with no approval step by the front desk. The agent's decision, because an approval step would keep the front desk's time tied up, which is the thing the owner wants to stop. Not confirmed by the owner.
2. A customer reaches their appointment through a private link in the confirmation email. No accounts, no passwords. Proposed by the agent, and agreed by the owner: "Yes, the private link in the confirmation email is fine." (2026-11-10)
3. A customer cannot move an appointment that starts in less than 24 hours. The owner: "They can't move it less than 24 hours before." (2026-11-10)
4. Inside those 24 hours the link still opens, shows the appointment, and tells the customer to phone the salon. Proposed by the agent on 2026-11-10; the owner answered with the rule in decision 3 and did not comment on this part. Not confirmed by the owner.
5. The link cannot be guessed, and it opens one appointment only. The agent's decision, because the link is the only thing that proves whose appointment it is. Not confirmed by the owner.
6. A customer can only move to a time when the stylist is free, and two customers can never end up with the same stylist at the same time. The agent's decision, because a double-booked stylist puts the front desk back on the phone. Not confirmed by the owner.
7. The customer may choose a different stylist as well as a different time. Their current stylist's free times are shown first. The agent's decision, because a customer whose stylist is full would otherwise phone. Not confirmed by the owner.
8. An appointment can be moved more than once, and the same link keeps working after a move. The agent's decision, because a limit would send the customer back to the phone. Not confirmed by the owner.
9. After a move the customer gets an email with the new time, and the old time becomes free for others. The agent's decision, because the customer needs a record and the freed time is worth money to the salon. Not confirmed by the owner.
10. Words the customer reads in this feature say "appointment". The code keeps `booking`. The agent's decision, because "appointment" is the word the owner used in the request. Not confirmed by the owner.

## Not part of this
- Cancelling an appointment by the customer. Later work. `ARCHITECTURE.md` lists cancelling as done, but the code has none.
- Customer accounts, passwords, appointment history.
- Text messages.
- A screen for the front desk. Later work.
- Booking a new appointment by the customer.

The result is a failure, even if it works, if any of these is true: a stylist can be double-booked; one customer can open or move another customer's appointment; a customer can move an appointment inside the 24 hours; customers find the page confusing enough that they phone anyway.

## Must not change
- Creating a booking works as it does today, and a booking keeps its customer, stylist, slot and status.
- The front desk can still move any appointment for a customer who phones, at any time.
- The subject line of the existing confirmation email.

## How it will be judged
- `npm test` passes, with tests for the 24-hour rule at its edge, for double-booking, and for a wrong link.
- The owner opens the link from a real confirmation email on their own phone, moves an appointment, and gets the new email. Only the owner can judge whether the page and the emails read well enough that a customer would not phone.
- Over time: the front desk's hour a day on the phone goes down. Only the owner can see this.

## Where it runs
A web page the customer opens in the browser on their phone, from the link in the email, served by the salon app on Node. The agent's decision. The repository today has no web server and sends no email, only functions that make a booking and an email subject line, so both are part of this work unless they exist somewhere the agent could not see. Not confirmed by the owner.

## How the owner wants to work
- The owner: "I use claude and codex both". Either program may build or review.
- From `ORCHESTRATE.md`: work is integrated locally on `main`, and the check is `npm test`. Agents do not push to a remote repository.
- Anything that spends money, publishes, or can't be undone comes to the owner first. That includes signing up for a service that sends email. The agent's decision.

## Still open
- Which service sends the email. Not decided yet. Meanwhile the planner assumes email is sent through one small piece that can be swapped, and tests run without sending anything.
- How long an appointment lasts and what opening hours are, which decide which times are free. The code does not say. Not decided yet. Meanwhile the planner assumes free times come from a list the salon supplies.
- How the front desk learns that an appointment has moved. The planner chooses, without building a screen.

---

Is this right?

## Owner

Looks right to me, go ahead. Call it an appointment everywhere.

---

Ended: the owner approved; the approval was not passed to the agent.
