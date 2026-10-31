---
name: structuring-camel-quarkus-projects
description: "Single source of truth for where Camel Quarkus integration code goes: directories, packages, file naming and test placement. Use when creating, moving or naming a route, processor, service, model, config or test class in a Camel Quarkus project."
---

## Overview

Layout and naming conventions for Camel Quarkus integration projects: which directory and package each artifact type goes in, how its file is named, and where its test lives. Load it before creating or moving any Java file. It covers placement only; framework behaviour (annotations, CDI, test APIs) belongs to the version-specific skills such as `developing-camel-quarkus-core-v3-40`.

Metadata: the config at [assets/project-structure.yml](./assets/project-structure.yml) holds the machine-readable form of this layout.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- [Layout config (YAML)](./assets/project-structure.yml)
- [Loader notes](./blueprints/project-structure-loader.md)
- [Evaluation Scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

- **Resolve `base_package` from the real project first** — read it from the existing source tree or `pom.xml`. `com.company.project` in the config is only a placeholder.
- **Inspect the current tree before creating a file** — `find src/main/java -type d` and `find src/main/java -name "*.java"` avoid duplicates and namespace clashes.
- **Place each artifact in the package for its type** — see the table in [Quick Reference](#quick-reference).
- **Name classes with the type suffix** — `[Functionality]Route`, `[Functionality]Processor`, `[Functionality]Service`, `[Entity]Model`, `[Config]Config`; PascalCase class names, camelCase methods and variables.
- **Mirror the main package in the test tree** — one `[ClassName]Test` per RouteBuilder class (the testing blueprint of `integrating-camel-quarkus` refines this per `routeId` as an explicit exception; see the orchestrator's testing blueprint when installed), in the same package under `src/test/java`; integration tests are `[Functionality]IntegrationTest`.

### ⚠️ Ask First

- **Changing `base_package`** — confirm with the user before creating files under a package different from the project's existing one.
- **Adding a new sub-package** — e.g. `integration/adapters/` versus reusing `integration/services/`.
- **Project already follows a different layout** — ask whether to adopt this layout or follow the existing one; do not migrate files unprompted.

### 🚫 Never Do

- **Never hardcode paths or packages** — derive them from the resolved `base_package` and [assets/project-structure.yml](./assets/project-structure.yml). Instead: `src/main/java/${base_package_path}/integration/routes/`.
- **Never mix artifact types in one package** — routes belong in `integration.routes` by project convention (team convention). Instead: use the package from the table.
- **Never use underscores in class names** — `FileProcessing_Route` is wrong; use `FileProcessingRoute`.
- **Never name tests off-pattern** — `FileRouteSpecTest` is wrong for `FileProcessingRoute`; use `FileProcessingRouteTest`.

## Quick Reference

Paths are relative to the project root; `<base>` is the base package path (dots as slashes).

| Artifact | Package (under `base_package`) | File location | File name |
|---|---|---|---|
| RouteBuilder | `integration.routes` | `src/main/java/<base>/integration/routes/` | `[Functionality]Route.java` |
| Processor | `integration.processors` | `src/main/java/<base>/integration/processors/` | `[Functionality]Processor.java` |
| Service | `integration.services` | `src/main/java/<base>/integration/services/` | `[Functionality]Service.java` |
| Model | `model` | `src/main/java/<base>/model/` | `[Entity]Model.java` |
| Config class | `config` | `src/main/java/<base>/config/` | `[Config]Config.java` |
| Route test | `integration.routes` | `src/test/java/<base>/integration/routes/` | `[ClassName]Test.java` |
| Service test | `integration.services` | `src/test/java/<base>/integration/services/` | `[ClassName]Test.java` |
| Unit test | `unit` | `src/test/java/<base>/unit/` | `[ClassName]Test.java` |
| Integration test | `integration` | `src/test/java/<base>/integration/` | `[Functionality]IntegrationTest.java` |

Resources: `src/main/resources/application.properties` and `src/test/resources/application.properties`.

Precedence when values disagree: the project's real source tree and `pom.xml`, then [assets/project-structure.yml](./assets/project-structure.yml), then the placeholder defaults.

Verification: `find src/main/java -type d`, `find src/test/java -type d`, `./mvnw clean compile`, `./mvnw test` (or `mvn` when the project has no wrapper).

## External Resources

- [Camel Quarkus user guide](https://camel.apache.org/camel-quarkus/latest/) (select the project's version)
- [Quarkus guides](https://quarkus.io/guides/)
- [Maven standard directory layout](https://maven.apache.org/guides/introduction/introduction-to-the-standard-directory-layout.html)
