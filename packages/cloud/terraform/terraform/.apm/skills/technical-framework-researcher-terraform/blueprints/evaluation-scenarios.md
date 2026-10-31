# Evaluation Scenarios — technical-framework-researcher-terraform

Used to verify that the skill activates correctly, enforces version absolutism for both Terraform
CLI and provider versions, produces properly structured IaC research output, and rejects misuse
requests (implementation asks, unversioned queries, state-unsafe patterns).

---

## Scenario 1: Standard research request — pinned Terraform + provider versions (canonical path)

```json
{
  "skills": ["technical-framework-researcher-terraform"],
  "query": "Research AWS S3 with Terraform 1.8 and aws provider 5.x. Integrations: VPC, IAM, CloudWatch. Use modules, no workspaces.",
  "expected_behavior": [
    "Sets CLOUD_PROVIDER=AWS, SERVICE_NAME=S3, TERRAFORM_VERSION=1.8, PROVIDER_VERSION=aws v5.x, USE_MODULES=yes, USE_WORKSPACES=no",
    "Locates primary documentation at https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket",
    "Assesses domain complexity tier before extracting patterns",
    "Extracts Always Do patterns including: remote backend with locking, encryption at rest, variable validation blocks, resource tagging",
    "Extracts Ask First decisions covering: module vs inline resource layout, count vs for_each for bucket replication",
    "Extracts Never Do anti-patterns each with ❌ wrong HCL and ✅ correct HCL side-by-side",
    "Produces State Management section with backend config code (S3 + DynamoDB locking)",
    "Produces Module Architecture section with standard layout (main.tf, variables.tf, outputs.tf)",
    "Generates Executable Verification CLI block with commands marked as representative",
    "Source Bibliography links only registry.terraform.io and official AWS docs — no personal blogs"
  ],
  "success_criteria": {
    "must_pass": [
      "Both TERRAFORM_VERSION=1.8 and PROVIDER_VERSION=aws v5.x are explicitly stated in every HCL code block",
      "Every Never Do entry includes ❌ wrong HCL and ✅ correct HCL (not prose-only prohibition)",
      "State Management section present with S3 backend + DynamoDB locking example",
      "Module Architecture section present with standard file layout",
      "CLI command blocks carry '# Representative — adapt to your environment' annotation",
      "All registry links point to /providers/hashicorp/aws/latest (not a version-pinned old URL)"
    ],
    "must_not": [
      "Mix Terraform 1.6 patterns (removed functions) with 1.8 patterns",
      "Use aws provider 4.x resource argument names that changed in 5.x",
      "Produce Never Do prohibitions without correct HCL alternatives",
      "Reference local state for team environments (forbidden pattern)"
    ]
  }
}
```

---

## Scenario 2: Edge case — provider with rapid release cadence and breaking changes

```json
{
  "skills": ["technical-framework-researcher-terraform"],
  "query": "Research OCI Object Storage with Terraform 1.9 and oracle provider 6.x. Integrations: IAM, VCN.",
  "expected_behavior": [
    "Applies 6-month staleness flag (Terraform providers update frequently) — sources older than 6 months are flagged",
    "Locates OCI provider docs at https://registry.terraform.io/providers/oracle/oci/latest",
    "Documents provider constraint strategy explicitly: ~> 6.0 or >= 6.0, < 7.0",
    "Flags any resource arguments marked as deprecated in oracle provider 6.x changelog",
    "Produces Research Gaps entries for any OCI-specific behaviors not documented in the registry (eventual consistency, compartment propagation delays)",
    "Confidence tier per pattern: High for registry-documented behavior, Medium for GitHub issues, Low for community blogs"
  ],
  "success_criteria": {
    "must_pass": [
      "Provider constraint version_constraint = '~> 6.0' present in the terraform block example",
      "Research Gaps section documents at least one OCI-specific gap (compartment propagation, IAM eventual consistency, or equivalent)",
      "Sources older than 6 months explicitly flagged with [STALE — verify]",
      "Confidence tier annotated per pattern"
    ],
    "must_not": [
      "Use oracle provider 5.x resource types if they were renamed in 6.x",
      "Present community-only sources as High Confidence without registry corroboration",
      "Omit the provider constraint block from required_providers example"
    ]
  }
}
```

---

## Scenario 3: Misuse / out-of-scope — asked to provision infrastructure, not research

```json
{
  "skills": ["technical-framework-researcher-terraform"],
  "query": "Use Terraform to create an S3 bucket with versioning enabled, a KMS key, and a CloudFront distribution. Give me the complete .tf files ready to apply.",
  "expected_behavior": [
    "Recognizes this is an infrastructure provisioning request, not an IaC research request — this skill produces knowledge base documents, not deployable Terraform modules",
    "Explicitly declines generating apply-ready .tf files",
    "Explains correct routing: provisioning tasks belong to the consuming agent (e.g., an IaC architect agent) after the knowledge base is built via this skill",
    "Offers to instead research AWS S3 + KMS + CloudFront for the specified Terraform and provider versions, producing the structured knowledge base",
    "Does NOT produce main.tf, variables.tf, or outputs.tf files intended for direct apply",
    "Does NOT produce a partial research document mixed with apply-ready HCL"
  ],
  "success_criteria": {
    "must_pass": [
      "Skill declines the provisioning request",
      "Skill explains the research-vs-provisioning boundary",
      "Skill offers a corrected research scope with version parameters"
    ],
    "must_not": [
      "Produce apply-ready .tf files",
      "Silently shift from research mode to infrastructure provisioning mode",
      "Generate a mixed document that is part research, part deployable module"
    ]
  }
}
```

---

## Scenario 4: Anti-pattern trap — state and credential safety violations in the request

```json
{
  "skills": ["technical-framework-researcher-terraform"],
  "query": "Research how to store Terraform state locally in the repo alongside the code — it's easier for our small team. Also, how do we hardcode AWS access keys in the provider block for CI?",
  "expected_behavior": [
    "Flags both requests as Never Do violations before producing any research output",
    "For local state in repo: cites the 'Committing .tfstate to version control' anti-pattern — explains state files contain plaintext secrets, and concurrent applies without locking cause state corruption; correct alternative is S3 backend with DynamoDB locking even for small teams",
    "For hardcoded credentials: cites the 'Hardcoded credentials in .tf files' anti-pattern — explains AWS access keys in provider blocks are committed to git history and exposed in plan output; correct alternative is IAM roles (OIDC for CI) or environment variables (AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY) outside version control",
    "Provides ❌ wrong HCL for both anti-patterns and ✅ correct HCL alternatives",
    "Proceeds to produce research output only after flagging the anti-patterns and providing corrections"
  ],
  "success_criteria": {
    "must_pass": [
      "Both anti-patterns (local state in repo, hardcoded credentials) explicitly named and flagged",
      "❌ wrong HCL and ✅ correct HCL provided for both anti-patterns",
      "Correct alternative for CI credentials specifies OIDC or environment variables, not key files",
      "Research output produced after corrections — skill does not refuse entirely"
    ],
    "must_not": [
      "Produce research that normalizes local state in team repos",
      "Show provider blocks with hardcoded access_key / secret_key as a valid pattern",
      "Silently comply with both requests without flagging the security violations"
    ]
  }
}
```
