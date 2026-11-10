# Project brief: route setting tracker

Status: shown to the owner on 2026-11-10, awaiting their approval.

## The request
> I want to build something for my climbing gym so we can keep track of route setting. can you help me figure out what that should be

(2026-11-10)

> The back wall has no signal, so it needs to work with no signal there. That assumption in the brief is wrong.

(2026-11-10, correcting the draft's assumption that there is signal at every wall)

## Why
The owner: "Routes stay up too long. Members complain the walls are stale, and nobody knows which routes are oldest. Setters just go by memory."

## Who it is for, and what they will be able to do
The gym's four setters. The owner: "The four setters are the ones who'll use it."

A setter standing at the wall with a phone will be able to:
- log a route when it goes up;
- mark a route, or a whole wall of routes, as taken down;
- see every route that is up, oldest first, and see which wall has gone longest without a reset.

## Decisions
1. Setters and staff only; no member-facing part. Proposed by the agent, and agreed by the owner: "Yes, setters and staff only. The four setters are the ones who'll use it."
2. It is a web app the setters open on their phones, not a native app and not a spreadsheet. Proposed by the agent, and agreed by the owner: "Yes, a web app on their phones works. It'd be a mix of iPhone and Android."
3. Each route is tracked individually and belongs to a wall. A setter can take down one route or every route on a wall in one action, and ages can be viewed by route or by wall. The agent's decision, handed over by the owner ("I don't mind, you decide"), because it works whether the gym resets whole walls or single routes. Not confirmed by the owner.
4. A route records: its wall, grade, hold colour, who set it and the date it went up. The date defaults to today and the setter defaults to whoever is logged in. The agent's decision, because these are what a setter needs to find the route on the wall and nothing more. Not confirmed by the owner.
5. A route counts as overdue after 6 weeks and is highlighted in the list. The number is a setting the setters can change. The agent's decision, because the owner's complaint is routes staying up "too long" and the list needs a line to draw; 6 weeks is a common rotation for commercial gyms. Not confirmed by the owner.
6. The list of walls and the list of grades are editable by the setters, not fixed in the build. The agent's decision, because the gym's layout and grading scale are not known and will change. Not confirmed by the owner.
7. Each setter signs in as themselves, and stays signed in on their phone. The agent's decision, because "who set it" should be recorded without typing. Not confirmed by the owner.
8. Routes that are already up when the tool starts are entered by the setters with their best guess of the date, and are marked as estimated. The agent's decision, because the oldest routes are the reason for the tool and nobody has their real dates. Not confirmed by the owner.
9. Routes that have been taken down are kept as history, not deleted. The agent's decision, because it is free to keep and can't be recovered later. Not confirmed by the owner.
10. It works with no signal. The owner: "The back wall has no signal, so it needs to work with no signal there." A setter with no signal can still see the route list as it was when the phone last had signal, log routes and take routes down; the changes are saved on the phone and sent by themselves when signal returns.
11. The app shows when changes are waiting to be sent, and if two setters changed the same route while out of signal, the later change is kept. The agent's decision, because a setter has to be able to trust that nothing logged at the back wall is lost, and two people changing one route at once will be rare with four setters. Not confirmed by the owner.

## Not part of this
- A page members can see (what's new, what's coming down). Later work.
- Members rating or flagging routes. Later work.
- A native phone app, and anything that goes through an app store.
- Setter scheduling, hold inventory, and reports or charts.

It is a failure, even if it works, if a route logged at the back wall with no signal is lost, or if logging a route at the wall is slow enough that setters stop doing it. Logging one route should take a few taps and well under half a minute.

## Must not change
Nothing exists today: this is a new project. Setters currently track routes by memory.

## How it will be judged
- On an iPhone and on an Android phone, a setter can log a route, see it in the oldest-first list, and take it down.
- Overdue routes stand out at a glance.
- With the phone in airplane mode, a setter can open the app, log a route and take one down; when signal returns, the changes appear on another setter's phone with nothing lost.
- Only the owner and the setters can judge whether it is quick enough to use at the wall. The owner tries it on their own phone before it is called finished.

## Where it runs
A web app used in the phone browser, on both iPhone and Android (the owner: "a mix of iPhone and Android"). Used at the wall, so it must work on a small screen with one hand. It needs to be hosted on the internet so all four phones see the same data. The back wall has no signal, so the app must open and work there without a connection (decision 10).

## How the owner wants to work
The agent's decision, not confirmed by the owner: agents don't push to a remote repository, the work is built in Claude Code, and anything that spends money, publishes or can't be undone comes to the owner. Choosing and paying for hosting is one of those.

## Still open
- Where it is hosted: the planner proposes a free or low-cost option, and the owner approves it before anything is published or paid for.
- How setters sign in (for example a link, a PIN or a password): the planner chooses.