Agent: artifact-author (fix cycle, one skill)
Skill: packages/github-actions-cicd/.apm/skills/publishing-container-images-github-actions/
Findings to fix:
HIGH F-017: ci-image caller grants contents: read but the GHCR job needs packages: write -> either grant packages: write in ci-image (push: false still logs in? decide from the README: if no login when push false, split a PR-only build job without packages: write) - make the canonical PR example start successfully.
MEDIUM F-021: ECR/OCIR jobs must not bind environment or id-token on PR builds (push: false) - gate them with `if: inputs.push` or a separate PR job; read ECR role/OCIR secrets inside the called job from its environment, not in the caller (rule 17/18).
MEDIUM (contract, F-019/F-023): add an optional `artifact-name` input so callers (Next.js standalone, Java) can hand a built artifact to _image-publish; keep outputs digest and image-ref.
LOW (cheap): timeouts on jobs, concurrency on ci-image; Contents list in unverified-and-risks.md; Verification Loop grep pattern `\|` inside backticks -> correct -E syntax; cite the right source for the ECR long-lived-keys Never row.
Approval line: The user approved 9 skills, 2 agents, 4 rules and command /building-cicd-pipelines on 2026-10-30 (G1, workspace/github-actions-cicd/execution-1/state/gates/G1.md) and the fan-out at G2 (state/gates/G2.md); this is P6 fix cycle round 1. This is a relay, not a new approval.
Hard constraints:
- Do NOT spawn any agent; do NOT enter plan mode.
- Change only what a listed finding names; keep tags/registers consistent (update unverified-and-risks.md counts and mapping when you add/remove tags); keep every blueprint <= 160 lines; SKILL.md frontmatter only name + description.
- Do not touch _family_* files, shared files, other skills or other packages. If a finding contradicts a family fact, stop and report it.
- Apply workspace/github-actions-cicd/_family_facts.md (F1-F42) and _family_rules.md (1-18; NEW 17 canonical names, 18 timeouts/concurrency/id-token/env secrets) as given.
- Never make shipped text READ workspace/; never invent SHAs or versions.
Evidence: the round-1 reports in workspace/github-actions-cicd/execution-1/rounds/round-1/ (validate__<target>.md, test__<target>.md, audit__package.md) give file:line and fix hints.
Done when: .claude/skills/building-agent-packages/scripts/verify_skill.py <skill-dir> would exit 0 (the orchestrator runs it) and you return a list "F-id -> what changed (file)".
