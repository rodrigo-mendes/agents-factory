# aws-terraform-complete

AWS Terraform Complete: 26 version-locked provisioning-aws-<service>-v6 skills (hashicorp/aws 6.x) plus the aws-terraform-engineer and terraform-rules-author agents.

**Who it is for:** Teams that write AWS Terraform (hashicorp/aws 6.x) and want version-locked skills and an engineer agent that checks its work offline.

## Contents

<!-- BEGIN GENERATED:contents -->
**Packages included:** [`terraform`](../../cloud/terraform/terraform/README.md)
**Also installed as dependencies:** [`factory-core`](../../factory/factory-core/README.md), [`research-core`](../../factory/research-core/README.md), [`artifact-authoring`](../../factory/artifact-authoring/README.md), [`handoff-core`](../../delivery/protocol/handoff-core/README.md), [`aws-terraform`](../../cloud/terraform/aws-terraform/README.md), [`openspec-core`](../../delivery/specs/openspec-core/README.md)

| Type | Entry point or agent | Package |
|---|---|---|
| command | [`/provision-aws-terraform`](../../cloud/terraform/terraform/README.md#provision-aws-terraform) | `terraform` |
| command | [`/technical-framework-researcher-terraform`](../../cloud/terraform/terraform/README.md#technical-framework-researcher-terraform) | `terraform` |
| command | [`/terraform-engineering-best-practices-researcher`](../../cloud/terraform/terraform/README.md#terraform-engineering-best-practices-researcher) | `terraform` |
| command | [`/terraform-instructions-compiler`](../../cloud/terraform/terraform/README.md#terraform-instructions-compiler) | `terraform` |
| command | [`/terraform-rules-author`](../../cloud/terraform/terraform/README.md#terraform-rules-author) | `terraform` |
| agent | [`aws-terraform-engineer`](../../cloud/terraform/terraform/.apm/agents/aws-terraform-engineer.agent.md) | `terraform` |
| agent | [`terraform-code-reviewer`](../../cloud/terraform/terraform/.apm/agents/terraform-code-reviewer.agent.md) | `terraform` |
| agent | [`terraform-rules-author`](../../cloud/terraform/terraform/.apm/agents/terraform-rules-author.agent.md) | `terraform` |
| agent | [`framework-researcher`](../../factory/research-core/.apm/agents/framework-researcher.agent.md) | `research-core` |
| agent | [`research-synthesizer`](../../factory/research-core/.apm/agents/research-synthesizer.agent.md) | `research-core` |
| agent | [`section-investigator`](../../factory/research-core/.apm/agents/section-investigator.agent.md) | `research-core` |
| command | [`/agent-creator`](../../factory/artifact-authoring/README.md#agent-creator) | `artifact-authoring` |
| command | [`/architecture-approaches-skill-generator`](../../factory/artifact-authoring/README.md#architecture-approaches-skill-generator) | `artifact-authoring` |
| command | [`/methodologies-skill-generator`](../../factory/artifact-authoring/README.md#methodologies-skill-generator) | `artifact-authoring` |
| command | [`/skill-creator`](../../factory/artifact-authoring/README.md#skill-creator) | `artifact-authoring` |
| agent | [`artifact-author`](../../factory/artifact-authoring/.apm/agents/artifact-author.agent.md) | `artifact-authoring` |
| command | [`/syncing-spec-from-code`](../../delivery/protocol/handoff-core/README.md#syncing-spec-from-code) | `handoff-core` |
| agent | [`spec-synchronizer`](../../delivery/protocol/handoff-core/.apm/agents/spec-synchronizer.agent.md) | `handoff-core` |

Plus 29 knowledge skills that Claude loads by description. Each package manual lists them.
<!-- END GENERATED:contents -->

## Installation

From the folder of the project that should receive the bundle:

```bash
apm install <path-to-agents-factory>/packages/bundles/aws-terraform-complete --target claude
```

Add `--dry-run` to preview. APM installs the packages listed above and their dependencies into `.claude/`.

To produce the folder and zip that are sold or shared, export the bundle from this repository:

```bash
python scripts/export-bundle.py aws-terraform-complete           # dry run
python scripts/export-bundle.py aws-terraform-complete --apply   # writes dist/aws-terraform-complete/ and the zip
```

The export holds the `.claude/` folder and a `docs/` folder with the usage manuals of the packages it
includes.

## Quick Start

```text
/provision-aws-terraform private S3 bucket with KMS and access logging, with mocked test ./infra
```

## Documentation

The usage manuals cover installation, quick start, usage scenarios, a command or skill reference,
agents and limits:

- [`terraform`](../../cloud/terraform/terraform/README.md): usage manual.

See also the [package catalog](../../../docs/packages/README.md) and the
[entry points](../../../docs/entry-points/README.md).
