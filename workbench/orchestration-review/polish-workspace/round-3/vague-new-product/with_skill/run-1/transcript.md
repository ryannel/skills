# vague-new-product, with skill

## Owner

I want to build something for my climbing gym so we can keep track of route setting. can you help me figure out what that should be

## Agent

Yes. The folder I'm working in is empty, so this is a fresh start with nothing existing to fit around.

What I understand so far: you want a tool for your climbing gym that keeps track of route setting. "Keeping track" could mean quite different things to build, and which one is right depends on what's behind the request.

So, first question: why do you want this? What is happening at the gym now that made you want to build it?

## Owner

Routes stay up too long. Members complain the walls feel stale, and nobody really knows which routes are the oldest. Setters just go by memory.

## Agent

That narrows it a lot. The job is to make the age of every route visible, so setters stop relying on memory and the oldest routes come down first. I've started a draft brief with your words in it.

The whole tool turns on one number that only you can give: how long is too long for a route to stay up? If the answer differs by wall, by grade, or between boulders and rope routes, tell me the rule as you'd say it to a setter.

## Owner

nothing should be up more than 6 weeks

## Agent

Recorded in the draft brief, in your words: nothing up more than 6 weeks, one rule for every route.

Next question, and it's one I shouldn't guess at: imagine the tool is built and does exactly what we've described. What would make it a failure anyway?

## Owner

It would be a failure if it doesn't work at the back wall, because there's no signal there. Setters have to be able to use it with no connection. Also, it has to look good, because the setters won't use something ugly.

## Agent

Both are in the draft brief in your words. On looks: that can't be settled by describing it, so I've written that the first piece of work produces a few visual options and you pick one. Say so if you'd rather handle it differently.

The no-signal requirement makes the next decision the big one: what the setters hold in their hands at the wall.

- **Their own phones, as a web app (my recommendation).** Each setter opens it in the phone's browser once and adds it to the home screen. It works with no connection and syncs with everyone else's when the phone is back in signal. It runs on iPhone and Android alike, with no app store and no fees. The cost is that two setters working offline at the same time won't see each other's changes until they sync.
- **Their own phones, as an app-store app.** Same behaviour, but it needs separate iPhone and Android builds, store accounts and review. That's much more work for no gain I can see here.
- **One tablet owned by the gym.** There's nothing to sync, because there is only one copy. The cost is that the setters share a single device and someone has to carry it up to the wall.

Shall I write it down as the first one: setters use their own phones, through a web app that works offline?

## Owner

Yes, the first one works. Phones, mix of iphone and android, so the one that works on both.

## Agent

That settles what I needed to ask. Below is the full brief: the page a planning agent will work from, without being able to ask you anything.

Before you read it, these are the things I decided without asking you, so check them hardest:

- **It's for setters only.** Nothing for members, no setter scheduling, no hold inventory.
- **No reminders.** A setter sees what's past 6 weeks when they open the app; it doesn't notify anyone.
- **What a route record holds:** wall, grade, hold colour, date it went up, who set it.
- **Routes already on the wall** get entered once at the start, with a best-guess date where nobody remembers.
- **Syncing needs a shared copy kept online**, which may cost a small monthly amount. Nothing gets spent without coming to you first.
- **You pick the look** from a few options that the first piece of work produces.

When you approve, I will commit the brief and start a planning agent on it. Your approval covers both.

---

# Project brief: route setting tracker

## The request
> I want to build something for my climbing gym so we can keep track of route setting. can you help me figure out what that should be

(2026-11-10)

## Why
The owner, 2026-11-10: "Routes stay up too long. Members complain the walls feel stale, and nobody really knows which routes are the oldest. Setters just go by memory."

## Who it is for, and what they will be able to do
The gym's setters, on their own phones, at the wall. A setter can:
- record a route when it goes up, and mark it as taken down when it is stripped;
- see every route that is currently up with its age, oldest first, with anything past the limit standing out;
- do all of this with no connection, and have it reach the other setters' phones once the phone is back in signal.

The list of what a setter can do is the agent's reading of the owner's reason. Not confirmed by the owner.

## Decisions
1. A route is too old once it has been up more than 6 weeks, with no exceptions by wall, grade or type. The owner, 2026-11-10: "nothing should be up more than 6 weeks"
2. Setters must be able to use it with no connection, including at the back wall. The owner, 2026-11-10: "It would be a failure if it doesn't work at the back wall, because there's no signal there. Setters have to be able to use it with no connection."
3. It has to look good. The owner, 2026-11-10: "it has to look good, because the setters won't use something ugly."
4. Setters use their own phones, a mix of iPhone and Android, through a web app that is added to the home screen, works offline and syncs when back in signal. Proposed by the agent, and agreed by the owner: "Yes, the first one works. Phones, mix of iphone and android, so the one that works on both."
5. The owner picks the look from a few visual options, and the first piece of work produces those options. The agent's decision, because looks can't be agreed in words. Not confirmed by the owner.
6. A route record holds: which wall, the grade, the hold colour, the date it went up, and who set it. The agent's decision, because that is the least a setter needs to find the route on the wall and know its age. Not confirmed by the owner.
7. Routes already on the wall are entered once at the start, with a best-guess date where nobody remembers the real one. The agent's decision, because the tool is useless until the current walls are in it. Not confirmed by the owner.
8. Two setters working offline at the same time don't see each other's changes until both have synced, and no change is lost when they do. The agent's decision, following from decisions 2 and 4; the cost was put to the owner with decision 4.

## Not part of this
A failure even if it works, in the owner's words (2026-11-10): "It would be a failure if it doesn't work at the back wall, because there's no signal there." And: "it has to look good, because the setters won't use something ugly."

Left out:
- Anything for members: a public route list, ratings, comments, logging climbs. The agent's reading. Not confirmed by the owner.
- Scheduling setters, planning resets, hold inventory. The agent's reading. Not confirmed by the owner.
- Reminders or notifications when a route passes 6 weeks. The setter sees it when they open the app. The agent's reading. Not confirmed by the owner.
- An app-store app. Put to the owner as an option and not chosen.

## Must not change
Nothing exists today: the project folder was empty on 2026-11-10, and setters track routes by memory.

## How it will be judged
Only the owner can judge these:
- At the back wall, on a phone with no signal, a setter can record a route and see the list of route ages. Tested on both an iPhone and an Android phone.
- After walking back into signal, that route appears on another setter's phone.
- The owner can say within seconds which routes are the oldest and which are past 6 weeks.
- The owner likes the look enough to put it in front of the setters.

The checks are the agent's proposal, drawn from the owner's reason and failure conditions. Not confirmed by the owner.

## Where it runs
In the browser on setters' own phones, iPhone and Android, added to the home screen, working offline (decision 4). Syncing needs a shared copy of the data kept online.

## How the owner wants to work
The agent's decisions, not confirmed by the owner: the work is built in Claude Code, the program this chat runs in. Agents don't push to a remote repository. Anything that spends money, publishes, or can't be undone comes to the owner first.

## Still open
- Where the shared online copy is hosted, and what it costs. The planner chooses; any spending comes to the owner before it happens.
- Whether setters sign in, and how. The planner chooses the simplest thing that records who set a route.
- How many setters and routes there are. Not asked. Assume a single gym: under 20 setters and a few hundred routes.

---

Is this right, or what should change?

## Owner

Looks right to me, go ahead.

---

Ended: the owner approved; the approval was not passed to the agent.
