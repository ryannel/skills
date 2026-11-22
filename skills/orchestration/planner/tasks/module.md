# Planning a module

Planning a module means writing its design and its next milestones, with their items. The same task plans a
module's next milestones once the ones already planned are nearly built.

Each module has a folder in the plans folder with its design `DESIGN.md`, its plan file `PLAN.md`, its log `LOG.md`
and its done-when file `DONE.json`. [The module's files](../references/done-when.md) gives each one's shape. Builders
and reviewers act on the design and the notes in the plan file, so write them the way the `prompting-agents` skill
describes.

## The design

`DESIGN.md` says what the module's end users need to see, feel or get, and across what range. It names the mechanism
that produces each of those, and says what the module provides to other modules.

Most problems have been solved before, in shipped products or published work, so find out how before you invent a
mechanism, and prefer current practice. Check that each mechanism can produce its behaviour across the whole range
before anyone builds on it, because a reviewer will try the edge of any range the design leaves open. Where the
product promises exactness, as with money, say what keeps it exact and up to what size of input.

Use only numbers that are real: from the brief, from the user, or measured. A bound nobody measured becomes a target
builders fail against, so make measuring it the milestone's first item, and set the bound from the result.

## The milestones

Make each milestone one outcome a reviewer can judge, small enough for one builder session, which for current models
is hours of work. Each milestone costs a builder run, the checks and usually a review, so a finer split pays those
costs again without making the work better. Name each for what someone can see or do once it is Done, such as "A new
end user signs up and lands on an empty dashboard", because that name is what the user reads on the status page.

Write items for the next one or two milestones, the ones you can define well from what is known now, or as far as
your task says. Name the later ones in `PLAN.md` as headings with an ID and an outcome, and no items. When a module
has one planned milestone left, the lead starts a planner to write the next ones, and by then the built work has
answered questions you would otherwise guess at. New milestones and a changed design wait for a design review
before any builder starts them.

When the module has been building, read its reviews first. A finding that came up in two reviews becomes an item,
because a builder fixing one review at a time won't stop it coming back. You may change the design, and rename,
merge or drop a named milestone the built work has made wrong. If another module's `depends_on` names it, change
that module too.

Under a planned milestone in `PLAN.md`, write only what its builder couldn't work out from the items and the design:
what already exists and where, what another module owns that it uses, or an order where the order is part of the
task. Leave out a list of steps, because the builder sees the code close up and plans the work better.

## What it needs from other modules

Write each interface first, so this module can be built against a simple stub that follows the interface until it
needs the real thing. Then, for each thing this module uses from another, find the milestone there that delivers it,
and add it, written `"CORE:M3"`, to the `depends_on` field of the first milestone here that can't work without it. If
no milestone delivers it yet, add one to the owning module. A `depends_on` entry may name a milestone that so far has
only a heading, so keep milestone IDs the same once written. When your task is limited to this module, another
module's folder isn't yours to change, so end with `BLOCKED: needs <MODULE>'s files`, saying what that milestone must
deliver, and the lead gives the task to a planner for the whole project.
