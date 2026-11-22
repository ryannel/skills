# Unblocking a builder

A builder has stopped on something the plan should answer, and the lead has sent you the reasons. Settle it so the
builder can go on, and change only what the block reaches.

## Something another module owns is missing

The builder ended with `BLOCKED needs_dependency`. Plan the missing part in the module the module list says owns
it, because otherwise two modules would own the same thing. If that is another module, add the milestone there that
delivers it, or move one earlier, and add it to the blocked milestone's `depends_on`. If the module list had the
owner wrong, fix the list and the interface first.

When your change reaches the blocked milestone itself, such as its `depends_on` or an item, the script lifts the
block. When the plan already answers the block, change no file and end with `KEEP <MODULE> <milestone>: builder:
<where the plan answers it>`. The script lifts the block, and the lead starts the builder again with your reasons.

## The builder asked a question about the plan

The builder ended with `NEEDS_CONTEXT:` and a question the plan should answer, and the lead sent it to you. Answer it
in the plan files, where the next builder will read it, such as in the design or the note under the milestone. If
the plan already answers it, change no file and end with `KEEP <MODULE> <milestone>: builder: <where the plan
answers it>`. If only the user can answer it, end with `NEEDS_CONTEXT:` and the question.

## An item can't be met

The script stops a builder that isn't getting anywhere, and the builder may say an item can't be met as written. If
an item really can't, change it and end with `PLANNED`. If every item can be met, change no file and end with
`KEEP <MODULE> <milestone>: builder: <how the items can be met>`, and the lead starts a new builder session with
your reasons.
