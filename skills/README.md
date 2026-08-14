# Skill catalogue

Skills are grouped by **domain**, one directory per domain:

```
skills/<domain>/<skill-name>/SKILL.md
```

The `skills` CLI walks this tree up to three levels deep, so a domain directory is a
supported layout rather than a workaround. Installing is by skill name and does not
depend on which domain a skill lives in:

```bash
npx skills add ryannel/skills --skill <skill-name>
```

## Domains

| Domain | What belongs in it |
|---|---|
| [`generative-media/`](generative-media/) | Image and video models, and the craft spanning them — model setup, prompting, LoRA training, production pipelines, GPU deployment |

## Adding a new domain

1. Create `skills/<domain>/` and put the skill folders inside it.
2. Add a plugin entry to [`../.claude-plugin/marketplace.json`](../.claude-plugin/marketplace.json)
   naming that domain's skills. The plugin name becomes the heading users see when they
   browse this repo with `npx skills add ryannel/skills --list`, so name it for the
   domain, not the repo.
3. Register each skill in the freshness protocol so it does not silently rot.

**Keep cross-skill links relative and within a domain.** Every link in this repo is
`../sibling/` or `../../sibling/reference.md`, which is what made the domains
introducible without rewriting anything. A link that reaches across domains is a sign
the two skills belong in the same one.

**A domain earns its own authoring spec.** `generative-media` has one — the shared
research protocol, section anatomy and provenance discipline that makes its skills
read as a suite. A new domain should get its own rather than borrowing that one, which
is shaped around model ecosystems specifically.
