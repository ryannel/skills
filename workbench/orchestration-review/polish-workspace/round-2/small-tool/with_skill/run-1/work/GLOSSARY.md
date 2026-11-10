# Glossary

The names this project uses, and what each one means. Plans, code, text on screen and chat all use these names.
An entry with a `Proposed:` line has not been agreed by the owner yet.

**Plant**
One houseplant that the tool tracks. Each plant is in one room and has one watering schedule.

**Room**
A place in the home where plants are kept, such as the kitchen. A room is used to group plants.

**Watering Schedule**
How often one plant needs watering, for example every 7 days.
Not: Reminder. The schedule is the rule, and a reminder is the message that the rule produces.
Avoid: interval, frequency, cadence

**Watering**
One occasion on which a plant was watered, with its date. The next due date is counted from the latest watering.
Not: Watering Schedule. A watering has happened, and a schedule says when the next one should.
Avoid: log entry, event

**Due**
The status of a plant whose watering schedule says it needs watering today or earlier.
Avoid: thirsty, overdue, pending

**Reminder**
A message from the tool that tells you a plant is due.
Avoid: alert, notification
