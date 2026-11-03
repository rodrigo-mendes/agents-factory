# Package brief — github-actions-cicd

Source: user request 2026-10-30 ("quer automatizar o ci cd de projetos com infra com terraform, java e
react+nextjs com github actions") and the approved plan
(`~/.claude/plans/quer-automatizar-o-ci-keen-lollipop.md`). Scope answers were collected with the
question tool before state existed; they are re-confirmed and recorded verbatim at G1.

```yaml
slug: github-actions-cicd
language: en                        # artifacts in English (factory convention); user talks in pt-BR
frameworks:                         # versions resolved in P1 from official pages
  - GitHub Actions (GitHub.com, dated, not version-locked)
  - Terraform CLI <current stable>
  - Java LTS <current> with Maven <current> and Gradle <current>
  - Node.js LTS <current> with Next.js <current major>
needs:
  - CI on pull request and CD on merge for Terraform infra deploying to AWS and OCI
  - keyless cloud login from Actions (AWS OIDC; OCI federation if officially supported, else API key)
  - Java builds (Maven and Gradle) producing container images and Lambda zips, or CI only
  - Next.js builds deployed to Vercel, AWS S3+CloudFront (static export), a container, or CI only
  - pipelines composed of replaceable building blocks (reusable workflows + composite actions)
  - blast-radius control: env promotion of one artifact, approvals, progressive delivery, rollback
  - supply-chain security: dependency review, CodeQL, IaC and image scans, SBOM, Dependabot
legacy_source: none
deliverables: [skills, agent, rules, readme]   # 2 agents + 1 command
agent_kind: executor                # plus a second, advisory (read-only) reviewer agent
out_of_scope:
  - GitHub Enterprise Server
  - self-hosted runner fleets
  - Azure, Jenkins, Azure DevOps
  - database migrations
  - running pipelines or terraform apply for real
research_worker: researching-technical-frameworks   # default depth (user: "usar o padrao")
rounds: 3
max_rounds: 5
token_budget: 9500000              # raised after budget exceeded (DEC-020); was 7000000 (DEC-009)
```

Planned units (names final at G1):
1. composing-github-actions-pipelines
2. automating-terraform-github-actions (pilot)
3. federating-github-actions-aws-oidc
4. federating-github-actions-oci
5. building-java-github-actions
6. publishing-container-images-github-actions
7. building-nextjs-github-actions
8. limiting-blast-radius-github-actions-deploys
9. securing-supply-chain-github-actions

Agents: cicd-pipeline-engineer (executor), cicd-pipeline-reviewer (advisory).
Rules: github-workflows-security, github-workflows-pr-ci, github-workflows-merge-cd, github-workflows-building-blocks.
Command: building-cicd-pipelines (context: fork -> cicd-pipeline-engineer).
