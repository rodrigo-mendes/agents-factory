# Always-Do Patterns

Back to [SKILL.md](../SKILL.md). Quarkus 3.40.1.1. Code and trees are illustrative; the directory names are a team convention (medium confidence, M1 in the register).

## Contents

- [1. Resolve the real coordinates](#1-resolve-the-real-coordinates)
- [2. Artifact contract](#2-artifact-contract)
- [3. Package taxonomy](#3-package-taxonomy)
- [4. Index library modules](#4-index-library-modules)
- [5. Tests live with the module](#5-tests-live-with-the-module)
- [6. OpenSpec at the root](#6-openspec-at-the-root)
- [7. .gitignore](#7-gitignore)

## 1. Resolve the real coordinates

Read `groupId`, the base package and the existing `<modules>` from the project before creating anything; ask when missing. See [loader notes](./project-structure-loader.md).

```bash
# Representative - adapt to your environment
grep -n "<groupId>\|<module>" pom.xml | head
find functions -maxdepth 2 -name pom.xml
```

## 2. Artifact contract

Each function module hands Terraform one file, `functions/<name>/target/function.zip`. The rest of the contract is owned by the Lambda skill; this table only names what to pass on ([packaging blueprint](../../developing-quarkus-amazon-lambda-v3-40/blueprints/packaging-and-artifact-contract.md#artifact-contract-consumed-by-terraform)).

| Item | JVM build | Native build |
|---|---|---|
| Package | `target/function.zip` | `target/function.zip`, executable renamed `bootstrap` |
| Runtime | `java21`, `java17.al2023` or `java25` (unverified, U4 in the register; see developing-quarkus-amazon-lambda-v3-40 Ask First C2) | `provided.al2023` (pairing: medium confidence, M4) |
| Handler | `io.quarkus.amazon.lambda.runtime.QuarkusStreamHandler::handleRequest` (JVM build) | not stated by the guide (unverified, U3 in the register) |
| Environment | `QUARKUS_LAMBDA_HANDLER` (optional override) | `DISABLE_SIGNAL_HANDLERS=true`, optional `QUARKUS_LAMBDA_HANDLER` |
| Extra zip content | `src/main/zip.jvm/` | `src/main/zip.native/` |

Infra receives the zip path as an input (for example a variable per function); the HCL belongs to `provisioning-aws-lambda-v6`, never SAM or CDK. `manage.sh` and `sam.*.yaml` are generated helpers, not the deployment path.

## 3. Package taxonomy

Source: `refactoring-quarkus-java` (`package-taxonomy`). Team practice, not a Quarkus requirement (medium confidence, M1); this pattern sits outside the High tier.

```
functions/orders/src/main/java/<base>/orders/
├── OrdersLambda.java          package root: @Named handler, thin
├── handler/                   one class per use-case flow (CreateOrderFlow)
├── web/                       response building, error to HTTP mapping (HTTP Lambdas)
├── client/                    AWS SDK and REST client wrappers
├── transform/                 mapping and marshalling
└── obs/                       observability helpers (see observing-quarkus-lambda)
```

The handler reads the event, validates at the boundary, calls one flow and builds the response. `handler/` means a use-case flow, not the Lambda handler class.

## 4. Index library modules

A dependency is scanned for beans only with `beans.xml`, `META-INF/jandex.idx` or `quarkus.index-dependency.<name>.*` ([CDI reference](https://quarkus.io/version/3.40/guides/cdi-reference), via `refactoring-quarkus-java`).

```properties
# Quarkus 3.40.1.1 - in the consuming function module's application.properties (representative)
quarkus.index-dependency.shared-tenant.group-id=com.company.project
quarkus.index-dependency.shared-tenant.artifact-id=shared-tenant
```

The alternative is an empty `shared/<name>/src/main/resources/META-INF/beans.xml`. Do one of them for every library module that holds beans.

## 5. Tests live with the module

- Team practice (medium confidence, M1): `functions/<name>/src/test/java/<base>/<name>/` mirrors the main package; one test class per entry class plus unit tests next to the flows they cover.
- Lambda tests use `quarkus-junit` and RestAssured against the mock event server; `quarkus-test-amazon-lambda` and `LambdaClient` were removed in Quarkus 3.31 ([Migration Guide 3.31](https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.31)). Test ports 8080 (dev) and 8081 (test), keys `quarkus.lambda.mock-event-server.dev-port` and `.test-port`; `0` means random ([packaging blueprint](../../developing-quarkus-amazon-lambda-v3-40/blueprints/packaging-and-artifact-contract.md#dev-mode-and-mock-event-server-detail-testing-quarkus-amazon-lambda-v3-40)).
- Depth: [testing-quarkus-amazon-lambda-v3-40](../../testing-quarkus-amazon-lambda-v3-40/SKILL.md).

## 6. OpenSpec at the root

```
openspec/
├── specs/
└── changes/
    ├── <id>/{proposal.md, specs/, design.md, tasks.md}
    └── archive/<date>-<id>/
```

Layout from OpenSpec v1.15.0 (https://github.com/Fission-AI/OpenSpec). Delta format, validator quirks and the CLI belong to `specifying-changes-with-openspec-v1-15`. Claude Code support for OpenSpec uses `.claude/skills/openspec-*` and `/opsx:<id>` commands (same source); those are tool files, not part of this layout.

## 7. .gitignore

```gitignore
# Maven build output (function.zip, bootstrap, sam.*.yaml live in target/)
target/

# Terraform
.terraform/
*.tfstate
*.tfstate.*
*.tfplan
# NOT ignored: .terraform.lock.hcl - commit it next to each root module
```

`.terraform.lock.hcl` must be committed (rule `aws-terraform-project-config`, rule 4, whose verify step expects it not git-ignored). The state, plan and `.terraform/` entries are medium confidence: no AWS Terraform rule read for this skill lists them. Check with:

```bash
git check-ignore -v functions/orders/target/function.zip     # expected: ignored
git check-ignore -v infra/prod/.terraform.lock.hcl           # expected: no output
```
