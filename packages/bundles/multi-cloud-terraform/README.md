# multi-cloud-terraform

Multi-Cloud Terraform: AWS (hashicorp/aws 6.x) and OCI (oracle/oci) provisioning skills and agents in one install.

**Who it is for:** Teams that provision both AWS (hashicorp/aws 6.x) and OCI (oracle/oci) with Terraform.

## Contents

<!-- BEGIN GENERATED:contents -->
**Packages included:** [`terraform`](../../cloud/terraform/terraform/README.md), [`oci-terraform`](../../cloud/terraform/oci-terraform/README.md)
**Also installed as dependencies:** [`factory-core`](../../factory/factory-core/README.md), [`research-core`](../../factory/research-core/README.md), [`artifact-authoring`](../../factory/artifact-authoring/README.md), [`handoff-core`](../../delivery/protocol/handoff-core/README.md), [`aws-terraform`](../../cloud/terraform/aws-terraform/README.md), [`openspec-core`](../../delivery/specs/openspec-core/README.md), [`oci-core`](../../cloud/provider/oci/oci-core/README.md)

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
| command | [`/cleaning-up-oci-resources`](../../cloud/terraform/oci-terraform/README.md#cleaning-up-oci-resources) | `oci-terraform` |
| command | [`/provision-oci-infra`](../../cloud/terraform/oci-terraform/README.md#provision-oci-infra) | `oci-terraform` |
| agent | [`oci-terraform`](../../cloud/terraform/oci-terraform/.apm/agents/oci-terraform.agent.md) | `oci-terraform` |
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

Plus 48 knowledge skills that Claude loads by description. Each package manual lists them.
<!-- END GENERATED:contents -->

## Installation

From the folder of the project that should receive the bundle:

```bash
apm install <path-to-agents-factory>/packages/bundles/multi-cloud-terraform --target claude
```

Add `--dry-run` to preview. APM installs the packages listed above and their dependencies into `.claude/`.

To produce the folder and zip that are sold or shared, export the bundle from this repository:

```bash
python scripts/export-bundle.py multi-cloud-terraform           # dry run
python scripts/export-bundle.py multi-cloud-terraform --apply   # writes dist/multi-cloud-terraform/ and the zip
```

The export holds the `.claude/` folder and a `docs/` folder with the usage manuals of the packages it
includes.

## Quick Start

```text
/provision-aws-terraform private S3 bucket with KMS and access logging, with mocked test ./infra
/provision-oci-infra my-capability functions
```

## Documentation

The usage manuals cover installation, quick start, usage scenarios, a command or skill reference,
agents and limits:

- [`terraform`](../../cloud/terraform/terraform/README.md): usage manual.
- [`oci-terraform`](../../cloud/terraform/oci-terraform/README.md): usage manual.

See also the [package catalog](../../../docs/packages/README.md) and the
[entry points](../../../docs/entry-points/README.md).
