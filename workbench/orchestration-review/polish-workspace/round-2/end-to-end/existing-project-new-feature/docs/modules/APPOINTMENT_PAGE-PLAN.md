# APPOINTMENT_PAGE plan
Reviews: design review at bb1ebc7, DESIGN OK (docs/evidence/APPOINTMENT_PAGE/design-review.md)
Milestone: M1 Three looks for the appointment page, for the owner to choose from
Now: M1 options built and on the sheet; waiting for the owner to choose (since 2026-11-10)
Next: M2 A customer moves their appointment from the email link on a phone (waits for BOOKINGS:M2 and the owner's choice)
Blocked: M1.2, the owner choosing A, B, C or a mix from docs/evidence/APPOINTMENT_PAGE/options.png

## M1 Three looks for the appointment page, for the owner to choose from: in progress
- [x] Three options, different in kind, for the appointment and choose-a-time screen, at 375 px
- [x] One side-by-side image at docs/evidence/APPOINTMENT_PAGE/options.png, at real size and enlarged
- [ ] The owner picks one

## M2 A customer moves their appointment from the email link on a phone: not started
- [ ] Server-rendered pages for every state in the design, in the chosen look, working without JavaScript
- [ ] GET never changes anything; moves only on POST; no-store, no-referrer, noindex
- [ ] `npm run demo` starts the page on a fresh demo store and prints the links
- [ ] The owner tries it on their own phone

## Log
- 2026-11-10 Planned from the brief. The brief asks for look options first ("The owner will choose from options, so the first piece of work should produce them"), so M1 is options; it needs no real data and runs alongside BOOKINGS.
- Assumption: three options, for the screen that shows the appointment and offers new times, since that screen decides the rest of the look.
- Assumption: the builder for this module is Claude, because building and inspecting the page needs a browser, which won't start in Codex's workspace-write sandbox. Reviews go to Codex, which asks to run the browser outside the sandbox, or move to Claude if refused.
- Assumption: the page works without JavaScript, so it works in any email app's in-app browser.
- 2026-11-10 M1 built (verified): three options as static HTML mockups in docs/evidence/APPOINTMENT_PAGE/options/: A card and day list, B week strip, C plain letter. They were rendered at 375 px with phone emulation in headless Chrome over DevTools (the Chrome headless window has a 500 px minimum) and laid out in options.png at real size and 2x. Builder inspection is in options.md. Not verified: how they look on a real phone's browser. M1.2 waits for the owner.
