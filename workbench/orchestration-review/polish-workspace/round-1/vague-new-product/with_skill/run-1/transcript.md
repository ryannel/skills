# vague-new-product, with skill

## Owner

I want to build something for my climbing gym so we can keep track of route setting. can you help me figure out what that should be

## Agent

Happy to help. The folder I'm working in is empty, so we're starting from scratch: a new tool for your gym that keeps track of route setting. I'll ask you questions one at a time, then write up a short brief of what to build for you to check.

What's going on at the gym that makes you want this now?

## Owner

Routes stay up too long. Members complain the walls are stale, and nobody knows which routes are oldest. Setters just go by memory.

## Agent

That gives the tool one main job: show which routes have been up longest, so setters know what to strip next without relying on memory.

The decision that changes the build most is who uses it:

1. **Setters and staff only (my recommendation).** Setters log each route when it goes up and when it comes down, and anyone on staff can see every route by age, oldest first. This is the smallest version and it goes straight at the problem you described.
2. **Setters, plus a page members can see.** The same, plus a public view of what's new and what's coming down. It shows members the walls are turning over, but it means a second audience and a public page to design, roughly half as much work again.
3. **Members take part too.** Members rate or flag routes, so popularity counts alongside age when deciding what to strip. This is the largest: it needs member accounts or QR codes on the wall, and some moderation.

I'd start with option 1, because the stale walls come from setters not knowing what's oldest, and a member page can be added later on top of the same data.

Shall I plan it as a setters-and-staff tool for now?

## Owner

Yes, setters and staff only. The four setters are the ones who'll use it.

## Agent

Noted: setters only, the four of them, with the member page and member ratings listed as possible later work.

The next decision is what it runs on. This one is expensive to change later, and it's also where a much cheaper route exists:

1. **A shared spreadsheet, no build at all.** One row per route with the date it went up, sorted by age. It's free and could be running today. The cost is that it's fiddly to fill in on a phone at the wall, and it only works if all four setters keep it up.
2. **A web app the setters open on their phones (my recommendation).** Logging a new route takes a few taps at the wall, and the oldest-first list is the home screen. Nothing to install. It needs somewhere to be hosted, which is usually free or a few dollars a month at this size, and a simple login.
3. **A native phone app.** It feels the same in use as option 2, but it has to be built for iPhone and Android and go through the app stores. That is a lot more work for no gain with four users.

I'd go with option 2, because the tool only helps if logging at the wall is quicker than not bothering, and that is where a spreadsheet tends to fall down. If you'd rather try the spreadsheet for a month first, that's a reasonable call and costs nothing.

Shall I plan it as a web app the setters use on their phones?

## Owner

Yes, a web app on their phones works. It'd be a mix of iPhone and Android.

## Agent

Settled: a web app in the phone browser, working on both iPhone and Android.

The next thing is a fact about how your gym works, and it changes what the main screen shows.

When your setters reset, do they strip a whole wall or section at once, or do they pull individual routes one at a time?

## Owner

I don't mind, you decide.

## Agent

I've made that decision and the remaining smaller ones, and the brief is below for you to check.

**What I decided without asking you** (decisions 3 to 9 in the brief):
- **Whole wall or single route:** the tool handles both. Each route is tracked individually and belongs to a wall, and a setter can take down one route or a whole wall in one action.
- **Overdue line:** a route is highlighted as overdue after 6 weeks, and the setters can change that number. Six weeks is my guess at a sensible rotation, so correct it if your gym aims for something else.
- **Routes already on the wall:** setters enter them with a best-guess date, marked as estimated.
- **Sign-in:** each setter signs in as themselves, so "who set it" is filled in automatically.

**What I'm unsure of:**
- I've assumed there is Wi-Fi or phone signal at the walls. If there isn't, say so, because working offline is a bigger build.
- Hosting may cost a few dollars a month. Nothing gets published or paid for without your say-so.

When you approve this, I'll commit the brief and start a planner, which turns it into a build plan.

---

# Project brief: route setting tracker

## The request
> I want to build something for my climbing gym so we can keep track of route setting. can you help me figure out what that should be

(2026-11-10)

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

## Not part of this
- A page members can see (what's new, what's coming down). Later work.
- Members rating or flagging routes. Later work.
- A native phone app, and anything that goes through an app store.
- Setter scheduling, hold inventory, and reports or charts.

It is a failure, even if it works, if logging a route at the wall is slow enough that setters stop doing it. Logging one route should take a few taps and well under half a minute.

## Must not change
Nothing exists today: this is a new project. Setters currently track routes by memory.

## How it will be judged
- On an iPhone and on an Android phone, a setter can log a route, see it in the oldest-first list, and take it down.
- Overdue routes stand out at a glance.
- Only the owner and the setters can judge whether it is quick enough to use at the wall. The owner tries it on their own phone before it is called finished.

## Where it runs
A web app used in the phone browser, on both iPhone and Android (the owner: "a mix of iPhone and Android"). Used at the wall, so it must work on a small screen with one hand. It needs to be hosted on the internet so all four phones see the same data.

## How the owner wants to work
The agent's decision, not confirmed by the owner: agents don't push to a remote repository, the work is built in Claude Code, and anything that spends money, publishes or can't be undone comes to the owner. Choosing and paying for hosting is one of those.

## Still open
- Where it is hosted: the planner proposes a free or low-cost option, and the owner approves it before anything is published or paid for.
- How setters sign in (for example a link, a PIN or a password): the planner chooses.
- Whether it must work with no phone signal in the gym: not decided yet. Assume the gym has Wi-Fi or signal at the walls.

---

Is this right, or is there anything you'd change?

## Owner

The back wall has no signal, so it needs to work with no signal there. That assumption in the brief is wrong.

## Agent

I've corrected the brief: working with no signal is now a requirement in your words, and the wrong assumption is gone.

What changed:

- **The request:** your correction is added, word for word, with today's date.
- **New decision 10 (yours):** "The back wall has no signal, so it needs to work with no signal there." With no signal, a setter can still see the route list as it was when the phone last had signal, log routes and take routes down. The changes are saved on the phone and sent automatically when signal returns.
- **New decision 11 (mine, for you to correct):** the app shows when changes are waiting to be sent. If two setters change the same route while out of signal, the later change is kept. With four setters that should be rare.
- **How it will be judged:** added a test that with the phone in airplane mode a setter can log a route and take one down, and the changes reach another setter's phone once signal is back.
- **Failure:** a route logged at the back wall and then lost now counts as a failure.
- **Where it runs:** says the app must open and work at the back wall without a connection.
- **Still open:** the signal question is removed, leaving hosting and how setters sign in.

This makes the build somewhat bigger, but it is still a web app in the phone browser, so decision 2 stands.

Everything else is as I showed you, including the 6-week overdue line and the other decisions I made for you. With this correction, is the brief right? If so, I'll commit it and start the planner.

## Owner

Yep, that looks right now. Go ahead.

---

Ended: the owner approved; the approval was not passed to the agent.
