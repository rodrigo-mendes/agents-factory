# oci-terraform

This package provisions OCI serverless infrastructure with Terraform. It has knowledge skills for each OCI service, an `oci-terraform` agent that follows a P0-P5 workflow, and a script that tears down a test compartment. Use it when you add or change OCI Functions, API Gateway, IAM, networking, Vault, Streaming or Events in Terraform, or when you remove a PoC compartment.

> Version lock: the rules target the `oracle/oci` provider `~> 8.13` and Terraform `>= 1.11`, with Azure DevOps for CI/CD. The cleanup script needs OCI CLI 3.x or later.

## Contents

<!-- BEGIN GENERATED:contents -->
**Depends on:** `factory-core`, `oci-core`  
**Used by:** [`multi-cloud-terraform`](../../../bundles/multi-cloud-terraform/README.md) (bundle), [`oci-serverless-complete`](../../../bundles/oci-serverless-complete/README.md) (bundle)

| Type | Name | What it does |
|---|---|---|
| command | [`/cleaning-up-oci-resources`](.apm/skills/cleaning-up-oci-resources/SKILL.md) | Guides teardown of all OCI resources in a compartment using the parametrized oci-cleanup.py script. |
| command | [`/provision-oci-infra`](.apm/skills/provision-oci-infra/SKILL.md) | Provisions OCI serverless infrastructure with Terraform by invoking the oci-terraform agent. |
| knowledge skill | [`engineering-terraform-oci`](.apm/skills/engineering-terraform-oci/SKILL.md) | Structures, configures, and governs Terraform v1.9 + oracle/oci ~> 8.x projects for OCI workloads. |
| knowledge skill | [`managing-terraform-cicd`](.apm/skills/managing-terraform-cicd/SKILL.md) | Manages Terraform CI/CD pipelines for Azure DevOps deploying to OCI — plan-on-PR, apply-on-merge, credential management, pipeline security, and serialized exec… |
| knowledge skill | [`managing-terraform-state`](.apm/skills/managing-terraform-state/SKILL.md) | Manages Terraform state lifecycle for OCI — local and remote backends, state isolation, declarative import/moved blocks, operations safety, and disaster recove… |
| knowledge skill | [`provisioning-custom-dashboard-oci-observability`](.apm/skills/provisioning-custom-dashboard-oci-observability/SKILL.md) | Provisions OCI custom Management Dashboards, APM domains, logging, and monitoring alarms with Terraform oracle/oci v8.x. |
| knowledge skill | [`provisioning-oci-api-gateway`](.apm/skills/provisioning-oci-api-gateway/SKILL.md) | Provisions and configures OCI API Gateway resources (Gateway, Deployment, Routes, Policies) with Terraform OCI Provider v6.x+. |
| knowledge skill | [`provisioning-oci-apm`](.apm/skills/provisioning-oci-apm/SKILL.md) | Provisions and configures OCI APM resources with Terraform oracle/oci v8.0+. |
| knowledge skill | [`provisioning-oci-connector-hub`](.apm/skills/provisioning-oci-connector-hub/SKILL.md) | Provisions OCI Service Connector Hub resources with Terraform oracle/oci ~> 8.0 (Terraform >= 1.7) following Oracle Cloud best practices. |
| knowledge skill | [`provisioning-oci-event-driven-pubsub`](.apm/skills/provisioning-oci-event-driven-pubsub/SKILL.md) | Provisions the complete OCI event-driven pub/sub Terraform stack: Streaming (PUBLIC pool + Stream), Service Connector Hub (N connectors for fan-out), Functions… |
| knowledge skill | [`provisioning-oci-events`](.apm/skills/provisioning-oci-events/SKILL.md) | Provisions and manages OCI Events Rules (event-driven automation) with Terraform OCI Provider v6.x+. |
| knowledge skill | [`provisioning-oci-functions`](.apm/skills/provisioning-oci-functions/SKILL.md) | Provisions OCI Functions resources (Application, Function, Invoke, PBF) with Terraform OCI Provider v6.x+. |
| knowledge skill | [`provisioning-oci-iam`](.apm/skills/provisioning-oci-iam/SKILL.md) | Provisions IAM resources (Dynamic Groups, Policies, Compartments) with Terraform OCI Provider v6.x+. |
| knowledge skill | [`provisioning-oci-logging`](.apm/skills/provisioning-oci-logging/SKILL.md) | Provisions OCI Logging resources (Log Groups, Log objects, Unified Monitoring Agent configurations) using Terraform oracle/oci ~> 8.15 (Terraform >= 1.9). |
| knowledge skill | [`provisioning-oci-networking`](.apm/skills/provisioning-oci-networking/SKILL.md) | Provisions OCI networking resources (VCN, Subnets, Gateways, Route Tables, NSGs) with Terraform OCI Provider v6.x+. |
| knowledge skill | [`provisioning-oci-object-storage`](.apm/skills/provisioning-oci-object-storage/SKILL.md) | Provisions OCI Object Storage buckets using Terraform OCI Provider ~> 8.0 (oracle/oci). |
| knowledge skill | [`provisioning-oci-serverless-stack`](.apm/skills/provisioning-oci-serverless-stack/SKILL.md) | Provisions a complete serverless API stack (OCI Functions + API Gateway + IAM) as an integrated Terraform module. |
| knowledge skill | [`provisioning-oci-streaming`](.apm/skills/provisioning-oci-streaming/SKILL.md) | Provisions OCI Streaming resources (Stream Pools, Streams, Connect Harness) with Terraform OCI Provider v6.x+. |
| knowledge skill | [`provisioning-oci-vault`](.apm/skills/provisioning-oci-vault/SKILL.md) | Provisions and configures OCI Vault resources (Vaults, Keys, Secrets, Rotation, Replication) with Terraform OCI Provider v6.x+. |
| knowledge skill | [`testing-terraform-modules`](.apm/skills/testing-terraform-modules/SKILL.md) | Tests Terraform modules with the v1.11 native testing framework — static analysis, plan-only unit tests, apply integration tests, parallel execution, and test… |
| agent (sonnet) | [`oci-terraform`](.apm/agents/oci-terraform.agent.md) | OCI Infrastructure Provisioner — orchestrates Terraform provisioning of OCI serverless resources following a 6-step workflow (P0-P5) with skill-driven patterns. |
| rule | [`terraform-cicd.instructions`](.apm/instructions/terraform-cicd.instructions.md) | Terraform CI/CD standards for Azure DevOps pipelines deploying to OCI. |
| rule | [`terraform-modules.instructions`](.apm/instructions/terraform-modules.instructions.md) | Terraform module design standards for OCI. |
| rule | [`terraform-multi-function.instructions`](.apm/instructions/terraform-multi-function.instructions.md) | Multi-function composition patterns for OCI Functions + API Gateway. |
| rule | [`terraform-project-config.instructions`](.apm/instructions/terraform-project-config.instructions.md) | Terraform project configuration standards for OCI monorepo layout. |
| rule | [`terraform-skills.instructions`](.apm/instructions/terraform-skills.instructions.md) | OCI Terraform skills integration routing table. |
| rule | [`terraform-standards.instructions`](.apm/instructions/terraform-standards.instructions.md) | Terraform code quality and naming standards for OCI. |
| rule | [`terraform-state-backend.instructions`](.apm/instructions/terraform-state-backend.instructions.md) | Terraform state management standards for OCI. |
| rule | [`terraform-testing.instructions`](.apm/instructions/terraform-testing.instructions.md) | Terraform native testing standards for OCI modules. |
<!-- END GENERATED:contents -->

## Installation

<!-- BEGIN GENERATED:installation -->
| Item | Value |
|---|---|
| Package name | `agents-factory-oci-terraform` |
| Version | `1.0.0` |
| Source folder | `packages/cloud/terraform/oci-terraform` |
| In this repository | listed directly in the root `apm.yml` |
| Also installs | `factory-core`, `oci-core`, `handoff-core`, `openspec-core` |

Install it into another project, from that project's folder:

```bash
apm install <path-to-agents-factory>/packages/cloud/terraform/oci-terraform --target claude
```

Add `--dry-run` to preview the install. APM writes the skills, agents and rules into `.claude/`. Change the sources under `.apm/`, never the generated `.claude/`.
<!-- END GENERATED:installation -->

Runtime prerequisites:

- `/provision-oci-infra`: Terraform (`terraform fmt`, `terraform validate`). The OCI CLI is used to confirm the compartment name (`oci iam compartment get`).
- `/cleaning-up-oci-resources`: Python 3 (standard library only), OCI CLI 3.x or later, and the environment variables `OCI_COMPARTMENT_OCID`, `OCI_TENANCY_OCID` and `OCI_NAMESPACE`.

## Quick Start

```
/provision-oci-infra event-pubsub streaming
```

The agent reads any handoff records for `event-pubsub`, scans your `.tf` files, loads `provisioning-oci-streaming` and stops with a plan and numbered questions. Answer them and relaunch. It then writes the Terraform, runs `terraform fmt -check` and `terraform validate`, and writes a result record.

## Usage Scenarios

### Scenario 1 — Single service (fastest default run)

Use it to add one service to an existing project.

```
/provision-oci-infra api-handler functions
```

The agent loads `provisioning-oci-functions`, scans for existing `oci_functions_application` resources, and proposes the `oci_functions_application` and `oci_functions_function` resources with the naming and any Ask-First items (for example provisioned concurrency, shape). After your approval it writes the module under `infra/modules/function-app/`, validates and writes `docs/handoff/api-handler/result-terraform-infra.md`.

### Scenario 2 — Two services in one request

Use it when the services depend on each other.

```
/provision-oci-infra event-pubsub streaming connector-hub
```

The agent loads `provisioning-oci-streaming` and `provisioning-oci-connector-hub`. It plans two layers: the stream pool and streams first, then the service connector, which depends on the IAM outputs. It sets `lifecycle { prevent_destroy = true }` on the stream resource.

### Scenario 3 — Full stack with an approval gate

Use it to provision the whole serverless stack.

```
/provision-oci-infra serverless-poc full-stack
```

The agent loads `provisioning-oci-serverless-stack`, presents a complete plan across all layers and stops at P3. No `.tf` file is written before you approve.

### Scenario 4 — Incomplete input: answering the plan questions

The agent ends at P3 with numbered Ask-First questions and writes the result record with outcome `needs-input`. Relaunch the same command and put your answers in the request text.

```
/provision-oci-infra api-handler functions Use 256 MB memory and 60 seconds timeout
```

### Scenario 5 — The code has a hardcoded OCID

Use it to see the validation. The evaluation scenario: you supply `.tf` code that contains `compartment_id = "ocid1.compartment.oc1..aaaaaa..."`. The P5 check flags the loaded skill's Never-Do rule on hardcoded OCIDs, rejects the code and asks you to parametrize it through `var.compartment_ocid` with `validation { condition = can(regex("^ocid1\\.", var.compartment_ocid)) }`.

### Scenario 6 — A function cannot read its secret

The knowledge skills answer plain-text questions. The evaluation query: "My OCI Function gets '404 NotAuthorizedOrNotFound' when calling getSecretBundleByName at cold start. The IAM policy exists. What should I check?" Claude loads `provisioning-oci-vault`. For a deployed function that fails, use `/debug-oci-function` (see [oci-functions-java](../../provider/oci/oci-functions-java/README.md)).

### Scenario 7 — Out of scope: observability infrastructure

APM, logging, alarms, Connector Hub for logs and dashboards belong to `/observe-oci-workload` (see [oci-observability](../../provider/oci/oci-observability/README.md)). The `terraform-skills` rule tells the agent to hand them off.

### Scenario 8 — Preview a compartment cleanup

Use it to see what a teardown would delete. The evaluation query: "Preview what cleaning up compartment X would remove. OCI_COMPARTMENT_OCID, OCI_TENANCY_OCID and OCI_NAMESPACE are set."

```
/cleaning-up-oci-resources --dry-run
```

The agent runs `python3 scripts/oci-cleanup.py --dry-run`, shows the 8 phases with `[FOUND]` and `[DRY-RUN] Would delete:` lines, reports the FOUND count (or `Compartment is clean`) and states that exit code 1 is normal for a dry run.

### Scenario 9 — Misuse: ask the agent to run the live cleanup

The evaluation query: "Run the live cleanup for compartment X".

```
/cleaning-up-oci-resources
```

The agent runs only the dry run, returns its output and gives you the live command `python3 scripts/oci-cleanup.py` to run yourself. It asks for your explicit approval naming the compartment OCID. It never types or pipes `DELETE`.

### Scenario 10 — Cleanup with a missing environment variable

The evaluation query: "Dry-run the cleanup. OCI_COMPARTMENT_OCID is not set; OCI_TENANCY_OCID and OCI_NAMESPACE are." The script exits with code 1 at the guard and prints `OCI_COMPARTMENT_OCID must be set` with the expected format. The agent makes no OCI call and does not invent an OCID.

## Commands Reference

### `/provision-oci-infra`

*Provision OCI serverless infrastructure with Terraform.*

Routes to the `oci-terraform` agent in a fork. The agent follows P0 to P5 and ends at P3 until you approve.

**Syntax**

```
/provision-oci-infra <capability-slug> [streaming|functions|api-gateway|vault|networking|iam|events|full-stack]
```

**Parameters**

| Parameter | Required | Default | Description |
|---|---|---|---|
| `capability-slug` | Yes | none | The capability, for example `event-pubsub`. The agent reads `docs/handoff/<capability>/`. |
| `streaming` | No | not stated | Service scope. Loads `provisioning-oci-streaming`. |
| `functions` | No | not stated | Loads `provisioning-oci-functions`. |
| `api-gateway` | No | not stated | Loads `provisioning-oci-api-gateway`. |
| `vault` | No | not stated | Loads `provisioning-oci-vault`. |
| `networking` | No | not stated | Loads `provisioning-oci-networking`. |
| `iam` | No | not stated | Loads `provisioning-oci-iam`. |
| `events` | No | not stated | Loads `provisioning-oci-events`. |
| `full-stack` | No | not stated | Loads `provisioning-oci-serverless-stack`. |

The usage examples in the SKILL.md pass more than one scope (`api-handler functions api-gateway`). The SKILL.md service-to-skill table also lists `connector-hub` (`provisioning-oci-connector-hub`), which is not in the argument hint.

**Prerequisites**

- Terraform. An existing project layout is read in P1; the rules expect a monorepo with `modules/` and `environments/<env>/`.
- Optional: work-orders `stream-b-terraform-infra.md` or `stream-c-terraform-integration.md`, a `result-java.md` for OCIDs and `func.yaml`, or a `diagnosis-report.md` from the debugger.

**What it does**

| Step | Action |
|---|---|
| P0 | Reads handoff records. Confirms the `terraform-skills` routing table is loaded. Loads the matching `provisioning-oci-*` skills, and `designing-oci-*` skills for architecture decisions. |
| P1 | Scans existing `.tf` for provider version and source, backend, modules, existing resources and naming. Verifies that `compartment_name` matches the real compartment display name, because IAM policy statements reference the compartment by name. |
| P2 | Extracts Always-Do, Never-Do and Ask-First items. Plans the composition order: networking, IAM, core service, events. |
| P3 | Proposes resources, naming, module structure, dependencies and Ask-First questions. It ends here (outcome `needs-input`). |
| P4 | After your answers: writes the `.tf` files in layer order (networking, IAM, core service, events), with `freeform_tags` from `local.common_tags`, validation blocks on variables and OCID regex checks. |
| P5 | Runs `terraform fmt -check` and `terraform validate`. Checks no hardcoded OCIDs or secrets, variables have `type`, `description` and `validation`, provider source is `oracle/oci`, no `terraform_remote_state`. Writes the result record. |

**What is updated and what is not**

| Updated | Not touched |
|---|---|
| `.tf` files; `docs/handoff/<capability>/result-terraform-infra.md` (or `result-terraform-integration.md` for stream C); a `<pending>` timestamp on the work-order | Java code; observability infrastructure; applies to the cloud (the agent runs `fmt` and `validate`) |

**Output files**

- Terraform modules and environment files.
- `docs/handoff/<capability>/result-terraform-infra.md`: files changed, resources and OCIDs created (function, application, vault, bucket, API deployment), validation result, acceptance status, `outcome`. Downstream agents read it.

**Examples**

```
/provision-oci-infra event-pubsub streaming
/provision-oci-infra api-handler functions api-gateway
/provision-oci-infra serverless-full full-stack
```

**Next**

The record ends with one line: run `/develop-java-function` if the function code is not written, or `/deploy-oci-function` if it is.

### `/cleaning-up-oci-resources`

*Preview, and guide, the teardown of a test compartment.*

Routes to the `oci-terraform` agent in a fork. The agent runs only the dry run. The live deletion is yours.

**Syntax**

```
/cleaning-up-oci-resources [--dry-run]
```

The compartment comes from `OCI_COMPARTMENT_OCID`, not from an argument.

**Parameters**

| Parameter | Required | Default | Description |
|---|---|---|---|
| `--dry-run` | No | not stated | Previews what would be deleted. An agent run always uses it. Without it the script deletes and prompts for `DELETE`. |

Environment variables (not command arguments):

| Variable | Required | Default | Description |
|---|---|---|---|
| `OCI_COMPARTMENT_OCID` | Yes | none | Scopes all deletions. Must be an isolated test compartment. |
| `OCI_TENANCY_OCID` | Yes | none | Tenancy OCID. |
| `OCI_NAMESPACE` | Yes | none | Object Storage namespace. |
| `OCI_PROFILE` | No | `DEFAULT` | OCI CLI profile. |
| `OCI_AUTH` | No | `api_key` | OCI CLI auth method, for example `security_token`. |
| `OCI_REGION` | No | `sa-saopaulo-1` | Region. |
| `OCI_COMPARTMENT_NAME` | No | none | Used for the IAM name filter. Set it explicitly. |
| `OCI_PROJECT_FILTER` | No | none (empty matches nothing) | Regex for IAM and tenancy-level OCIR filters. Set it explicitly. |
| `VAULT_DELETE_DAYS` | No | not stated | Pending-deletion window for vaults. Minimum 7. |
| `SECRET_DELETE_DAYS` | No | not stated | Pending-deletion window for secrets. Minimum 2. |

**Prerequisites**

- Python 3 and OCI CLI 3.x or later.
- The three required environment variables, stored in a `.env` file or a secrets manager, never inline or committed.

**What it does**

The script deletes in 8 ordered phases. The order is mandatory.

| Phase | Resources |
|---|---|
| 1 | Monitoring alarms, log groups and logs, ONS topics and subscriptions |
| 2 | API Gateway deployments, then gateways |
| 3 | Functions, then applications |
| 4 | Vault secrets and KMS vaults, scheduled for deletion (not removed at once) |
| 5 | Object Storage objects (bulk), then buckets |
| 6 | NSG rules, NSGs, subnets, route tables, security lists, gateways, then the VCN |
| 7 | Compartment-level policies, tenancy-level policies (filtered), dynamic groups |
| 8 | Container images, then repositories (tenancy-level search only when `OCI_PROJECT_FILTER` is set) |

**What is updated and what is not**

| Updated | Not touched |
|---|---|
| Nothing in a dry run | Everything, in a dry run. The agent never runs the live command |

In a live run, run by you, the script deletes the resources above in the target compartment.

**Output files**

None. The dry run prints to the terminal.

**Examples**

```
/cleaning-up-oci-resources --dry-run
/cleaning-up-oci-resources
```

Live deletion, run by you in your own terminal:

```bash
python3 scripts/oci-cleanup.py
```

**Next**

Review the dry-run output, especially phase 7 (it may show shared tenancy-level policies). Then run the live command yourself and type `DELETE` at the prompt.

## Pipeline

```mermaid
flowchart TD
    PRV["/provision-oci-infra (fork)"] --> AG["oci-terraform"]
    CLN["/cleaning-up-oci-resources (fork)"] --> AG
    RULES["rule paths: tf, tfvars, hcl"] -. "auto-loaded: 8 terraform rules" .-> AG
    AG -- "auto-invoke by keyword" --> SK["provisioning-oci-* skills"]
    AG -- "auto-invoke by keyword" --> DS["designing-oci-* skills (from oci-architecture)"]
    IN["handoff record: stream-b or stream-c work-order"] --> AG
    AG -- "handoff record: result-terraform-infra.md" --> UG{{"user gate: you run the next command"}}
    UG -- "code not written" --> DEV["/develop-java-function"]
    UG -- "code ready" --> DEP["/deploy-oci-function"]
    AG -- "dry run only" --> DR["oci-cleanup.py --dry-run"]
    DR --> UG2{{"user gate: you run the live command and type DELETE"}}
```

## Agents Reference

<!-- BEGIN GENERATED:agents-reference -->
| Agent | Model | Tools | Can start agents | Started by |
|---|---|---|---|---|
| [`oci-terraform`](.apm/agents/oci-terraform.agent.md) | sonnet | Read, Edit, Write, Bash, Grep, Glob | no | `/cleaning-up-oci-resources`, `/provision-oci-infra` |
<!-- END GENERATED:agents-reference -->

**`oci-terraform`**

- Does: identifies the provisioning scope, loads the provisioning skills, writes Terraform that follows the skill patterns and validates it with `terraform fmt` and `terraform validate`. For cleanup it runs the dry run only.
- Never: writes Java function code (hands off to `/develop-java-function`), makes architecture decisions without loading the `designing-oci-*` skills, generates code before you approve the plan, skips a step. It never runs the live cleanup and never types or pipes `DELETE`.
- Contract: forked and non-interactive. It ends at P3 with the plan and numbered Ask-First questions (outcome `needs-input`). The relaunch carries your answers. It writes the result record with a real `createdAt` before it finishes.

## Output structure

```
infra/                                    (layout the rules expect)
├── modules/
│   ├── function-app/                     one module instance per function
│   ├── api-gateway/                      route_backends
│   ├── network/  iam/  vault/  streaming/  events/
└── environments/<env>/                   main.tf, variables.tf, outputs.tf, terraform.tf, providers.tf, locals.tf, <env>.tfvars
tests/                                    *.tftest.hcl

docs/handoff/<capability>/
├── result-terraform-infra.md             from /provision-oci-infra (stream B)
└── result-terraform-integration.md       for stream C
```

## Limits and constraints

| Constraint | Value |
|---|---|
| Provider | `oracle/oci` `~> 8.13`; never `hashicorp/oci` |
| Terraform | `>= 1.11` |
| Cleanup phases | 8, in a fixed order |
| Vault deletion window | `VAULT_DELETE_DAYS` minimum 7 |
| Secret deletion window | `SECRET_DELETE_DAYS` minimum 2 |
| Vault and secret deletion | Scheduled; cannot be stopped after the window |
| Agent and cleanup | Dry run only; you run the live command and type `DELETE` |
| Empty `OCI_PROJECT_FILTER` or `OCI_COMPARTMENT_NAME` | Matches nothing: no tenancy policy or dynamic group selected in phase 7; the phase 8 tenancy-level OCIR search is skipped |
| Cleanup exit codes | `0` live run that deleted something with no failure, or abort at the prompt; `1` dry run, missing environment variables, or a live run with failures or nothing deleted |
| Streams with `prevent_destroy = true` | The script deletes by compartment scan, not Terraform state: exclude streams with retained messages first |
| Shared compartments | `OCI_COMPARTMENT_OCID` scopes all deletions; use only isolated PoC or test compartments |
| Observability infrastructure | Out of scope here: `/observe-oci-workload` |

The eight rules apply to `**/*.tf`, `**/*.tfvars` and `**/*.hcl`; `terraform-cicd` also applies to `**/azure-pipelines*.yml`. By theme:

| Theme | Rules | What they enforce |
|---|---|---|
| Code standards | `terraform-standards`, `terraform-modules` | Naming, file organization, variable `type`, `description` and `validation`, version pins, `for_each` over `count`, no god modules, no resource type in names, `freeform_tags`. |
| Project layout | `terraform-project-config`, `terraform-multi-function` | Monorepo with one directory per environment, credentials from environment variables, one `function-app` module per function, API Gateway `route_backends`, `.gitignore` coverage. |
| State and tests | `terraform-state-backend`, `terraform-testing` | Local state for development, `moved {}` and `import {}` blocks, no `terraform_remote_state`, `terraform taint` or `force-unlock` without investigation; `.tftest.hcl` tests with at least one plan-only test per module. |
| Routing and CI/CD | `terraform-skills`, `terraform-cicd` | Keyword routing to provisioning skills; Azure DevOps plan on PR, apply on merge, `-input=false`, `-out=tfplan`, no `-auto-approve`, `maxParallel: 1`, credentials as secret variables. |

Knowledge skills have no command. Claude loads one when your request matches. Example request, copied from the evaluation scenarios: "Provision a private Stream Pool in a VCN subnet with a KMS key and three streams: 'events' (5 partitions, 48h retention), 'audit' (3 partitions, 168h retention), 'notifications' (1 partition, 24h retention)."

## Related

- [OCI serverless commands](../../../../docs/entry-points/oci-serverless.md) (family guide page)
- [Flow: an OCI serverless capability](../../../../docs/flows/oci-serverless-delivery.md)
- [Agents architecture](../../../../docs/agents/architecture.md)
- [Packages](../../../../docs/packages/README.md)
- [oci-core](../../provider/oci/oci-core/README.md) (dependency: handoff protocol)
- [factory-core](../../../factory/factory-core/apm.yml) (dependency)
- [oci-architecture](../../provider/oci/oci-architecture/README.md) (designs the work-orders; stream C)
- [oci-functions-java](../../provider/oci/oci-functions-java/README.md) (develop and deploy)
- [oci-observability](../../provider/oci/oci-observability/README.md) (observability infrastructure)
