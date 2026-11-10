# small-tool, with skill

## Owner

starting a little cli that tracks which houseplants need watering. plants, rooms, a watering schedule, reminders. can you set up a glossary so we use the same words

## Agent

I've written `GLOSSARY.md` at the project root with six entries: your four words plus two I had to add. All six are marked as proposed until you agree them.

| Name | Meaning |
|---|---|
| **Plant** | One houseplant that the tool tracks. Each plant is in one room and has one watering schedule. |
| **Room** | A place in the home where plants are kept, used to group plants. |
| **Watering Schedule** | How often one plant needs watering, for example every 7 days. |
| **Watering** (mine) | One occasion on which a plant was watered, with its date. |
| **Due** (mine) | The status of a plant whose watering schedule says it needs watering today or earlier. |
| **Reminder** | A message from the tool that tells you a plant is due. |

Here are the names in use, as the main thing the tool does:

1. You add a **Plant** and say which **Room** it is in.
2. You give the plant a **Watering Schedule**, such as every 7 days.
3. Each time you water the plant, you record a **Watering**.
4. The tool counts from the latest watering, and marks the plant **Due** when its schedule says so.
5. The tool shows you a **Reminder** for each plant that is due.

I guessed at three things, so correct any that are wrong:

- **Schedule per plant:** I assumed each plant has its own watering schedule, not one schedule per room.
- **Watering and Due:** these are my words for things the steps needed. If you already call them something else, your word replaces mine.
- **No separate "overdue":** a plant that is three days late is still just Due.

I also added `AGENTS.md` with one line pointing to the glossary, so later sessions find it. Once you say the names are right, I'll remove the proposed marks.

## Owner

Looks right to me, approved.

## Agent

All six names are now agreed in `GLOSSARY.md`: Plant, Room, Watering Schedule, Watering, Due and Reminder. I removed the proposed marks and changed nothing else.

---

Ended: the agent finished and asked nothing.
