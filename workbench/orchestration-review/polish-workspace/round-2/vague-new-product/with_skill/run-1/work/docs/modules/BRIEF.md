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

Standing at any wall, a setter can record a route when it goes up, mark it gone when it comes down, and see
the routes that are up, oldest first, for the whole gym or for one wall. The agent's reading of the reason
above. Not confirmed by the owner.

## Decisions
1. The tool is for staff only. Proposed by the agent, and agreed by the owner: "Yes, staff-only first is fine."
2. The users are the four setters. The owner: "It's the four setters who'll use it"
3. It is used on phones, at the wall. The owner: "on their phones at the wall"
4. Members never use it. The owner: "Members never touch it."
5. It must work at the back wall, where there is no signal. The owner: "It would fail if it doesn't work at the
   back wall, there's no signal there."
6. It has to look good. The owner: "if it's ugly, the setters just won't use it, so it has to look good."
7. With no signal, a setter can still see the list and record and remove routes. The changes reach the other
   setters' phones when the phone next has a connection. The agent's decision, because four people share one
   record and decision 5 rules out needing a connection at the wall. Not confirmed by the owner.
8. It is a web app that opens in the phone's browser and can be added to the home screen, not an app from an
   app store. The agent's decision, because it works on both iPhone and Android, can work with no signal, and
   avoids app store fees and review. Not confirmed by the owner.
9. A route's record holds the wall, the grade, the hold colour, who set it and the date it went up. Recording
   one takes a few taps. The agent's decision, because that is the least that identifies a route and gives its
   age. Not confirmed by the owner.
10. Only the setters can open it. The agent's decision, because of decision 4 and because a web app is
    otherwise reachable by anyone with the address. Not confirmed by the owner.

## Not part of this
- Anything members see or use. The owner: "Members never touch it."
- It is a failure if it doesn't work at the back wall, or if it is ugly. The owner's words are in decisions 5
  and 6.
- Later work, not planned now: a page for members showing what is new and what is coming down; member ratings
  or flags on routes; a setting schedule or reminders. The agent's reading. Not confirmed by the owner.

## Must not change
Nothing exists today. The project folder was empty on 2026-11-10, and routes are tracked by the setters'
memory.

## How it will be judged
- The owner chooses the look from options. How it should look can't be agreed in words, so the first piece of
  work produces a few visual options on a phone screen for the owner to pick from.
- Only the owner and the setters can test it at the back wall, on their own phones, with no signal: record a
  route there, walk back into signal, and see it on another setter's phone.
- A setter can answer "which routes are oldest?" from the tool without asking anyone.

## Where it runs
On the four setters' phones, in the phone's browser, iPhone and Android, including with no signal (decisions
3, 5, 7 and 8). The shared record needs somewhere to live online. Where that is, and what it costs, comes to
the owner before any money is spent.

## How the owner wants to work
The agent's decision, because no `ORCHESTRATE.md` exists. Not confirmed by the owner: agents don't push to a
remote repository, the work is built in Claude Code, and anything that spends money, publishes or can't be
undone comes to the owner.

## Still open
- How old is too old for a route. Not decided yet. Assume meanwhile: no fixed limit, the list sorts oldest
  first, and a limit can be added as a setting.
- What happens when two setters change the same route while one has no signal. The planner chooses.
- Whether routes that have come down are kept as history. The planner chooses.
