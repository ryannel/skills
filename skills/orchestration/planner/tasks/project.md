# Planning a new project

A new project has a brief and settings but no plan yet. Your first plan is the module list, then a plan for each
module on the thin slice described under "The order", and for the acceptance module when there is one, each written
as [planning a module](module.md) says. The other modules get a row in the module list, and a planner plans each when
its turn comes.

## The module list

The module list opens with the module table, every module in build order, under the exact
header [the module table](../references/done-when.md#the-module-table) gives, because the script reads it. A project
small enough for one module still gets the table, with one row. After the table, say what each module owns, and list
each interface, meaning what one module provides to the others. Then list the brief's "Later", each piece with the
module that will own it, so the user can see it is waiting rather than forgotten.

Draw the lines between modules around state, so each kind of state has one module in charge of it.

## The order

Plan the first milestones as a thin slice through the whole product: the smallest thing an end user could do from
start to finish, however crude, such as importing one statement and printing one balance. Each module on that path
makes its part of the slice its first milestone.

In an empty repository, the first milestone of one module lays down what every other builds in, such as the
manifest, the framework and the database setup, and the other slice milestones list it in `depends_on`. After that,
plan enough work that can run side by side for the number of builders your task names, with interfaces and stubs so
modules don't wait on each other. When the look is the product, the user's choice of look comes before any slice
milestone that carries it. Options that are images or sounds made outside the product needn't depend on the
milestone that lays down the project, so they can be built, and chosen from, while it is.

## The acceptance module

Each module is judged on its own, so every part can pass and the whole can still miss what the user asked for. The
acceptance items guard against that. Turn the brief's "What finishes this goal" into items about what an end user
can do with the whole product, proved on a real target, meaning a device or platform the product runs on. Write them
now, though they run last, because they define done for the whole build.

They usually go in a last module, `ACCEPTANCE`, the last row of the table, with one milestone whose `depends_on`
names the milestone in each module that completes it. When the user or your task limits the number of modules, such
as "plan it as one module", the limit wins, because it is the user's choice and the acceptance module is only the
plan's habit: put the acceptance items in the last milestone of the last module instead.

## The settings

The lead writes the settings, `ORCHESTRATE.md`, from the brief before planning starts. Once you've chosen the stack,
write their `Test command:` and `Setup command:` lines. Also fill in the "Starting from a clean clone" section and
the Run and Capture columns of the Targets table, because several builders and reviewers run copies of the product
at once, and each needs its own ports and database. The script's `settings --template` explains each line and what
it needs. The settings hold settings, not progress, so write no status there.
