# Checks for modernise-old-skill

The request, in the person's words:

> 
> this skill was written about a year ago for sonnet 4. we're on fable 5.2 now and a couple of people use astra in codex, and with it loaded the agent keeps stopping to ask permission for everything + runs the whole 25 min test suite on tiny changes. can you update it? it's in db-migrations/

Checks:

1. The revised skill's name is still db-migrations, and scripts/check_skill.py reports no problems for it.
2. The revised skill keeps the rule that a statement taking a lock runs with lock_timeout set to 5s, with its reason.
3. The revised skill keeps the fact that orders and customers use soft deletes through deleted_at.
4. The revised skill keeps make migrate-check and what it does, including that staging is refreshed nightly.
5. The revised skill states the production rule once: production migrations are run by the DBA on call after approval. It does not also keep a blanket 'ask before any change' or 'confirm before every command' line.
6. The revised skill says that editing files in db/migrations/ and running make migrate-check need no approval.
7. The line requiring the full test suite after any change is removed or replaced by what check a migration needs.
8. The never-retry caution is removed, or flagged to the person as probably out of date. It is not kept as an unconditional rule.
9. The revised skill has no word in capitals for emphasis.
10. The revised body has no section about when to use the skill.
11. The description no longer claims any database work. It says when to use the skill in terms of adding, changing or reviewing a migration.
12. The lines telling the agent to use subagents whenever possible, to think step by step, and to double-check are gone.
13. The reply to the person lists what was removed or changed and why.
14. An untouched copy of the old version is kept, or the reply says where the old version can be found.
