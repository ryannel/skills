# existing-project-new-feature, with skill

## Owner

for the salon app I want customers to be able to move an appointment themselves instead of phoning us. brief is fine to write up, I use claude and codex both

## Agent

I read the repo before replying. What I understood: a customer who has an appointment should be able to change it to another time on their own, without calling the salon.

Three things I found that you should know:

- **There is nothing customer-facing yet.** The app is one function that creates a booking and one email subject line. There is no page, link or login a customer could use, so this feature includes giving them a way in.
- **Nothing checks whether a slot is free.** Moving an appointment needs that, so it becomes part of this work.
- **Cancelling isn't there.** `docs/modules/ARCHITECTURE.md` says creating and cancelling are done, but the code only creates.

On names: you say "appointment", the code says `booking`, and the email says "reservation". I'll use "appointment" in the brief and leave the code's name alone.

Before I put any choices to you, one question: what is the phoning costing you today that makes this worth building now?

## Owner

The front desk spends about an hour a day on the phone moving bookings.

## Agent

Got it: the goal is to win back that hour a day at the front desk. I've started a draft of the brief with your words in it.

Next question, and it's one only you can answer: suppose this ships and customers can move appointments on their own. What would make you call it a failure anyway, including anything about how the salon runs today that it must not disturb?

## Owner

A failure would be if a moved appointment ends up with a different stylist than the customer had, unless they picked another one themselves. The stylist has to stay the same by default.

## Agent

That's in the brief in your words: the stylist stays the same unless the customer picks another one themselves.

The decision that changes the build most is how a customer gets to their appointment, since there is no page or login today. The choices:

| Choice | How it works | What it costs |
|---|---|---|
| **A. Private link in the email** (recommended) | The email they already get carries a link that opens their appointment. They pick a new time on a web page. | Smallest build. Anyone who has the email can move that one appointment. |
| **B. Look-up with a code** | They enter their email or phone number on your site and get a one-time code to type in. | More to build, and one more step for the customer. Safer if emails get forwarded. |
| **C. Customer accounts** | They sign up and log in with a password. | By far the most to build: sign-up, passwords, resets. People who forget their password will phone anyway. |

I recommend A. Your goal is fewer calls, so the path with the fewest steps wins, and the worst case is someone moving a single appointment to another free time.

Shall I go with A, the private link in the email?

## Owner

Yes, go with A, the private link in the email.

---

Ended: the owner approved; the approval was not passed to the agent.
