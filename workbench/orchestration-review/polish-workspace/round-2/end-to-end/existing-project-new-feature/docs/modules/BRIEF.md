# Project brief: customers move their own appointment

## The request
> for the salon app I want customers to be able to move an appointment themselves instead of phoning us. brief is fine to write up, I use claude and codex both
> 2026-11-10, on reading the brief: "Decision 5 is wrong: they can't move it less than 24 hours before. The rest looks fine."
> 2026-11-10, asked where the salon's bookings are kept today: "no idea, it's in the repo"

## Why
The owner, 2026-11-10: "The front desk spends about an hour a day on the phone moving bookings."

## Who it is for, and what they will be able to do
Customers of the salon. A customer who has an appointment can move it to a different time themselves, without phoning. The front desk benefits: the aim is to get back most of that hour a day.

## Decisions
1. Customers see the word "appointment" everywhere, including the email that today says "reservation". The code keeps the name `booking`. The agent's decision, because the owner's request uses "appointment". Not confirmed by the owner.
2. A customer reaches their appointment through a private link in the confirmation email, with no account and no password. Proposed by the agent, and agreed by the owner: "Yes, go with the link in the email."
3. A moved appointment stays with the same stylist, and the customer may choose a different one. The owner: "A moved appointment must keep the same stylist unless the customer picks a different one."
4. The customer is offered only times that are free: inside opening hours, in the future, and with no confirmed appointment for that stylist. Two customers can never end up in the same slot with the same stylist. The agent's decision, because a move that double-books causes a phone call instead of saving one. Not confirmed by the owner.
5. A customer cannot move an appointment less than 24 hours before it starts. The owner, 2026-11-10, correcting the agent's earlier "no cut-off": "they can't move it less than 24 hours before."
   - Inside those 24 hours the link still shows the appointment, and tells the customer to phone the salon to change it. The agent's decision, because a dead link would leave the customer with nothing to do. Not confirmed by the owner.
   - Outside them, a customer may move as many times as they like, with no fee. The agent's decision, because the owner named no other limit. Not confirmed by the owner.
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
- A customer with only the confirmation email can move their appointment to a free time, with the same stylist by default, and gets an email with the new time. A customer inside the 24 hours cannot move it. `npm test` passes, with tests covering decisions 3 to 6. The agent's reading. Not confirmed by the owner.
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
- Where the salon's existing appointments are kept. Not decided yet: the owner does not know, and the repository saves bookings nowhere today. Assume the store this work adds becomes the salon's record of appointments, and that appointments made before it exists are not in it.
- How the page looks. The owner will choose from options, so the first piece of work should produce them.
