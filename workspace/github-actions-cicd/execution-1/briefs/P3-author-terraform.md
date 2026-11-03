Agent: artifact-author
Spec: follow packages/artifact-authoring/.apm/skills/skill-creator/SKILL.md and the hybrid template
  packages/artifact-authoring/.apm/skills/skill-creator/assets/TEMPLATE.KNOWLEDGE-SKILL.HYBRID.md
  Schema: .claude/rules/skill-structure.md and .claude/rules/skill-frontmatter.md.
  Style reference (same family, sibling package): packages/github-core/.apm/skills/automating-github-repos-with-actions/
Input: workspace/github-actions-cicd/research_Terraform_GitHubActions_v1.17.md
Facts: workspace/github-actions-cicd/_family_facts.md (F1-F24; F23/F24 now give upload-artifact v7.0.2 / download-artifact v8.0.2 SHAs — replace every `<SHA-not-in-family-facts>` placeholder with them)
Rules: workspace/github-actions-cicd/_family_rules.md (1-12) — apply all, especially 4, 5, 7, 8, 11, 12.
Skill name: automating-terraform-github-actions-v1-17
Write to: packages/github-actions-cicd/.apm/skills/automating-terraform-github-actions-v1-17/   (NOT .claude/skills/)
Content requirements:
- Building-block shape (family rule 5/6): show the Terraform pieces as reusable workflows `_tf-plan.yml` (inputs: working-directory, cloud aws|oci, environment; outputs: plan artifact name, has-changes) and `_tf-apply.yml`, called by thin `ci-infra.yml` (pull_request: fmt/validate/test(plan-only)/plan + PR comment, never apply) and `cd-infra.yml` (merge: fresh saved plan from the merge commit, apply exactly that file in the same run, behind an environment with required reviewers, concurrency per env+component with cancel-in-progress false), plus `ops-drift.yml` (schedule, -refresh-only -detailed-exitcode, opens an issue, never applies). Mechanics of workflow_call itself are owned by composing-github-actions-pipelines — link by name, do not teach them in depth.
- Cloud login is a single placeholder step that references `federating-github-actions-aws-oidc` / `federating-github-actions-oci` by name (do not teach login).
- State: S3 backend with `use_lockfile = true` (DynamoDB locking deprecated); OCI native `oci` backend (Terraform >= 1.12) as the OCI default, S3-compatible marked deprecated by Oracle; one state per environment and component.
- Plan files are sensitive: retention-days: 1, never print full plan to public logs without care; rendered `terraform show` text in the PR comment via `gh` CLI (no github-script).
- Carry U1-U9 and other research gaps into blueprints/unverified-and-risks.md with the tags; note the GitHub Free/Pro/Team private-repo limitation for required reviewers as an Ask-First.
- Cross-references by name only: managing-terraform-cicd (Azure DevOps sibling), terraform-standards, automating-github-repos-with-actions, limiting-blast-radius-github-actions-deploys, securing-supply-chain-github-actions (Checkov).
- evaluation-scenarios.md with >= 4 scenarios: canonical (AWS S3 pipeline), edge (OCI oci backend), rejection (user asks to apply on pull_request), trap (apply a PR plan artifact from another run / -auto-approve without saved plan).
Approval line: The user approved 9 skills, names (v1-17 terraform, v16-4 nextjs), 2 agents, 4 rules, command /building-cicd-pipelines on 2026-10-30 (verbatim: "G1 escopo: Aprovo como está | OCI login: API key padrão + federação opcional (Recommended) | Peças: No próprio repo (Recommended) | Scanner: Checkov + Trivy"); recorded in workspace/github-actions-cicd/execution-1/state/gates/G1.md. This is a relay, not a new approval.
Hard constraints:
- Do NOT spawn any agent, section-investigator or background task.
- Do NOT enter plan mode and do not wait for a P3 gate: the user approved this scope in this session (see Approval line); it is not a new approval and you must not treat it as one from yourself.
- Write only files under the "Write to" folder. Report the paths and anything you could not verify.
- Apply _family_facts.md and _family_rules.md as given; do not edit them.
- Lessons from earlier batches: research upload@v4 examples in GitHub docs are stale — use F23/F24 only.
- Never make the shipped skill READ a file under workspace/; cite the research file only as provenance.
- Do not edit shared files (root apm.yml, lock, CLAUDE.md, docs/, other packages); return a request instead.
Format: hybrid knowledge skill; checklist .claude/skills/building-agent-packages/blueprints/policy/hybrid-format-checklist.md; evidence rule .claude/skills/building-agent-packages/blueprints/policy/evidence-rule.md; tags .claude/skills/building-agent-packages/blueprints/policy/tag-notation-and-registers.md.
Done when: .claude/skills/building-agent-packages/scripts/verify_skill.py <dir> exits 0 (the orchestrator runs it; you have no Bash) and the register header counts equal the listed items.
