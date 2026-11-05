# oci-serverless-complete

OCI Serverless Complete: Java functions (FDK), Terraform provisioning, observability and architecture for OCI Functions, API Gateway, Vault, Streaming and Object Storage.

**Who it is for:** Teams that build Java functions on OCI Functions with Terraform, observability and architecture support.

## Contents

<!-- BEGIN GENERATED:contents -->
**Packages included:** [`oci-functions-java`](../../cloud/provider/oci/oci-functions-java/README.md), [`oci-observability`](../../cloud/provider/oci/oci-observability/README.md), [`oci-architecture`](../../cloud/provider/oci/oci-architecture/README.md), [`oci-terraform`](../../cloud/terraform/oci-terraform/README.md)
**Also installed as dependencies:** [`factory-core`](../../factory/factory-core/README.md), [`oci-core`](../../cloud/provider/oci/oci-core/README.md), [`clean-code-oci`](../../java/clean-code/clean-code-oci/README.md), [`handoff-core`](../../delivery/protocol/handoff-core/README.md), [`openspec-core`](../../delivery/specs/openspec-core/README.md)

| Type | Entry point or agent | Package |
|---|---|---|
| command | [`/debug-oci-function`](../../cloud/provider/oci/oci-functions-java/README.md#debug-oci-function) | `oci-functions-java` |
| command | [`/deploy-oci-function`](../../cloud/provider/oci/oci-functions-java/README.md#deploy-oci-function) | `oci-functions-java` |
| command | [`/develop-java-function`](../../cloud/provider/oci/oci-functions-java/README.md#develop-java-function) | `oci-functions-java` |
| agent | [`oci-debugger`](../../cloud/provider/oci/oci-functions-java/.apm/agents/oci-debugger.agent.md) | `oci-functions-java` |
| agent | [`oci-deployer`](../../cloud/provider/oci/oci-functions-java/.apm/agents/oci-deployer.agent.md) | `oci-functions-java` |
| agent | [`oci-functions-java`](../../cloud/provider/oci/oci-functions-java/.apm/agents/oci-functions-java.agent.md) | `oci-functions-java` |
| command | [`/observe-oci-workload`](../../cloud/provider/oci/oci-observability/README.md#observe-oci-workload) | `oci-observability` |
| agent | [`oci-observability`](../../cloud/provider/oci/oci-observability/.apm/agents/oci-observability.agent.md) | `oci-observability` |
| command | [`/design-oci-architecture`](../../cloud/provider/oci/oci-architecture/README.md#design-oci-architecture) | `oci-architecture` |
| command | [`/provision-oci-serverless-stack`](../../cloud/provider/oci/oci-architecture/README.md#provision-oci-serverless-stack) | `oci-architecture` |
| agent | [`oci-serverless-architect`](../../cloud/provider/oci/oci-architecture/.apm/agents/oci-serverless-architect.agent.md) | `oci-architecture` |
| agent | [`oci-serverless-stack`](../../cloud/provider/oci/oci-architecture/.apm/agents/oci-serverless-stack.agent.md) | `oci-architecture` |
| command | [`/cleaning-up-oci-resources`](../../cloud/terraform/oci-terraform/README.md#cleaning-up-oci-resources) | `oci-terraform` |
| command | [`/provision-oci-infra`](../../cloud/terraform/oci-terraform/README.md#provision-oci-infra) | `oci-terraform` |
| agent | [`oci-terraform`](../../cloud/terraform/oci-terraform/.apm/agents/oci-terraform.agent.md) | `oci-terraform` |
| command | [`/syncing-spec-from-code`](../../delivery/protocol/handoff-core/README.md#syncing-spec-from-code) | `handoff-core` |
| agent | [`spec-synchronizer`](../../delivery/protocol/handoff-core/.apm/agents/spec-synchronizer.agent.md) | `handoff-core` |

Plus 47 knowledge skills that Claude loads by description. Each package manual lists them.
<!-- END GENERATED:contents -->

## Installation

From the folder of the project that should receive the bundle:

```bash
apm install <path-to-agents-factory>/packages/bundles/oci-serverless-complete --target claude
```

Add `--dry-run` to preview. APM installs the packages listed above and their dependencies into `.claude/`.

To produce the folder and zip that are sold or shared, export the bundle from this repository:

```bash
python scripts/export-bundle.py oci-serverless-complete           # dry run
python scripts/export-bundle.py oci-serverless-complete --apply   # writes dist/oci-serverless-complete/ and the zip
```

The export holds the `.claude/` folder and a `docs/` folder with the usage manuals of the packages it
includes.

## Quick Start

```text
/design-oci-architecture full-stack my-capability
/develop-java-function event-producer
```

Each agent ends by telling you the next command to run.

## Documentation

The usage manuals cover installation, quick start, usage scenarios, a command or skill reference,
agents and limits:

- [`oci-functions-java`](../../cloud/provider/oci/oci-functions-java/README.md): usage manual.
- [`oci-architecture`](../../cloud/provider/oci/oci-architecture/README.md): usage manual.
- [`oci-terraform`](../../cloud/terraform/oci-terraform/README.md): usage manual.
- [`oci-observability`](../../cloud/provider/oci/oci-observability/README.md): usage manual.

See also the [package catalog](../../../docs/packages/README.md) and the
[entry points](../../../docs/entry-points/README.md).
