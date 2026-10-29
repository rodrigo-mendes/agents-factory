---
name: structuring-quarkus-lambda-projects
description: "Defines where code goes in a Quarkus 3.40 AWS Lambda SaaS repo: Lambda granularity, Maven modules, package taxonomy, tests, function.zip to Terraform, openspec/ and infra/. Use when creating or moving a module, package, handler or test. Not for handler code, HCL or Quarkus 4."
---

# Structuring Quarkus Lambda projects (Quarkus 3.40 LTS)

> Version lock: every claim applies to **Quarkus 3.40 LTS, patch 3.40.1.1**, Quarkiverse quarkus-amazon-services 3.23.x and OpenSpec v1.15.0. Research date **2026-10-28**. No new research: each statement comes from a named neighbour skill, a family fact or a repository rule.
> Claims tagged (unverified) or (medium confidence) were not fully confirmed against an official page; each maps to a line of the [register](./blueprints/unverified-and-risks.md#tag-to-register-mapping). The directory names `functions/`, `shared/`, `infra/` and the module naming are a team convention (medium confidence, M1).
> Covers placement only: repository layout, modules, packages, tests, artifact hand-off, ignore rules. Layout config: [assets/project-structure.yml](./assets/project-structure.yml).

## Version Context

| Item | Value | Source (fetched 2026-10-28) |
|---|---|---|
| Quarkus | 3.40 LTS, released 2026-09-30, community-maintained until 2027-09-30; patch 3.40.1.1 | https://quarkus.io/releases |
| Build output per function module | `target/function.zip` (native: executable renamed `bootstrap`), plus `manage.sh`, `sam.jvm.yaml`, `sam.native.yaml` | https://quarkus.io/guides/aws-lambda |
| Quarkiverse AWS clients | BOM `io.quarkiverse.amazonservices:quarkus-amazon-services-bom:3.23.0`, built on Quarkus 3.40.0 (parent POM) | https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/common-features.html ; https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-services-parent/3.23.0/quarkus-amazon-services-parent-3.23.0.pom |
| HTTP extensions | `quarkus-amazon-lambda-http` and `-rest`: "This technology is considered preview" | https://quarkus.io/version/3.40/guides/aws-lambda-http |
| OpenSpec | v1.15.0, layout `openspec/specs`, `openspec/changes/<id>/...` | https://github.com/Fission-AI/OpenSpec |
| Terraform targets (pointer) | Terraform `~> 1.16`, hashicorp/aws `~> 6.69`, `use_lockfile = true`, commit `.terraform.lock.hcl` | rule `aws-terraform-project-config` |

**Version-lifetime risk** (as of 2026-10-28; details in [register](./blueprints/unverified-and-risks.md#version-lifetime-risk)).
- Quarkus 4.0.0 is "Upcoming" with no date; the layout of this skill is for 3.40.x.
- The HTTP extensions are preview; a layout that depends on them may need rework on upgrade.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- [Team practice (outside the tiers)](#team-practice-not-a-quarkusaws-fact)
- [Verification Loop](#verification-loop)
- [Layout config (YAML)](./assets/project-structure.yml)
- [Loader notes](./blueprints/project-structure-loader.md)
- [Always-do patterns](./blueprints/always-do-patterns.md)
- [Ask-first decisions](./blueprints/ask-first-decisions.md)
- [Never-do patterns](./blueprints/never-do-patterns.md)
- [Unverified and risks register](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Repository layout

```
<repo>/
├── pom.xml            parent: BOM imports, plugin management, <modules>
├── functions/<name>/  one Maven module per deployable Lambda artifact -> target/function.zip
├── shared/<name>/     library modules (no function.zip); need a bean index
├── infra/             Terraform root modules (HCL owned by provisioning-aws-lambda-v6)
├── openspec/          specs and changes (repo root, not in a module)
└── .gitignore
```

The directory names `functions/`, `shared/` and `infra/` are a team convention (medium confidence), not a Quarkus requirement.

Inside a function module the packages follow the taxonomy of `refactoring-quarkus-java` (package `quarkus-core`, blueprint `package-taxonomy`): the Lambda handler or REST resource at the package root, then `handler/` (one class per use-case flow, not the Lambda handler), `web/`, `client/`, `transform/`, `obs/`. It is a team convention, not a Quarkus requirement (see [Team practice](#team-practice-not-a-quarkusaws-fact)).

## Blueprints & Guardrails

### ✅ Always Do

- **Resolve `groupId` and base package from the real project first**, from the root `pom.xml` or the source tree; `com.company.project` is a placeholder. See [patterns](./blueprints/always-do-patterns.md#1-resolve-the-real-coordinates).
- **Treat `target/function.zip` per function module as the only artifact handed to Terraform**, with, for the JVM build, the handler `io.quarkus.amazon.lambda.runtime.QuarkusStreamHandler::handleRequest` and the user handler chosen by `quarkus.lambda.handler` ([aws-lambda guide](https://quarkus.io/guides/aws-lambda)). See [patterns](./blueprints/always-do-patterns.md#2-artifact-contract) and the [packaging blueprint](../developing-quarkus-amazon-lambda-v3-40/blueprints/packaging-and-artifact-contract.md#artifact-contract-consumed-by-terraform).
- **Index every library module that holds beans** with `beans.xml`, `META-INF/jandex.idx` or `quarkus.index-dependency.<name>.*`; a dependency is scanned only then ([CDI reference](https://quarkus.io/version/3.40/guides/cdi-reference)). See [patterns](./blueprints/always-do-patterns.md#4-index-library-modules).
- **Test Lambdas with `quarkus-junit` plus RestAssured against the mock event server** (`quarkus-test-amazon-lambda` was removed in Quarkus 3.31, [Migration Guide 3.31](https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.31)). Detail: `testing-quarkus-amazon-lambda-v3-40`. See [patterns](./blueprints/always-do-patterns.md#5-tests-live-with-the-module).
- **Keep `openspec/` at the repository root** with `openspec/specs` and `openspec/changes/<id>/{proposal.md,specs/,design.md,tasks.md}`; rules of the format belong to `specifying-changes-with-openspec-v1-15`. See [patterns](./blueprints/always-do-patterns.md#6-openspec-at-the-root).
- **Commit `.terraform.lock.hcl`** next to each Terraform root module (rule `aws-terraform-project-config`, rule 4; [HashiCorp dependency lock file](https://developer.hashicorp.com/terraform/language/files/dependency-lock)). See [patterns](./blueprints/always-do-patterns.md#7-gitignore).

The ignore entries for `target/`, `.terraform/`, `*.tfstate*` and `*.tfplan` cannot be High (medium confidence, M3 in the register); they live, tagged, in [always-do pattern 7](./blueprints/always-do-patterns.md#7-gitignore).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| Lambda granularity (ADR, no default) | A: one module per function. B: one HTTP Lambda serving many routes (`quarkus-amazon-lambda-http` or `-rest`, preview). C: one module with several `@Named` handlers deployed as several Lambdas from the same code. Role, memory, timeout, runtime mode and SnapStart are per Lambda. [Detail](./blueprints/ask-first-decisions.md#1-one-function-per-module-or-one-http-lambda-with-many-routes) | "How many Lambdas, and which routes or events go to which? Is per-function least privilege required?" |
| Splitting a shared library module | Needs a bean index and may change which tests see the beans; a second consumer justifies it. [Detail](./blueprints/ask-first-decisions.md#2-shared-library-modules) | "Is there a second function that needs this code?" |
| Package taxonomy adoption | Adopt the taxonomy of `refactoring-quarkus-java` or keep the project's. [Detail](./blueprints/ask-first-decisions.md#3-package-taxonomy-or-existing-layout) | "Adopt this layout or follow the existing one?" |
| Mock event server port per module | Fixed 8081 vs `0` (random) when modules test in parallel; parallel execution is the user's build choice (medium confidence). [Detail](./blueprints/ask-first-decisions.md#4-mock-event-server-port-in-multi-module-builds) | "Do modules run tests in parallel?" |
| Native module vs JVM module | Per function: JVM, JVM + SnapStart or native (mutually exclusive); decided in the Lambda skill. [Detail](./blueprints/ask-first-decisions.md#5-runtime-mode-per-module) | "Which mode per function?" |
| Existing project with a different layout | Do not migrate unprompted | "Adopt this layout or keep the current one?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Put more than one HTTP framework in a function module ([guide](https://quarkus.io/version/3.40/guides/aws-lambda-http)) | Keep one of `quarkus-rest`, `quarkus-reactive-routes`, `quarkus-undertow` |
| Deploy from `sam.*.yaml` or write SAM or CDK; they are reference output ([packaging blueprint](../developing-quarkus-amazon-lambda-v3-40/blueprints/packaging-and-artifact-contract.md)) | Terraform through `provisioning-aws-lambda-v6` |
| Copy the REST extension's `sam.native.yaml` runtime `provided` (deprecated 2024-01-08; [source file at tag 3.40.1.1](https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda-rest/deployment/src/main/resources/http/sam.native.yaml)) | Take the runtime from the Lambda skill's Ask First choice |
| Rename or move the Lambda handler bean without changing `quarkus.lambda.handler` ([aws-lambda guide](https://quarkus.io/guides/aws-lambda)) | Change class name, CDI name and property in one step |
| Add `quarkus-test-amazon-lambda` or `LambdaClient`; removed in Quarkus 3.31 ([Migration Guide 3.31](https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.31)) | `quarkus-junit` plus RestAssured against the mock event server |
| Ignore `.terraform.lock.hcl` (rule `aws-terraform-project-config`, rule 4; [HashiCorp](https://developer.hashicorp.com/terraform/language/files/dependency-lock)) | Commit it (rule 4) |
| Create or move a module that holds beans without a bean index | Add `beans.xml`, `jandex.idx` or `quarkus.index-dependency.*` |

Full ❌/✅ examples: [never-do patterns](./blueprints/never-do-patterns.md). Unconfirmed items: [register](./blueprints/unverified-and-risks.md).

### Team practice (not a Quarkus/AWS fact)

Team conventions, outside the three tiers (medium confidence, M1). Follow them in a new repo; in an existing one ask first (Ask First: package taxonomy).

- Keep the Lambda handler class or REST resource at the package root and delegate to flows in `handler/`; do not put the handler class inside `handler/`, `web/` or another sub-package ([taxonomy](./blueprints/always-do-patterns.md#3-package-taxonomy)).
- Keep tests in `src/test/java` of the same module, mirroring the main package ([patterns](./blueprints/always-do-patterns.md#5-tests-live-with-the-module)).
- Do not hardcode packages or paths: derive them from the resolved coordinates and [assets/project-structure.yml](./assets/project-structure.yml), e.g. `functions/${name}/src/main/java/${base_package_path}/...` ([never-do N1](./blueprints/never-do-patterns.md#n1-hardcoded-paths-and-packages), medium confidence, M1).

## Neighbours (names and links)

| Need | Skill |
|---|---|
| Handlers, packaging, JVM/SnapStart/native | [developing-quarkus-amazon-lambda-v3-40](../developing-quarkus-amazon-lambda-v3-40/SKILL.md) |
| HTTP extensions behind API Gateway | [developing-quarkus-amazon-lambda-http-v3-40](../developing-quarkus-amazon-lambda-http-v3-40/SKILL.md) |
| Tests | [testing-quarkus-amazon-lambda-v3-40](../testing-quarkus-amazon-lambda-v3-40/SKILL.md) |
| Cognito and tenant isolation | [securing-quarkus-lambda-cognito-v3-40](../securing-quarkus-lambda-cognito-v3-40/SKILL.md) |
| Observability across functions | [observing-quarkus-lambda](../observing-quarkus-lambda/SKILL.md) |
| Package taxonomy, refactoring | `refactoring-quarkus-java` (package `quarkus-core`, name only) |
| OpenSpec | `specifying-changes-with-openspec-v1-15` (name only) |
| Terraform | `provisioning-aws-lambda-v6`, `provisioning-aws-api-gateway-v6`; rules `aws-terraform-code-standards`, `aws-terraform-project-config`, `aws-terraform-skills-management` (names only) |
| IAM per function | `securing-aws-iam-serverless` (name only; rule R01, one IAM role per compute resource) |

## Quick Reference

Paths relative to the repository root; `<base>` is the base package path (dots as slashes).

| Artifact | Location | Name |
|---|---|---|
| Function module | `functions/<name>/` | kebab-case, one per Lambda artifact (convention) |
| Library module | `shared/<name>/` | kebab-case; bean index required |
| Lambda handler | `functions/<name>/src/main/java/<base>/<name>/` | `[Functionality]Lambda.java`, `@Named` |
| REST resource | same package root | `[Functionality]Resource.java` |
| Use-case flow | `.../handler/` | `[Functionality]Flow.java` |
| External I/O wrapper | `.../client/` | `[Functionality]Client.java` |
| Test | `functions/<name>/src/test/java/<base>/<name>/` | `[ClassName]Test.java` |
| Config | `functions/<name>/src/main/resources/application.properties` | one per module |
| Extra zip content | `src/main/zip.jvm/` or `src/main/zip.native/` | per module |
| Artifact | `functions/<name>/target/function.zip` | generated, ignored by git |
| Specs and changes | `openspec/specs`, `openspec/changes/<id>/` | OpenSpec v1.15.0 |
| Terraform | `infra/` | layout inside: `provisioning-aws-lambda-v6` |

Precedence when values disagree: the project's real tree and `pom.xml`, then [assets/project-structure.yml](./assets/project-structure.yml), then placeholders.

## Verification Loop

Run after creating or moving a module (representative, adapt to your environment):

1. `find functions -maxdepth 2 -name pom.xml` (expected: one `pom.xml` per function module).
2. `./mvnw install` (expected: `target/function.zip` in each function module).
3. `unzip -l functions/<name>/target/function.zip` (native build: entry `bootstrap`).
4. `git check-ignore -v functions/<name>/target/function.zip` (expected: ignored) and `git check-ignore -v infra/<env>/.terraform.lock.hcl` (expected: no output).
5. If a check fails, fix the module or the ignore entry and repeat from step 1. The register counts expected here: 4 unverified (U1-U4), 5 medium-confidence (M1-M5) (see [register](./blueprints/unverified-and-risks.md)).

## External Resources

All fetched 2026-10-28.

- Quarkus AWS Lambda guide: https://quarkus.io/guides/aws-lambda
- Quarkus Lambda HTTP guide: https://quarkus.io/version/3.40/guides/aws-lambda-http
- Quarkus CDI reference: https://quarkus.io/version/3.40/guides/cdi-reference
- OpenSpec: https://github.com/Fission-AI/OpenSpec
- Family-fact sources are cited inline by URL (the family-facts file is provenance only and is not shipped).
- Full bibliography: [unverified and risks](./blueprints/unverified-and-risks.md#source-bibliography)
