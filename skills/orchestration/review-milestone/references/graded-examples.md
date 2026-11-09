# Graded examples to start from

These four are generic, so a project's reviews never start with nothing to calibrate against. The project's own file,
named by the profile's `Graded examples` line, adds real ones over time, and where the two disagree, the project's
file wins.

## A real pass

The milestone: a CLI reads a CSV from stdin or a file and prints a summary, with a useful exit code on bad input. Its
items are a check over quoted fields, empty input and malformed rows, and an `ask` about whether both input routes use
the same parser.

The reviewer built the commit in a clean checkout and ran the check. It also tried input the tests didn't cover: a
1 GB file piped in, a file with Windows line endings, and Ctrl-C halfway through. The exit codes matched the help
text. The diff showed one parser, called from both routes. The verdict was pass on every item, with the extra inputs
listed in the review.

Why it's here: so that failing everything doesn't look like rigour. A pass is right when you tried to break it and
couldn't.

## A stub that looks finished

The milestone: a new user signs up and lands on an empty dashboard. The builder's screenshots showed every step.

The reviewer signed up, reloaded the page, and was signed out. The diff showed the sign-up handler returning a fixed
user object, and nothing written to the database. The check passed, because it only asserted that the dashboard
rendered. The verdict was fail on the sign-up item, with the reload as the reproduction. The review added a finding
that the check was too weak, and proposed an item that signs up, reloads and checks that the session survives.

Why it's here: the screenshots were real, and the check passed. Only using the product and reading the diff showed
there was nothing behind it.

## Works on the happy path only

The milestone: a boat's wake develops, turns and fades across the speed range. The builder's frame sequence showed the
boat at cruising speed in a straight line.

The reviewer wrote an inspection list (wake at rest, at low speed, at full speed, in a hard turn, and as it fades) and
captured each one. At full speed, the wake was a texture scrolling with the boat. It didn't develop or fade, and in
the turn it bent with the hull instead of trailing behind. The verdict was fail, with the frames for each entry.

Why it's here: the builder's capture was honest, but it only showed the one case that worked.

## Couldn't reach the target

The milestone includes an item proved on a physical iPhone. The reviewer had only the simulator.

The verdict on that item was `cant_tell`, not pass, with the reason given: no device was available, and the simulator
can't show performance. The review said what would settle it, which was a frame-time capture from the device.
Everything else passed. The milestone failed with `0 fail, 1 cant_tell`, so the builder's next attempt knows exactly
what evidence to bring.

Why it's here: a stand-in result is useful, but it never turns into a pass on the real target.
