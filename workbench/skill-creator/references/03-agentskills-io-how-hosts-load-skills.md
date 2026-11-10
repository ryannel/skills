# agentskills.io: how to add skills support to your agent

- URL: https://agentskills.io/client-implementation/adding-skills-support
- Read in Chrome on 2026-11-10. Paraphrased.
- This page is written for people who build an agent host. It is useful to a skill author because it says what a
  host does with a skill, including the parts that differ from host to host.

## What every host does

| Stage | What is loaded | When | Cost |
|---|---|---|---|
| 1. Catalogue | Name and description of each skill | At the start of a session | About 50 to 100 tokens a skill |
| 2. Instructions | The body of `SKILL.md` | When the skill is activated | Under 5,000 tokens recommended |
| 3. Resources | Scripts, references, assets | When the instructions refer to them | Varies |

## What differs between hosts, and what an author should assume

- **Where skills are found.** Most hosts read a folder of their own (`.claude/skills/`, for example) and the
  shared `.agents/skills/`, in the project and in the user's home folder. When a project skill and a user skill
  have the same name, the project one wins.
- **Malformed YAML.** A common mistake is an unquoted value with a colon in it, such as
  `description: Use this skill when: the user asks about PDFs`. Some hosts repair it and some drop the skill. A
  skill with no description is skipped. So an author should quote any description that contains a colon.
- **Who decides to load a skill.** In most hosts the model decides, from the catalogue. Hosts do not match
  keywords. A user can also name a skill directly (`/skill-name` or `$skill-name`).
- **What the model receives.** Either the whole file including frontmatter (when the model reads the file itself)
  or the body only (most hosts with a dedicated skill tool). So an author should not put an instruction in the
  frontmatter and expect the model to see it once the skill is loaded, and should not rely on the body repeating
  the description.
- **Listing the folder.** Some hosts list the skill's other files next to the instructions when it loads. They
  don't read them. An author can't rely on the listing, so `SKILL.md` still has to name each file and say when to
  read it.
- **Relative paths.** The host tells the model the skill's folder, and paths in the skill are relative to it.
- **Compaction.** The page tells hosts to exempt loaded skills from summarising, because a skill lost
  mid-conversation "silently degrades" the work with no visible error. Hosts differ in whether and how much they
  keep (Claude Code keeps the first 5,000 tokens of each).
- **Loading twice.** Hosts may skip loading a skill that is already in the conversation.
- **Subagents.** Some hosts can run a skill in a separate subagent session, which gets the skill as its
  instructions and returns a summary.
- **Trust.** Skills in a project come from the repository, which may be untrusted. Hosts may load them only for
  a folder the user has marked as trusted.
