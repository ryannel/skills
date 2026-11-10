# Project brief: customers move their own appointment

DRAFT. Not yet approved by the owner.

## The request
> for the salon app I want customers to be able to move an appointment themselves instead of phoning us. brief is fine to write up, I use claude and codex both

(2026-11-10)

## Why
The owner, 2026-11-10: "The front desk spends about an hour a day on the phone moving bookings."

## Who it is for, and what they will be able to do
Customers of the salon who already have an appointment. From the confirmation email they open a private link,
see their appointment, pick another free time, and get an email confirming the new time. They do it without
phoning and without the front desk doing anything.

## Decisions
1. A move takes effect at once, with no approval step by the front desk. The agent's decision, because an
   approval step would keep the front desk's time tied up, which is the thing the owner wants to stop. Not
   confirmed by the owner.
2. A customer reaches their appointment through a private link in the confirmation email. No accounts, no
   passwords. Proposed by the agent, and agreed by the owner: "Yes, the private link in the confirmation email
   is fine." (2026-11-10)
3. A customer cannot move an appointment that starts in less than 24 hours. The owner: "They can't move it less
   than 24 hours before." (2026-11-10)
4. Inside those 24 hours the link still opens, shows the appointment, and tells the customer to phone the
   salon. Proposed by the agent on 2026-11-10; the owner answered with the rule in decision 3 and did not
   comment on this part. Not confirmed by the owner.
5. The link cannot be guessed, and it opens one appointment only. The agent's decision, because the link is
   the only thing that proves whose appointment it is. Not confirmed by the owner.
6. A customer can only move to a time when the stylist is free, and two customers can never end up with the
   same stylist at the same time. The agent's decision, because a double-booked stylist puts the front desk
   back on the phone. Not confirmed by the owner.
7. The customer may choose a different stylist as well as a different time. Their current stylist's free times
   are shown first. The agent's decision, because a customer whose stylist is full would otherwise phone. Not
   confirmed by the owner.
8. An appointment can be moved more than once, and the same link keeps working after a move. The agent's
   decision, because a limit would send the customer back to the phone. Not confirmed by the owner.
9. After a move the customer gets an email with the new time, and the old time becomes free for others. The
   agent's decision, because the customer needs a record and the freed time is worth money to the salon. Not
   confirmed by the owner.
10. Words the customer reads in this feature say "appointment". The code keeps `booking`. The agent's decision,
    because "appointment" is the word the owner used in the request. Not confirmed by the owner.

## Not part of this
- Cancelling an appointment by the customer. Later work. `ARCHITECTURE.md` lists cancelling as done, but the
  code has none.
- Customer accounts, passwords, appointment history.
- Text messages.
- A screen for the front desk. Later work.
- Booking a new appointment by the customer.

The result is a failure, even if it works, if any of these is true: a stylist can be double-booked; one
customer can open or move another customer's appointment; a customer can move an appointment inside the 24
hours; customers find the page confusing enough that they phone anyway.

## Must not change
- Creating a booking works as it does today, and a booking keeps its customer, stylist, slot and status.
- The front desk can still move any appointment for a customer who phones, at any time.
- The subject line of the existing confirmation email.

## How it will be judged
- `npm test` passes, with tests for the 24-hour rule at its edge, for double-booking, and for a wrong link.
- The owner opens the link from a real confirmation email on their own phone, moves an appointment, and gets
  the new email. Only the owner can judge whether the page and the emails read well enough that a customer
  would not phone.
- Over time: the front desk's hour a day on the phone goes down. Only the owner can see this.

## Where it runs
A web page the customer opens in the browser on their phone, from the link in the email, served by the salon
app on Node. The agent's decision. The repository today has no web server and sends no email, only functions
that make a booking and an email subject line, so both are part of this work unless they exist somewhere the
agent could not see. Not confirmed by the owner.

## How the owner wants to work
- The owner: "I use claude and codex both". Either program may build or review.
- From `ORCHESTRATE.md`: work is integrated locally on `main`, and the check is `npm test`. Agents do not push
  to a remote repository.
- Anything that spends money, publishes, or can't be undone comes to the owner first. That includes signing up
  for a service that sends email. The agent's decision.

## Still open
- Which service sends the email. Not decided yet. Meanwhile the planner assumes email is sent through one
  small piece that can be swapped, and tests run without sending anything.
- How long an appointment lasts and what opening hours are, which decide which times are free. The code does
  not say. Not decided yet. Meanwhile the planner assumes free times come from a list the salon supplies.
- How the front desk learns that an appointment has moved. The planner chooses, without building a screen.
