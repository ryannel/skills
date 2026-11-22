# Planning a new project

A new project has a brief and settings but no plan yet. Your first plan is the module list, then a plan for each
module on the thin slice described under "The order", and for the acceptance module, each written as
[planning a module](module.md) says. The other modules get a row in the module list, and a planner plans each when
its turn comes.

## The module list

`ARCHITECTURE.md` in the plans folder opens with a table of every module in build order. The script reads the
table, so keep this header:

```markdown
| # | Module | What it's for | Needs |
|---|---|---|---|
| 1 | AUTH | People sign in, and stay signed in across devices | |
```

`What it's for` is one plain sentence for the user. A project small enough for one module still gets the table,
with one row. After the table, say what each module owns, and list each interface, meaning what one module provides
to the others. Then list the brief's "Later", each piece with the module that will own it, so the user can see it is
waiting rather than forgotten.

Draw the lines between modules around state, so each kind of state has one module in charge of it, because most bugs
between modules come from two of them changing the same thing.

## The order

Plan the first milestones as a thin slice through the whole product: the smallest thing an end user could do from
start to finish, however crude, such as importing one statement and printing one balance. Each module on that path
makes its part of the slice its first milestone. The slice shows that the modules fit together before any of them is
built out, and gives the user something to try early. After it, build first what is riskiest and what most other work
depends on, because that is what is most likely to force everything else to change.

In an empty repository, the first milestone of one module lays down what every other builds in, such as the
manifest, the framework and the database setup, and the other slice milestones list it in `depends_on`, because
builders who each create it at once produce merges that conflict. After that, plan enough work that can run side by
side for the number of builders your task names, with interfaces and stubs so modules don't wait on each other.
When the look is the product, the user's choice of look comes before any slice milestone that carries it. Options
that are images or sounds made outside the product needn't depend on the milestone that lays down the project, so
they can be built, and chosen from, while it is.

## The acceptance module

Each module is judged on its own, so every part can pass and the whole can still miss what the user asked for. The
acceptance module guards against that. Turn the brief's "What finishes this goal" into items about what an end user
can do with the whole product, proved on a real target, meaning a device or platform the product runs on. Put them
in a last module, `ACCEPTANCE`, the last row of the table, with one milestone whose `depends_on` names the milestone
in each module that completes it. Write its items now, though it runs last, because they define done for the whole
build.

## The settings

The lead writes the settings, `ORCHESTRATE.md`, from the brief before planning starts. Add two lines to them: `Test
command:`, the command that must pass before every merge, and `Setup command:`, what a fresh copy of the repository
needs before its tests run, such as `npm ci`, or `none`. Once you've chosen the stack, also fill in the settings'
"Starting from a clean clone" section and the Run and Capture columns of the Targets table, because several builders
and reviewers run copies of the product at once, and each needs its own ports and database. The script tests every
merge in a clean copy where nothing is installed. The test command has to pass before any test exists, so on a new
repository use one that passes on an empty suite. `pytest`, for one, fails when it finds no tests, and `pytest || [ $?
-eq 5 ]` lets that case pass.
