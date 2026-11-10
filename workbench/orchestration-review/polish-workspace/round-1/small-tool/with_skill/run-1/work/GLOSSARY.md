# Glossary

The names this project uses. Plans, code, on-screen text and chat all follow them.
Every entry is agreed by the owner unless it has a `Proposed:` line.

**Plant**
One houseplant that the tool tracks. Each plant lives in one room and has its own watering schedule.

**Room**
A place in the home where plants are kept, such as the kitchen. Used to group plants.
Avoid: location, area

**Watering Schedule**
How often a plant needs watering, such as every 7 days.
Not: Reminder. The schedule is the rule; a reminder is the message that the rule produces.
Avoid: interval, frequency, cadence

**Watering**
One occasion on which a plant was watered, recorded with its date. The next due date is counted from the latest one.
Not: Watering Schedule. A watering is something that happened; the schedule is how often it should happen.
Avoid: log entry, event

**Due**
The status of a plant whose watering schedule says it needs water today or earlier. A plant that is days late is still Due; there is no separate late status.
Not: Reminder. Due is a status the plant has whether or not anyone was told.
Avoid: thirsty, pending, overdue

**Reminder**
A message from the tool telling the owner that a plant is due.
Avoid: alert, notification
