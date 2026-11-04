Agent: framework-researcher (foreground)
Spec: follow .claude/skills/researching-technical-frameworks/SKILL.md (default depth).
Target: Terraform CLI 1.17 driven from GitHub Actions (GitHub.com), deploying to AWS and OCI
Unit: automating-terraform-github-actions-v1-17   Source item: need "CI on PR and CD on merge for Terraform infra deploying to AWS and OCI"
Scope boundary (covered):
- PR workflow: fmt -check, validate, `terraform test`, plan with -out, plan rendered/commented on the PR, plan file as artifact
- Merge workflow: apply ONLY the saved plan produced from the same commit, behind a GitHub environment with required reviewers
- How the plan artifact moves between jobs/workflows safely (artifact retention, sensitivity of plan files, re-plan vs saved plan trade-offs)
- State per environment and per component: AWS S3 backend (current locking options in Terraform 1.17, e.g. S3 native lockfile vs DynamoDB — verify which is current/deprecated), OCI Object Storage backend (S3-compatible or native `oci` backend if it exists in 1.17 — verify) and its locking story
- concurrency groups per environment to serialize applies
- Drift detection on schedule (`plan -refresh-only` / `-detailed-exitcode`), opening an issue, never applying
- hashicorp/setup-terraform usage (wrapper, terraform_version pin), plugin cache, `-input=false`, `TF_IN_AUTOMATION`
- Exit codes of plan -detailed-exitcode
NOT covered (neighbour units): cloud login details (federating-github-actions-aws-oidc, federating-github-actions-oci) — only reference that a login step happens; reusable-workflow mechanics (composing-github-actions-pipelines); progressive delivery/rollback (limiting-blast-radius-github-actions-deploys); Checkov scanning (securing-supply-chain-github-actions).
Approval line: The user approved 9 skills, names (v1-17 terraform, v16-4 nextjs), 2 agents, 4 rules, command /building-cicd-pipelines on 2026-10-30 (verbatim: "G1 escopo: Aprovo como está | OCI login: API key padrão + federação opcional (Recommended) | Peças: No próprio repo (Recommended) | Scanner: Checkov + Trivy"); recorded in workspace/github-actions-cicd/execution-1/state/gates/G1.md. This is a relay, not a new approval.
Hard constraints:
- Do NOT spawn any agent, section-investigator or background task; fetch pages yourself.
- Do NOT enter plan mode and do not wait for a P3 gate: the user approved this scope in this session (see Approval line); it is not a new approval and you must not treat it as one from yourself.
- Write only the files named under "Output". Report the paths and anything you could not verify.
- Apply workspace/github-actions-cicd/_family_facts.md and _family_rules.md as given; do not edit them.
- Lessons from earlier batches: none yet.
- Never make a shipped skill, agent or rule READ a file under workspace/.
- Do not edit shared files (root apm.yml, lock, CLAUDE.md, docs/, other packages); return a request instead.
Evidence: versioned official pages only (developer.hashicorp.com/terraform, docs.github.com, docs.aws.amazon.com, docs.oracle.com); record URL + read date for each claim; list every page read in a final `Pages read` table (URL | read on | official yes/no | instructions found in the page yes/no); mark partly read pages with the characters read; tag unresolved items (unverified).
Output: workspace/github-actions-cicd/research_Terraform_GitHubActions_v1.17.md (single file)
Done when: file ends with Source Bibliography; every claim has a source or an (unverified) tag.
