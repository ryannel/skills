# Changing the plan

Something has changed what the plan should say: the user's words, their answer to an assumption, or a builder's
proposal to change an interface. Change only what it reaches.

## The user changed what they want

The lead sends you what the user asked for, and has already added it to the brief. Change the plan to match, and
quote their words in `LOG.md`.

Some changes reach many modules, such as a looser quality bar for all visual work. Change first the modules the
lead's task names, and the milestones being built or Blocked on an item the change makes pointless, because that is
where the old wording costs most now. Make the whole change in each module you touch, and list in your report the
modules you left, so the lead can start a planner for them.

## The user dropped a module

Delete the module's whole folder, its record file included, and its row in the module table, and change the
`depends_on` of any milestone in another module that waits on it. The script merges that only while none of the
module's milestones has started, because once one has, its record is the only account of that work. When one has,
keep the folder and record, remove from its done-when file only the milestones that haven't started, and say in your
report what started work stays, so the lead can ask the user.

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
