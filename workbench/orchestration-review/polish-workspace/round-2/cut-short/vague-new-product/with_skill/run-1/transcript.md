# vague-new-product, with skill

## Owner

I want to build something for my climbing gym so we can keep track of route setting. can you help me figure out what that should be

## Agent

Yes. The project folder is empty, so this is a fresh start with nothing existing to work around.

What I have so far: you want a tool for your climbing gym that keeps track of route setting. That could turn into quite different things depending on what you need from it, so before I suggest any shape for it:

**Why do you want this? What is happening at the gym today that made you want to build it?**

## Owner

Routes stay up too long. Members complain the walls feel stale, and nobody knows which routes are the oldest. Setters just go by memory.

## Agent

That points at a clear core: a record of every route on the wall and the date it went up, so anyone on staff can see which routes are oldest and what is due to come down. Setters log a route when they set it and mark it gone when they strip it.

The decision that changes the build most is who it is for:

1. **Setters and staff only.** A private tool for logging routes and seeing the oldest ones. This is the smallest build and it goes straight at the problem you described.
2. **Staff, plus a page members can see.** Members could see what is new and what is coming down. It tackles the "stale" feeling from their side too, but it adds a public page, and the data has to be kept tidy enough to show.
3. **Members take part.** They rate, comment on or tick off routes. This is a much bigger product, with member accounts and moderation.

I recommend option 1. Your problem is that nobody knows which routes are oldest, and a staff tool fixes that. A member page can be added later on top of the same records.

**Shall I plan it as a staff-only tool, with anything member-facing left for later?**

## Owner

Yes, staff only is fine. The setters are the ones who'll use it.

## Agent

Staff only it is, with the setters as the users. I've noted the member-facing ideas as later work.

One question now that only you can answer, and it shapes the rest:

**What would make this a failure even if it works as described? Think of the setters, the gym, and how a setting day really goes.**

## Owner

It has to work with no signal. The back wall has none, so if it needs internet there, the setters won't use it. And it has to look good, because they won't use something ugly.

## Agent

Both are in the brief in your words. Two things follow from them:

- **No signal:** everything a setter does at the wall will work with no connection at all.
- **Looks:** we can't settle that by talking, so the first piece of work will produce a few visual options for you to choose from before anything is built on top.

The no-signal rule makes the next decision the expensive one: what the setters hold in their hands.

1. **Each setter's own phone.** It works offline at the back wall and catches up with everyone else's records once the phone is back in signal. Nobody has to fetch a device, and it runs on both iPhone and Android. It costs more to build, because phones have to merge their records, and it needs a small hosted service to hold the shared copy, which may carry a small monthly cost.
2. **One shared gym tablet or phone.** All the records live on that one device, and it never needs internet. This is the simplest and cheapest build. The costs are that setters have to pass it around, and if it breaks or goes missing the records go with it unless someone backs it up.

I recommend option 1. Setters already have a phone in their pocket, and a tool they have to go and fetch is one they will skip, which puts you back to memory.

**Shall I plan it for each setter's own phone?**

## Owner

Yes, each setter's own phone is fine. Mix of iPhone and Android, so it needs to work on both.

---

Ended: the owner approved; the approval was not passed to the agent.
