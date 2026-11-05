# Terraform commands

These commands research Terraform providers, write AWS Terraform, and compile Terraform knowledge
into rules. They work offline on files: they never apply, destroy or import infrastructure.

## Commands

| Job | Command | Routes to | Argument hint |
|---|---|---|---|
| Write or review AWS Terraform for a fixed requirement | [`/provision-aws-terraform`](../../packages/cloud/terraform/terraform/README.md#provision-aws-terraform) | `aws-terraform-engineer` | `<requirement> <terraform-dir>` |
| Research a provider at a version | [`/technical-framework-researcher-terraform`](../../packages/cloud/terraform/terraform/README.md#technical-framework-researcher-terraform) | `framework-researcher` | `<provider> <version> [depth] [iterations]` |
| Research Terraform practice on a topic | [`/terraform-engineering-best-practices-researcher`](../../packages/cloud/terraform/terraform/README.md#terraform-engineering-best-practices-researcher) | `framework-researcher` | `<topic> [depth] [iterations]` |
| Compile a research file into instructions | [`/terraform-instructions-compiler`](../../packages/cloud/terraform/terraform/README.md#terraform-instructions-compiler) | `artifact-author` | `<research-file-path>` |
| Compile a research file into scoped rules for a project | [`/terraform-rules-author`](../../packages/cloud/terraform/terraform/README.md#terraform-rules-author) | `terraform-rules-author` | `<research-file-path> <project-root> [platform]` |

## Examples

Write an AWS module with a mocked test:

```
/provision-aws-terraform private S3 bucket with KMS and access logging, with mocked test ./infra
```

Research a provider:

```
/technical-framework-researcher-terraform aws 5.x depth=deep iterations=3
```

Turn research into rules for a project:

```
/terraform-rules-author workspace/research_terraform_v1.5.md ./infra platform: claude-code
```

## What it will not do

- `/provision-aws-terraform` runs only offline checks: format, validate without a backend, and
  mocked tests. It never runs `apply`, `destroy` or `import`. Run the plan and apply yourself, after
  review.
- It covers the 26 AWS services in [`aws-terraform`](../../packages/cloud/terraform/aws-terraform/README.md).
  A requirement outside them comes back as questions, not as guessed code.

## OCI Terraform

OCI provisioning is done by `/provision-oci-infra` in [oci-serverless](oci-serverless.md), not by
the commands above.

## Related

- Packages: [`terraform`](../../packages/cloud/terraform/terraform/README.md),
  [`aws-terraform`](../../packages/cloud/terraform/aws-terraform/README.md),
  [`oci-terraform`](../../packages/cloud/terraform/oci-terraform/README.md).
- Agents: `aws-terraform-engineer`, `terraform-rules-author` ([subagents](../agents/README.md)).
