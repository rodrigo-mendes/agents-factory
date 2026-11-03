Agent: artifact-author (fix cycle, one skill)
Skill: packages/github-actions-cicd/.apm/skills/building-java-github-actions/
Findings to fix:
MEDIUM F-020: timeout-minutes on every job (_java-build, cd-dependency-graph), concurrency on callers (rule 18).
MEDIUM F-028: cite the setup-java README for the `cache-read-only` input or remove it (gradle/actions setup-gradle has its own cache-read-only - keep it only where the source documents it); artifact names include a slug of working-directory to avoid collisions.
LOW (cheap): remove raw F-numbers/"family rule N" from 8 blueprints (state the fact itself); one claim per bullet SKILL.md:56; `target/*.jar` glob must exclude original-*.jar; gradle-build.md:73 contents: write at workflow level -> job level only where needed; PR concurrency on ci-orders.
Approval line: The user approved 9 skills, 2 agents, 4 rules and command /building-cicd-pipelines on 2026-10-30 (G1, workspace/github-actions-cicd/execution-1/state/gates/G1.md) and the fan-out at G2 (state/gates/G2.md); this is P6 fix cycle round 1. This is a relay, not a new approval.
Hard constraints:
- Do NOT spawn any agent; do NOT enter plan mode.
- Change only what a listed finding names; keep tags/registers consistent (update unverified-and-risks.md counts and mapping when you add/remove tags); keep every blueprint <= 160 lines; SKILL.md frontmatter only name + description.
- Do not touch _family_* files, shared files, other skills or other packages. If a finding contradicts a family fact, stop and report it.
- Apply workspace/github-actions-cicd/_family_facts.md (F1-F42) and _family_rules.md (1-18; NEW 17 canonical names, 18 timeouts/concurrency/id-token/env secrets) as given.
- Never make shipped text READ workspace/; never invent SHAs or versions.
Evidence: the round-1 reports in workspace/github-actions-cicd/execution-1/rounds/round-1/ (validate__<target>.md, test__<target>.md, audit__package.md) give file:line and fix hints.
Done when: .claude/skills/building-agent-packages/scripts/verify_skill.py <skill-dir> would exit 0 (the orchestrator runs it) and you return a list "F-id -> what changed (file)".
