Agent: artifact-author (fix cycle, one skill)
Skill: packages/github-actions-cicd/.apm/skills/federating-github-actions-oci/
Findings to fix:
HIGH F-016: _oci-deploy.yml must not declare OCI_CLI_* as required workflow_call secrets; its job declares environment: and reads the environment secrets directly (rule 18). Keep the Free variant note (repository secrets with warning) consistent.
MEDIUM F-027: untagged immutable environment `sub` (never-do-patterns.md:72, path-a-token-exchange.md:43, plan-variants.md:37) -> tag (unverified) or use only the F26 ref form.
MEDIUM F-019/F-020: environment names <env>/<env>-pr (rule 17: rename oci-pr/oci-dev/oci-prod usage to the canonical pattern or explain the mapping), timeouts on jobs.
LOW (cheap): setup-terraform with terraform_wrapper: false in the caller example; move exchange.sh into a clearly named file block the composite references (or inline the script in the composite); avoid raw F-numbers in shipped text.
Approval line: The user approved 9 skills, 2 agents, 4 rules and command /building-cicd-pipelines on 2026-10-30 (G1, workspace/github-actions-cicd/execution-1/state/gates/G1.md) and the fan-out at G2 (state/gates/G2.md); this is P6 fix cycle round 1. This is a relay, not a new approval.
Hard constraints:
- Do NOT spawn any agent; do NOT enter plan mode.
- Change only what a listed finding names; keep tags/registers consistent (update unverified-and-risks.md counts and mapping when you add/remove tags); keep every blueprint <= 160 lines; SKILL.md frontmatter only name + description.
- Do not touch _family_* files, shared files, other skills or other packages. If a finding contradicts a family fact, stop and report it.
- Apply workspace/github-actions-cicd/_family_facts.md (F1-F42) and _family_rules.md (1-18; NEW 17 canonical names, 18 timeouts/concurrency/id-token/env secrets) as given.
- Never make shipped text READ workspace/; never invent SHAs or versions.
Evidence: the round-1 reports in workspace/github-actions-cicd/execution-1/rounds/round-1/ (validate__<target>.md, test__<target>.md, audit__package.md) give file:line and fix hints.
Done when: .claude/skills/building-agent-packages/scripts/verify_skill.py <skill-dir> would exit 0 (the orchestrator runs it) and you return a list "F-id -> what changed (file)".
