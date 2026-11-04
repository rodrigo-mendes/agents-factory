Agent: quality-validator
Kind: VALIDATE (P3 pilot round, single skill)
Spec: follow .claude/skills/skill-best-practices-validator/SKILL.md
Target: packages/github-actions-cicd/.apm/skills/automating-terraform-github-actions-v1-17/ (SKILL.md + all blueprints)
Also check against: workspace/github-actions-cicd/_family_facts.md (every version/SHA must match), workspace/github-actions-cicd/_family_rules.md (rules 1-12), and the research provenance workspace/github-actions-cicd/research_Terraform_GitHubActions_v1.17.md (claims in Always/Never must trace to it).
Rubric: 100 - 6/HIGH - 2.5/MEDIUM - 0.5/LOW.
Known, do not report: `uses: ./<repo-workflows-dir>/...` placeholder is a deliberate workaround for a factory verifier rule (tracked as D-001).
Approval line: The user approved 9 skills, names (v1-17 terraform, v16-4 nextjs), 2 agents, 4 rules, command /building-cicd-pipelines on 2026-10-30 (verbatim: "G1 escopo: Aprovo como está | OCI login: API key padrão + federação opcional (Recommended) | Peças: No próprio repo (Recommended) | Scanner: Checkov + Trivy"); recorded in workspace/github-actions-cicd/execution-1/state/gates/G1.md. This is a relay, not a new approval.
Hard constraints:
- Do NOT spawn any agent, section-investigator or background task.
- Do NOT enter plan mode.
- Read-only except the one report file below.
- Do not edit the skill, family files or shared files.
Output: return the report INLINE (score; findings with severity HIGH/MEDIUM/LOW, file:line, evidence quote, fix hint) and also write workspace/github-actions-cicd/execution-1/rounds/round-0/validate__automating-terraform-github-actions-v1-17.md
