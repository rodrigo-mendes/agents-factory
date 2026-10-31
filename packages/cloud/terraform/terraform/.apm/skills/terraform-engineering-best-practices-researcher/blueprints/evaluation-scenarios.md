# Evaluation Scenarios — terraform-engineering-best-practices-researcher

Used to verify that the skill activates correctly, enforces version absolutism for Terraform
engineering practices, produces properly structured best-practices output calibrated to team size
and project scale, and rejects misuse requests (provisioning asks, unversioned queries,
scale-insensitive advice).

---

## Scenario 1: Standard research request — pinned version, explicit team/scale context (canonical path)

```json
{
  "skills": ["terraform-engineering-best-practices-researcher"],
  "query": "Research Terraform 1.9 engineering best practices for a medium team (5-15 engineers) on AWS at multi-app scale with dev/staging/prod environments. Tooling: GitHub Actions + Atlantis. No formal compliance requirements.",
  "expected_behavior": [
    "Sets TERRAFORM_VERSION=1.9, CLOUD_PROVIDER=AWS, TEAM_SIZE=medium (5-15), PROJECT_SCALE=multi-app, ENVIRONMENT_COUNT=dev/staging/prod, TOOLING_PREFERENCES=GitHub Actions + Atlantis",
    "Researches all 9 scope areas: project layout, module design, environment management, state at scale, CI/CD pipelines, testing, code quality, advanced patterns, governance",
    "Calibrates recommendations to medium team scale — avoids solo-dev shortcuts AND avoids enterprise over-engineering",
    "Always Do section includes: pin Terraform + provider versions, remote state with S3 locking, validate inputs, fmt + validate in CI, tag all resources, prevent_destroy for critical resources",
    "Ask First section covers: monorepo vs polyrepo, workspaces vs directory-per-env, native terraform test vs Terratest",
    "Never Do section includes ❌ wrong pattern and ✅ correct alternative for each anti-pattern — not prose-only prohibitions",
    "CI/CD examples include Atlantis-specific config (atlantis.yaml workflow blocks) since TOOLING_PREFERENCES specifies Atlantis",
    "Sources cite HashiCorp official docs dated <= 12 months; books cited with edition and chapter"
  ],
  "success_criteria": {
    "must_pass": [
      "All 9 research scope areas addressed",
      "Terraform version 1.9 features (e.g., provider-defined functions if applicable) called out explicitly",
      "Every Never Do entry has ❌ wrong / ✅ correct example (HCL or CI config, not prose only)",
      "Recommendations explicitly labelled as calibrated for TEAM_SIZE=medium, PROJECT_SCALE=multi-app",
      "Atlantis-specific CI/CD patterns present (atlantis.yaml, plan/apply workflow)",
      "Completion Checklist present in output"
    ],
    "must_not": [
      "Mix Terraform 1.7 deprecated behaviors with 1.9 patterns",
      "Give solo-dev advice (e.g., local state OK) to a medium team",
      "Give enterprise-only advice (e.g., Terraform Cloud Business tier) without flagging it as out-of-scope for this context",
      "Produce Never Do prohibitions without correct alternatives"
    ]
  }
}
```

---

## Scenario 2: Edge case — compliance requirement changes the recommended patterns

```json
{
  "skills": ["terraform-engineering-best-practices-researcher"],
  "query": "Research Terraform 1.9 best practices for a large team on AWS at enterprise scale. Compliance: SOC2 + PCI-DSS.",
  "expected_behavior": [
    "Applies compliance overlay: SOC2 and PCI-DSS requirements elevate certain patterns from Ask First to Always Do (e.g., audit logging mandatory, change approval workflow required)",
    "Documents compliance-specific Always Do patterns: immutable infrastructure for cardholder data environments, mandatory plan approval before apply, audit trail for all state changes",
    "Flags that compliance-specific implementations (e.g., exact Sentinel policies for PCI-DSS) are Low Confidence — must involve the user's security/compliance team",
    "Distinguishes between what Terraform itself enforces vs what must be enforced by CI/CD workflow or OPA/Sentinel policy",
    "Agent Operation Notes section marks compliance-specific patterns as Low Confidence",
    "Research Gaps populated for any PCI-DSS or SOC2 specifics not resolvable from public HashiCorp documentation"
  ],
  "success_criteria": {
    "must_pass": [
      "Compliance requirements visibly change the Always Do list compared to a non-compliance scenario",
      "At least one PCI-DSS and one SOC2 specific requirement explicitly called out",
      "Compliance patterns marked as Low Confidence with note to involve security team",
      "Research Gaps present for compliance-specific implementation details"
    ],
    "must_not": [
      "Present SOC2/PCI-DSS implementation as fully resolvable from public docs alone",
      "Apply standard medium-team patterns without compliance overlay when COMPLIANCE_REQUIREMENTS specifies SOC2 + PCI-DSS",
      "Mark compliance-specific patterns as High Confidence"
    ]
  }
}
```

---

## Scenario 3: Misuse / out-of-scope — asked to generate a project scaffold, not research practices

```json
{
  "skills": ["terraform-engineering-best-practices-researcher"],
  "query": "Create a complete Terraform project structure for our AWS multi-app environment with modules, CI/CD config, and atlantis.yaml — ready to use.",
  "expected_behavior": [
    "Recognizes this is a scaffolding/generation request, not a best-practices research request — this skill produces a knowledge base document, not a deployable project",
    "Explicitly declines generating a ready-to-use project scaffold",
    "Explains correct routing: scaffolding tasks belong to a code-generating agent consuming the knowledge base produced by this skill",
    "Offers to instead research Terraform 1.x engineering best practices for the given context, producing the structured knowledge base that a scaffolding agent can consume",
    "Does NOT produce directory trees with file contents intended for direct copy-paste deployment",
    "Does NOT produce atlantis.yaml, main.tf, or GitHub Actions workflow files as deliverables"
  ],
  "success_criteria": {
    "must_pass": [
      "Skill declines the scaffolding request",
      "Skill explains the research-vs-generation boundary",
      "Skill offers a corrected research scope"
    ],
    "must_not": [
      "Generate a deployable project scaffold as output",
      "Produce ready-to-use CI/CD pipeline YAML files as primary deliverable",
      "Silently shift from research mode to code generation mode"
    ]
  }
}
```

---

## Scenario 4: Anti-pattern trap — requesting patterns known to cause state divergence

```json
{
  "skills": ["terraform-engineering-best-practices-researcher"],
  "query": "We use a Git branch per environment strategy — one branch for dev, one for staging, one for prod. Each branch has its own state file checked into the repo. How should we structure our Terraform best practices around this setup?",
  "expected_behavior": [
    "Flags both anti-patterns before advising on best practices: (1) branch-per-environment causes state divergence risk, (2) committing .tfstate to version control exposes secrets and breaks concurrent applies",
    "For branch-per-environment: ❌ shows a git log where main and prod diverged 47 commits → describes the blast radius (drift, untestable plans); ✅ shows directory-per-environment or workspace approach with a single trunk branch",
    "For .tfstate in repo: ❌ shows git history containing plaintext DB passwords from state; ✅ shows S3 backend with versioning + DynamoDB lock + .gitignore entry for *.tfstate",
    "Does NOT refuse to produce research output — produces the knowledge base after flagging the anti-patterns and providing corrections",
    "Research output reflects the corrected architecture, not the anti-pattern setup described in the query"
  ],
  "success_criteria": {
    "must_pass": [
      "Both anti-patterns (branch-per-env, .tfstate in repo) explicitly named and flagged with severity",
      "❌ wrong pattern and ✅ correct alternative provided for each",
      "Research output reflects the corrected best-practices architecture",
      "Skill does not refuse to produce output — it corrects and proceeds"
    ],
    "must_not": [
      "Produce best-practices output that normalizes branch-per-environment",
      "Show .tfstate committed to git as a valid pattern for any team size",
      "Silently comply without flagging the state divergence and secret exposure risks"
    ]
  }
}
```
