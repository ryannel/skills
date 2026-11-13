# Graded examples to start from

A graded example is a past review, with a note on why its result was right. These five are generic, so that a
project's first reviews have something to compare with. The project's own file, named on the `Graded examples:`
line of the project settings, adds real ones over time. Where the two disagree, the project's file wins.

## A real pass

The milestone: a command-line tool reads a CSV from standard input or from a file and prints a summary, with a
useful exit code on bad input. Its items are an Automated Check over quoted fields, empty input and malformed
rows, and a Reviewer Question about whether both input routes use the same parser.

The reviewer built the commit in a clean copy and ran the check. It also tried input the tests didn't cover: a
1 GB file piped in, a file with Windows line endings, and Ctrl-C halfway through. The exit codes matched the help
text. The changed code showed one parser, called from both routes. Every item got a Pass, and the review listed
the extra inputs.

Why it is here: so that failing everything doesn't look like rigour. A Pass is right when you tried to break the
work and couldn't.

## A stub that looks finished

The milestone: a new user signs up and lands on an empty dashboard. The builder's screenshots showed every step.

The reviewer signed up, reloaded the page, and was signed out. The changed code showed the sign-up handler
returning a fixed user object, and nothing written to the database. The Automated Check passed, because it
asserted only that the dashboard rendered. The sign-up item got a Fail, with the reload as the steps to reproduce
it. The review added a finding that the check was too weak, and proposed an item that signs up, reloads and
confirms the session survives.

Why it is here: the screenshots were real, and the check passed. Only using the product and reading the changed
code showed there was nothing behind them.

## Works on the easy path only

The milestone: a boat's wake develops, turns and fades across the speed range. The builder's frames showed the
boat at cruising speed in a straight line.

The reviewer wrote an inspection list (the wake at rest, at low speed, at full speed, in a hard turn, and as it
fades) and recorded each one. At full speed, the wake was a texture scrolling with the boat. It didn't develop or
fade, and in the turn it bent with the hull instead of trailing behind. The item got a Fail, with the frames for
each entry on the list.

Why it is here: the builder's recording was honest, but it showed only the one case that worked.

## Couldn't reach the target

The milestone includes an item proved on a physical iPhone. The reviewer had only the simulator.

That item got Could Not Judge (`could_not_judge`), not a Pass, with the reason: no device was available, and the
simulator can't show performance. The review said what would settle it, which was a frame-time recording from the
device. Everything else passed. The review ended `0 fail, 1 could_not_judge`, so the builder's next attempt knows
exactly what evidence to bring.

Why it is here: a result from a stand-in is useful, but it never becomes a Pass on the real target.

## Meets the numbers, misses the look

The milestone: twelve harbour props for a low-poly sailing game, judged against the option the human chose, which
was hand-painted, chunky and slightly crooked. Every prop loaded, sat under its triangle budget and shared one
texture atlas, so the Automated Checks passed.

The reviewer wrote an inspection list (the silhouette at the game camera's distance, edge wear, the palette
beside the reference, and how the set reads together). It took screenshots of each prop beside the reference,
from four angles and at play distance. Nine props matched. The crane, a bollard and the lantern had clean, even
bevels and a brighter palette, and read as a different set. The look item got a Fail that named those three props
and the two qualities that differed, with the side-by-side screenshots. The budget and format items passed.

Why it is here: an item judged by taste fails on named qualities beside the reference, piece by piece, and never
on a general impression. Passing checks don't carry it either.
