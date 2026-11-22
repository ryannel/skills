# Changing the plan

Something has changed what the plan should say: the user's words, their answer to an assumption, or a builder's
proposal to change an interface. Change only what it reaches, because the script sets back to Not Started each
milestone whose items you change, and holds back each module whose design you change until a new design review
passes.

## The user changed what they want

The lead sends you what the user asked for, and has already added it to the brief. Change the plan to match, and
quote their words in `LOG.md`. If you change what a milestone that is Waiting: For Diagnosis asks for, its items,
quality bar or `depends_on`, the script counts your change as its diagnosis. If you change the items of a milestone
Blocked with Too Many Failed Reviews, the script starts it again with its review counts cleared, because only the
user sends one of those back to a planner.

Some changes reach many modules, such as a looser quality bar for all visual work. Change first the modules the
lead's task names, and the milestones being built or Blocked on an item the change makes pointless, because that is
where the old wording costs most now. Make the whole change in each module you touch, and list in your report the
modules you left, so the lead can start a planner for them.

## The user chose one of a set of options

Rewrite the quality bar and the `inspect` checklists of the later milestones that carry the look against the chosen
option, which the builder saved in the folder the settings' `References:` line names, because they were written
before it existed. When the user turned every option down, read their words against the reference: if the reference
is what they don't want, choose another, and plan a new set of options.

## The user answered an assumption

Delete the `Assumption:` line, note the answer in `LOG.md`, and change whatever the answer reaches.

## A builder proposed an interface change

Settle the proposal from the builder's module log for every module that provides or uses that interface: change the
interface in the module list and in each of those designs together, so no two modules disagree about it.
