# small-tool, without skill

## Owner

starting a little cli that tracks which houseplants need watering. plants, rooms, a watering schedule, reminders. can you set up a glossary so we use the same words

## Agent

I wrote `GLOSSARY.md` in the project root. It defines each term once and lists the synonyms we won't use (e.g. "room", not "location" or "zone").

| Group | Terms |
|---|---|
| Things | plant, name, species, room |
| Watering | watering (the recorded event), water (the verb), schedule, interval, last watered, next due |
| Status | OK, due, overdue, needs water (due or overdue) |
| Reminders | reminder, snooze |

In writing the definitions I made some design calls you should check:

- **One room per plant:** a room is only a grouping, with no schedule or settings of its own.
- **A schedule is just an interval:** each plant has one schedule, "every N days", with no weekday or seasonal rules yet.
- **Next due is derived:** it is last watered plus interval, never stored. A plant with no waterings counts as due immediately.
- **Due vs. overdue:** "due" means today only; "overdue" means the date has passed.
- **Reminders are generated:** they come from plant status and aren't objects you create or delete.
- **Snooze:** I added this term for pushing next due back without recording a watering. "Skip" is banned as ambiguous.
- **Out of scope:** fertilizing, misting and repotting; "watering" means water only.

Tell me which of these are wrong and I'll change the glossary before we write any code against it.

## Owner

Looks good to me, those all work. Go ahead.

## Agent

The CLI is built: `plants.py` in the project root, a single Python file with no dependencies, using the glossary's words throughout. I ran every command against a throwaway data file and they all behaved as expected. One wording fix ("every 1 day") went in after that run and wasn't re-run, and there is no automated test suite yet.

```
$ python3 plants.py add Gerald --room kitchen --every 7 --species pothos --watered 2026-11-01
$ python3 plants.py list
NAME              ROOM     INTERVAL  LAST WATERED  NEXT DUE    STATUS
Gerald            kitchen  7d        2026-11-01    2026-11-08  2 days overdue
Kitchen Monstera  kitchen  10d       2026-10-31    2026-11-10  due
Fern              balcony  3d        2026-11-09    2026-11-12  OK
$ python3 plants.py remind
2 plants need water:
  Gerald (kitchen): 2 days overdue
  Kitchen Monstera (kitchen): due
```

| Command | What it does |
|---|---|
| `add NAME --room ROOM --every DAYS [--species S] [--watered DATE]` | Add a plant |
| `water NAME... [--on DATE]` | Record a watering (today by default) |
| `snooze NAME DAYS` | Push next due back without recording a watering |
| `list [--room ROOM]` | All plants with status, soonest due first |
| `remind [--room ROOM]` | Only the plants that need water |
| `show NAME` | One plant's details and its waterings |
| `rooms` | Rooms with plant counts |
| `move NAME ROOM` | Move a plant to another room |
| `schedule NAME DAYS` | Change a plant's interval |
| `remove NAME` | Delete a plant and its waterings |

Things I decided that the glossary didn't settle:

- **Python:** you didn't name a language, so I picked it for a zero-install single file. Say so if you wanted something else.
- **Data file:** everything is stored in `~/.plants.json`; set `PLANTS_FILE` to put it elsewhere.
- **Rooms are implicit:** a room exists while at least one plant is in it, so there is no "add room" command.
- **Snooze counts from today for overdue plants:** snoozing a plant that is 2 days overdue by 2 days makes it due in 2 days, not due today.
- **Watering clears a snooze:** it also rejects future dates.
- **Names match case-insensitively:** multi-word names need quotes (`"kitchen monstera"`).
- **Reminders are pull-only:** `remind` prints when you run it; nothing notifies you on its own yet.

Next I'd suggest a scheduled daily `remind` (cron or launchd) and a small test suite — tell me if you want either.

---

Ended: the agent finished and asked nothing.
