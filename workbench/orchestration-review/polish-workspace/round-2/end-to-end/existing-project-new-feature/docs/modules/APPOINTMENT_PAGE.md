# APPOINTMENT_PAGE design: the page behind the private link

## The owner's request
> for the salon app I want customers to be able to move an appointment themselves instead of phoning us. brief is fine to write up, I use claude and codex both
> 2026-11-10, on reading the brief: "Decision 5 is wrong: they can't move it less than 24 hours before. The rest looks fine."

Project brief: docs/modules/BRIEF.md. Decision numbers below are the brief's.

## What people need

A customer taps the private link in their confirmation email on their phone (decision 2) and, without an account
or password, sees their appointment and moves it to a free time with as little thought as a phone call would take.
The page offers the same stylist first; choosing another is a deliberate act (decision 3: "A moved appointment
must keep the same stylist unless the customer picks a different one."). Only free times are offered (decision 4).
Less than 24 hours before the appointment the page still shows it and tells the customer to phone the salon, with
the number (decision 5). After a move the page shows the new time, and says an email is on its way (decision 6).
Customers see "appointment" everywhere (decision 1).

States the page has to handle: the appointment with a way to move it; choosing a time (same stylist by default);
choosing another stylist; confirming; moved; the time was taken while choosing (show fresh times, change
nothing); no free times within the horizon (say so and give the phone number); inside the cut-off; cancelled;
unknown link (no appointment details, phone number only).

How it looks is the owner's choice from options (brief, "Still open"), so M1 produces options and stops for the
owner.

## Mechanisms

**Server-rendered HTML forms over Node's built-in `http`**, phone-first, working with JavaScript turned off. Every
step is a plain page or form post, which is what lets it work on any phone browser from an email app's in-app
browser.

**Looking never changes anything.** Email security scanners and link previews open links in emails
automatically, so every GET is read-only and the move happens only on a POST from the confirm step. Pages behind
the link send `Cache-Control: no-store`, `Referrer-Policy: no-referrer` and `X-Robots-Tag: noindex`, so the token
doesn't leak into caches, other sites or search engines.

**The page stores nothing.** It reads and moves only through `findByLink`, `freeTimesByLink` and `moveByLink`
(ARCHITECTURE.md), and shows whatever refusal reason BOOKINGS returns. The rules (cut-off, free times, stylist)
live in BOOKINGS only, so the page can't disagree with them.

**A demo command** (`npm run demo`) starts the page on a fresh demo store with stylists and appointments, one of
them inside the cut-off, and prints each private link. That is how builders and reviewers reach the `web-mobile`
target from a clean clone.

## Who can build and review it

Builders and reviewers need a browser at phone size to take screenshots. A browser won't start inside Codex's
`workspace-write` sandbox, so this module's builder is Claude. Reviews go to the other host (Codex), whose reviewer
asks to run the browser outside the sandbox; if that is refused, the review moves to Claude.

## What this module provides
The customer-facing page. Nothing to other modules.

## Not this module's
Making the page reachable from the internet is publishing, which the owner decides. Whether customers find it
easy enough to stop phoning, and whether the front desk's hour a day shrinks, are the owner's judgement (brief,
"How it will be judged"); the first is the last item of M2, the second can only be seen after launch.
