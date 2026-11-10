# Project settings: salon

- **Purpose:** docs/modules/BRIEF.md  *(customers move their own appointment)*
- **Quality bar:** Customer pages as plain and quick on a phone as moving a booking from a Fresha or Treatwell confirmation email; emails as clear as those services' booking-change emails
- **Anchors:** docs/evidence/APPOINTMENT_PAGE  *(the look options, and the one the owner chooses)*
- **Plans:** docs/modules  *(script)*
- **Evidence:** docs/evidence  *(script)*
- **Graded examples:** docs/evidence/graded-examples.md
- **Check:** npm test  *(script)*
- **Integrate:** local  *(script)*
- **Branch:** main  *(script)*
- **Remote:** origin  *(script)*
- **Builders:** one builder per module: BOOKINGS on Codex; APPOINTMENT_PAGE on Claude, because its work drives a browser
- **Default host:** codex  *(script)*
- **Review host:** other  *(script: the owner uses both Claude and Codex)*
- **Codex sandbox:** workspace-write  *(script)*

## Starting from a clean clone
No dependencies to install today (Node 24, built-in `node:test` and `node:sqlite`). Planned, delivered by
APPOINTMENT_PAGE M2: `npm run demo` creates a fresh demo store with stylists and appointments (including one inside
the 24-hour cut-off), starts the appointment page, and prints each appointment's private link. It takes `PORT` and
the store's path from the environment, so two worktrees never share a port or a database. Real salon settings live
in `config/salon.json` (BOOKINGS M1).

## Targets

| Target | What it is | Run | Capture | Edge conditions |
|---|---|---|---|---|
| node | BOOKINGS code under Node 24 | `npm test` | test output and exit code | DST change in the salon's time zone, end of the booking horizon, closing time, concurrent writers |
| web-mobile | The appointment page in a phone-sized browser (375 × 812, touch) | `npm run demo` | screenshots of each state, network log | unknown link, inside the cut-off, time just taken, no free times, cancelled appointment, slow network |
| outbox | Emails as the development sender writes them to a folder | `npm run demo`, then a move | the written email files | moved twice, stylist changed, long names |

## Rules
- **Exclusive resources:** none
- **Large captures:** screenshots are small enough to commit under docs/evidence
- **Owner decides:** changing the goal or a decision the owner made in the brief; spending money, including choosing an email provider; sending real email to customers; publishing or deploying the page where customers can reach it; pushing to a remote; Codex sandbox danger-full-access; anything that can't be undone  *(script)*
- **Licences and paths not to touch:** none set by the owner  *(script)*

## Project guidance
- Customers see "appointment"; the code says `booking` (see docs/modules/GLOSSARY.md).
