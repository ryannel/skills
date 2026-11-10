# Project brief: customers move their own appointments

DRAFT. The conversation with the owner is still going. Not yet approved.

## The request
> for the salon app I want customers to be able to move an appointment themselves instead of phoning us. brief is fine to write up, I use claude and codex both

(2026-11-10)

## Why
The owner, 2026-11-10: "The front desk spends about an hour a day on the phone moving bookings."

## Who it is for, and what they will be able to do
Customers of the salon who already have an appointment. They will be able to move it to another time without
phoning the salon.

## Decisions
1. The thing a customer moves is called an appointment. The code keeps its name, `booking`. The agent's
   decision, because "appointment" is the word in the owner's request. Not confirmed by the owner, who has also
   said "bookings".
2. A moved appointment keeps the stylist the customer had, unless the customer picks another one themselves.
   The owner, 2026-11-10: "The stylist has to stay the same by default."

## Not part of this
The owner, 2026-11-10: "A failure would be if a moved appointment ends up with a different stylist than the
customer had, unless they picked another one themselves. The stylist has to stay the same by default."

## Must not change
Not yet asked.

## How it will be judged
Not yet asked.

## Where it runs
Not yet settled. Today the repository is a Node.js package with no customer-facing page, link or login.

## How the owner wants to work
The owner: "I use claude and codex both". From `ORCHESTRATE.md`: the check is `npm test`, work is integrated
locally, and the branch is `main`.

## Still open
- How a customer reaches their appointment, since nothing customer-facing exists today. Not decided yet.
- Whether a slot is free: nothing checks this today, and moving an appointment needs it. Not decided yet.
- Cancelling: `ARCHITECTURE.md` says it is done, but the code only creates a booking. Not decided yet whether
  this work includes it.
