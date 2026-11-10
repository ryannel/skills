# APPOINTMENT_PAGE M1: three looks for the appointment page

Sheet for the owner: `docs/evidence/APPOINTMENT_PAGE/options.png` (2440 × 2510). It shows the three options at real
size (375 px wide), with a dashed line at 812 px for the bottom of an iPhone screen, and the top of each enlarged 2×.
Sources: `options/*.html`. Each option is also saved on its own at 375 px as `options/*.png`. Regenerate everything
with `node docs/evidence/APPOINTMENT_PAGE/options/capture.mjs`. It drives headless Chrome over the DevTools Protocol
with phone emulation (375 px, touch, scale 1), because Chrome's headless window can't go below 500 px wide. The
capture log confirms `viewport 375px wide` for each option and no sideways overflow (page width 375).

Sample appointment, the same in all three: Jordan, Cut & finish with Maya, 45 min, Thursday 19 November 2026 at
10:30, at Studio Nine (020 7946 0321). The free times are the same in all three as well.

| Option | Kind | Tap targets (CSS) | Height |
|---|---|---|---|
| A · Card and day list | Appointment card, then every free day as a card with a 3-column grid of time buttons. Browse by scrolling. | time buttons 48 px tall, about 100 px wide; "Later days" 48 px; stylist row 62 px | 923 px (stylist link and phone number are below the fold) |
| B · Week strip | Dark header with a date tile; stylist row with "Change"; pick a day from a strip, then one of that day's times. Two steps. | day tiles 64 × 52 px; time pills 52 px, full width; "Change" 44 px | 812 px |
| C · Plain letter | Serif text that reads like a note from the salon; Maya's five soonest times as a ruled list; other days and stylists as text links. | list rows 58 px, full width; links 46 px | 819 px |

## Inspection (builder, 2026-11-10)

Pieces looked at, for each option at 375 px and at 2×:

- **The current appointment** (day, date, time, service, stylist). A, B and C each state it in full and it reads at
  a glance. B splits the date into a tile, which is still readable. Pass.
- **The free times** (readable, tappable). Every target is at least 44 px tall. No text is clipped or wraps badly at
  375 px or at 2×. Pass.
- **The same stylist by default; another stylist is a deliberate step.** A: "Free times with Maya", plus a separate
  "Choose a different stylist" row ("You'll stay with Maya unless you do"). B: "Maya (your stylist)" with "Change".
  C: "Maya's soonest free times" and a "See times with another stylist" link. Pass.
- **The phone number for when nothing suits.** It is on all three. In A it is below the fold. Pass.
- **Nothing changes on a tap.** A and C say so in words ("before anything changes", "before it is made"). B doesn't.
  This is a note for the chosen look, not a fault in an option.
- **Different in kind, not in colour alone.** Each option navigates differently: scroll every day (A), pick a day
  and then a time (B), or the soonest times first with other days behind a link (C). Their typography (system sans,
  geometric sans, serif) and structure (cards, header band with pills, ruled list) also differ. Pass.

These are options for the owner to turn down, so they are held to the milestone's bar and nothing more. Building the
real pages, with every state, is M2.

## The owner's choice (M1.2)

Not made yet. The owner needs to look at `options.png` and say A, B, C or a mix. The lead records the answer with
`owner answer`.
