# small-tool, with skill

## Owner

starting a little cli that tracks which houseplants need watering. plants, rooms, a watering schedule, reminders. can you set up a glossary so we use the same words

## Agent

I wrote `GLOSSARY.md` at the project root with six names: your four, plus two I had to add and have marked as proposed. I also added an `AGENTS.md` with one line pointing later sessions at the glossary.

Your four names:

- **Plant**: one houseplant the tool tracks. It lives in one room and has its own watering schedule.
- **Room**: a place in the home where plants are kept, used to group them.
- **Watering Schedule**: how often a plant needs watering, such as every 7 days.
- **Reminder**: a message from the tool telling you a plant is due.

The two I proposed, because the steps below can't be written without them:

- **Watering**: one occasion on which a plant was watered, recorded with its date.
- **Due**: the status of a plant whose watering schedule says it needs water today or earlier.

Here are the names in use:

1. You add a **Room**.
2. You add a **Plant** to that room and give it a **Watering Schedule**.
3. Each day the tool checks every plant's schedule against its latest **Watering** and marks the ones that are **Due**.
4. The tool shows you a **Reminder** for each due plant.
5. You water the plant and record a **Watering**. The plant is no longer due until its schedule comes round again.

Three things for you to confirm or change:

1. **Watering and Due**: are those the words you'd use? If so I'll remove the proposed marks.
2. **Overdue**: I've folded it into Due, so a plant three days late is still just "due". Say so if you want a separate status.
3. **One schedule per plant**: I wrote the schedule as belonging to each plant and counted from its latest watering. If you meant one schedule for the whole home, that entry changes.

## Owner

Looks good, those words work. Keep overdue folded into due, and one schedule per plant is right.

## Agent

All six names in `GLOSSARY.md` are now agreed: I removed the proposed marks from **Watering** and **Due**.

The **Due** entry now says a plant that is days late is still Due, with no separate late status, and "overdue" stays on its avoid list. The one-schedule-per-plant wording was already in the **Plant** entry, so that needed no change.

---

Ended: the agent finished and asked nothing.
