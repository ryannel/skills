# vague-new-product, with skill

## Owner

I want to build something for my climbing gym so we can keep track of route setting. can you help me figure out what that should be

## Agent

Yes. The folder I'm working in is empty, so we're starting from scratch with no existing code or documents to fit around.

What I have so far is that you want something for your climbing gym that keeps track of route setting. That could mean several different things to build, so before I suggest any of them:

Why do you want this? What is happening at the gym today that made you want it?

## Owner

Routes stay up too long. Members complain the walls feel stale, and nobody knows which routes are oldest. Setters just go by memory.

## Agent

That reason points at a narrow core: a record of every route that is up and the date it was set, so anyone can see the oldest ones at a glance. I've started a draft brief with your words in it.

The decision that changes the build most is who uses it:

1. **Setters and staff only (my recommendation).** Setters log a route when it goes up and mark it gone when it's stripped. Everyone on staff sees the list, oldest first. This is the smallest build, and it fixes "nobody knows which routes are oldest" directly.
2. **Staff, plus a page members can see.** The same log, with a public view of what's new and what's coming down. It answers the "stale" complaint visibly, but it costs more: a public page, and decisions about what members should and shouldn't see.
3. **Staff, plus member feedback.** Members rate or flag routes, so you strip by popularity as well as age. This is the largest build and needs member accounts or some guard against junk.

Options 2 and 3 can be added on top of option 1 later without redoing it.

Shall I plan this as a staff-only tool first, with the member-facing parts listed as later work?

## Owner

Yes, staff-only first is fine. It's the four setters who'll use it, on their phones at the wall. Members never touch it.

## Agent

Noted in the draft brief: staff-only, for the four setters, used on their phones at the wall, and members never touch it.

One more question before I write the brief up for you to check, and it's one only you can answer:

What would make this a failure even if it works as described?

## Owner

It would fail if it doesn't work at the back wall, there's no signal there. And if it's ugly, the setters just won't use it, so it has to look good.

## Agent

Both of those are now in the brief in your words. Here is the full brief for you to check.

**What I decided without asking you** (decisions 7 to 10 below):
- **No signal:** a setter can still see the list and make changes, and the changes reach the other phones once that phone is back in signal.
- **Web app, not an app-store app:** it opens in the phone's browser and can be added to the home screen. That covers iPhone and Android and avoids app store fees.
- **What a route's record holds:** wall, grade, hold colour, who set it and the date it went up.
- **Access:** only the setters can open it.

**What I'm least sure I understood:**
- **"No signal" at the back wall:** I've taken it as no connection of any kind there, wifi included.
- **"Look good":** this can't be settled in words, so the first piece of work will produce a few visual options on a phone screen for you to pick from.

When you approve, I'll commit the brief and start a planner, a separate agent that turns it into a build plan. Your approval covers both.

---

# Project brief: route setting tracker

## The request
> I want to build something for my climbing gym so we can keep track of route setting. can you help me figure out what that should be

(2026-11-10)

> Yes, staff-only first is fine. It's the four setters who'll use it, on their phones at the wall. Members never touch it.

(2026-11-10)

> It would fail if it doesn't work at the back wall, there's no signal there. And if it's ugly, the setters just won't use it, so it has to look good.

(2026-11-10)

## Why
The owner: "Routes stay up too long. Members complain the walls feel stale, and nobody knows which routes are oldest. Setters just go by memory."

## Who it is for, and what they will be able to do
The gym's four setters. The owner: "It's the four setters who'll use it, on their phones at the wall."

Standing at any wall, a setter can record a route when it goes up, mark it gone when it comes down, and see the routes that are up, oldest first, for the whole gym or for one wall. The agent's reading of the reason above. Not confirmed by the owner.

## Decisions
1. The tool is for staff only. Proposed by the agent, and agreed by the owner: "Yes, staff-only first is fine."
2. The users are the four setters. The owner: "It's the four setters who'll use it"
3. It is used on phones, at the wall. The owner: "on their phones at the wall"
4. Members never use it. The owner: "Members never touch it."
5. It must work at the back wall, where there is no signal. The owner: "It would fail if it doesn't work at the back wall, there's no signal there."
6. It has to look good. The owner: "if it's ugly, the setters just won't use it, so it has to look good."
7. With no signal, a setter can still see the list and record and remove routes. The changes reach the other setters' phones when the phone next has a connection. The agent's decision, because four people share one record and decision 5 rules out needing a connection at the wall. Not confirmed by the owner.
8. It is a web app that opens in the phone's browser and can be added to the home screen, not an app from an app store. The agent's decision, because it works on both iPhone and Android, can work with no signal, and avoids app store fees and review. Not confirmed by the owner.
9. A route's record holds the wall, the grade, the hold colour, who set it and the date it went up. Recording one takes a few taps. The agent's decision, because that is the least that identifies a route and gives its age. Not confirmed by the owner.
10. Only the setters can open it. The agent's decision, because of decision 4 and because a web app is otherwise reachable by anyone with the address. Not confirmed by the owner.

## Not part of this
- Anything members see or use. The owner: "Members never touch it."
- It is a failure if it doesn't work at the back wall, or if it is ugly. The owner's words are in decisions 5 and 6.
- Later work, not planned now: a page for members showing what is new and what is coming down; member ratings or flags on routes; a setting schedule or reminders. The agent's reading. Not confirmed by the owner.

## Must not change
Nothing exists today. The project folder was empty on 2026-11-10, and routes are tracked by the setters' memory.

## How it will be judged
- The owner chooses the look from options. How it should look can't be agreed in words, so the first piece of work produces a few visual options on a phone screen for the owner to pick from.
- Only the owner and the setters can test it at the back wall, on their own phones, with no signal: record a route there, walk back into signal, and see it on another setter's phone.
- A setter can answer "which routes are oldest?" from the tool without asking anyone.

## Where it runs
On the four setters' phones, in the phone's browser, iPhone and Android, including with no signal (decisions 3, 5, 7 and 8). The shared record needs somewhere to live online. Where that is, and what it costs, comes to the owner before any money is spent.

## How the owner wants to work
The agent's decision, because no `ORCHESTRATE.md` exists. Not confirmed by the owner: agents don't push to a remote repository, the work is built in Claude Code, and anything that spends money, publishes or can't be undone comes to the owner.

## Still open
- How old is too old for a route. Not decided yet. Assume meanwhile: no fixed limit, the list sorts oldest first, and a limit can be added as a setting.
- What happens when two setters change the same route while one has no signal. The planner chooses.
- Whether routes that have come down are kept as history. The planner chooses.

---

Is this right? Tell me anything to change, or approve it and I'll commit it and start the planner.

## Owner

Looks right to me, go ahead.

---

Ended: the owner approved; the approval was not passed to the agent.
