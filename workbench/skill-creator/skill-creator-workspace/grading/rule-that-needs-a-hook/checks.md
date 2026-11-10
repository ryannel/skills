# Checks for rule-that-needs-a-hook

The request, in the person's words:

> 
> make me a skill that makes sure claude never commits directly to main and always runs prettier before committing. it keeps forgetting even though both are in CLAUDE.md in caps. the whole team should get it, we're all on claude code

Checks:

1. The reply says that text in a skill or CLAUDE.md cannot guarantee a rule that must hold every time, and that such a rule belongs in a hook, a permission rule or a git hook.
2. The output includes a concrete mechanism that blocks a commit made on main: a hook script, hook configuration, a permission rule or a git hook, as a file or exact configuration.
3. The output includes a concrete mechanism that runs prettier before a commit.
4. The delivered solution is not only a skill or instruction text with stronger wording.
5. The mechanism is delivered in a form the rest of the team receives, such as project settings or files committed to the repository, or the reply says exactly what each teammate must do.
6. Any skill or instruction text in the output has no word in capitals for emphasis.
7. The reply says whether the mechanism was run or is untested.
