# Glossary

The words this project uses, in code, CLI output, and conversation. One word per
concept: if a term is listed under "Not" below, don't use it.

## Things

**Plant**
One physical houseplant you own. Has a name, belongs to exactly one room, and has
exactly one schedule. Two pothos are two plants.
Not: *item*, *entry*.

**Name**
The label you give a plant ("Kitchen Monstera", "Gerald"). Unique across all
plants; it is how you refer to a plant on the command line.
Not: *nickname*, *label*, *id*.

**Species**
What kind of plant it is ("Monstera deliciosa", "pothos"). Optional, free text,
purely informational.
Not: *type*, *kind*, *variety*.

**Room**
A named place where plants live ("kitchen", "balcony"). A room is only a grouping:
it has no schedule and no settings of its own. A plant is in exactly one room.
Not: *location*, *area*, *zone*, *group*.

## Watering

**Watering**
A recorded event: this plant was watered on this date. Waterings are history and
are never edited into the future.
Not: *log entry*, *event*, *session*.

**Water** (verb)
To record a watering for a plant. `water gerald` means "I watered Gerald", not
"Gerald needs water".

**Schedule**
A plant's rule for how often it wants water. Belongs to one plant. For now a
schedule is just an interval.
Not: *plan*, *routine*, *frequency*, *calendar*.

**Interval**
The number of days between waterings in a schedule ("every 7 days"). Always whole
days.
Not: *frequency*, *period*, *cadence*.

**Last watered**
The date of a plant's most recent watering. A plant with no waterings yet has no
last-watered date and counts as due immediately.

**Next due**
The date a plant should next be watered: last watered + interval. Derived, never
stored.
Not: *deadline*, *next watering*.

## Status

Every plant is in exactly one of these states on a given day.

**OK**
Next due is in the future.

**Due**
Next due is today.

**Overdue**
Next due has passed. "3 days overdue" means next due was 3 days ago.
Not: *late*, *thirsty*, *missed*.

**Needs water**
Umbrella term for due *or* overdue. Use this when the distinction doesn't matter
("4 plants need water").

## Reminders

**Reminder**
A message telling you which plants need water. Reminders are generated from plant
status; they are not stored objects you create or delete one by one.
Not: *alert*, *notification*, *alarm*, *nudge*.

**Snooze**
To push a plant's next due date back by some days without recording a watering.
The schedule and the watering history are unchanged.
Not: *skip*, *postpone*, *delay*.

## Deliberately not terms

- **Task / to-do**: we track plants and their status, not a task list.
- **Skip**: ambiguous between "snooze" and "pretend I watered it". Use *snooze* or
  *water*.
- **Fertilize, mist, repot**: out of scope until we decide otherwise. "Watering"
  means water only.
