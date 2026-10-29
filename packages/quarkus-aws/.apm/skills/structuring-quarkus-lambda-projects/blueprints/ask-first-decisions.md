# Ask-First Decisions

Back to [SKILL.md](../SKILL.md). Quarkus 3.40.1.1. Every decision is put to the user; none has a default.

## Contents

- [1. One function per module or one HTTP Lambda with many routes](#1-one-function-per-module-or-one-http-lambda-with-many-routes)
- [2. Shared library modules](#2-shared-library-modules)
- [3. Package taxonomy or existing layout](#3-package-taxonomy-or-existing-layout)
- [4. Mock event server port in multi-module builds](#4-mock-event-server-port-in-multi-module-builds)
- [5. Runtime mode per module](#5-runtime-mode-per-module)

## 1. One function per module or one HTTP Lambda with many routes

Record the answer as an ADR (OpenSpec `design.md` of the change that introduces it).

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| A. One module per function (`functions/<name>`, one `function.zip` each) | Per-Lambda IAM role (rule R01, one IAM role per compute resource: `securing-aws-iam-serverless`), memory, timeout, runtime mode and SnapStart per function | More modules, more `application.properties`; shared code needs a library module with a bean index | Event-driven functions, different permissions or runtime modes per function |
| B. One HTTP Lambda serving many routes (`quarkus-amazon-lambda-http` for an HTTP API or `-rest` for a REST API, one HTTP framework) | One artifact, one role, one memory and timeout; routing stays inside Quarkus REST | One IAM role for every route; one gateway integration timeout (HTTP API 30 s fixed, REST API 29 s default); both extensions are preview; routes cannot differ in runtime mode | Cohesive API with uniform permissions and latency profile |
| C. One module, several `@Named` handlers, several Lambdas from the same build | One build, per-Lambda role, memory and timeout; the handler is chosen by `quarkus.lambda.handler` (env `QUARKUS_LAMBDA_HANDLER` override) | `@Named` beans are unremovable roots, so every handler bean stays in every Lambda; the effect on start time is not stated by any page read (unverified); one runtime mode for the whole `function.zip` | Few small handlers that share most code and the same runtime mode |

- Facts behind the table: the Lambda handler is `QuarkusStreamHandler::handleRequest` and the user handler is selected by `quarkus.lambda.handler` ([aws-lambda guide](https://quarkus.io/version/3.40/guides/aws-lambda)); gateway timeouts and the preview status come from the [HTTP skill](../../developing-quarkus-amazon-lambda-http-v3-40/blueprints/ask-first-decisions.md#c1-http-api-or-rest-api) and [its C4](../../developing-quarkus-amazon-lambda-http-v3-40/blueprints/ask-first-decisions.md#c4-timeout-budget); `@Named` as unremovable root comes from the CDI reference via `refactoring-quarkus-java`.
- Which route belongs to which Lambda for tenant isolation is a security question: `securing-quarkus-lambda-cognito-v3-40` (Option A or B there) must be consistent with this choice.
- Ask: "How many Lambdas, and which routes or events go to which? Do routes need different permissions, memory, timeout or runtime mode? Is an HTTP API or a REST API planned (preview extensions)?"

## 2. Shared library modules

A new library module needs a bean index (`beans.xml`, `jandex.idx` or `quarkus.index-dependency.*`) and may change which tests see the beans ([CDI reference](https://quarkus.io/version/3.40/guides/cdi-reference), via `refactoring-quarkus-java`). Create one only when a second function consumes the code; until then keep it in the function module.

Ask: "Is there a second function that needs this code, and is a separate module worth the indexing and test relocation?"

## 3. Package taxonomy or existing layout

The taxonomy of `refactoring-quarkus-java` is a team convention, not a Quarkus requirement. If the project already has a layout, adopting this one is a migration: do not move files unprompted.

Ask: "Adopt this layout or follow the existing one?"

## 4. Mock event server port in multi-module builds

Test port default 8081, `0` means random ([packaging blueprint](../../developing-quarkus-amazon-lambda-v3-40/blueprints/packaging-and-artifact-contract.md#dev-mode-and-mock-event-server-detail-testing-quarkus-amazon-lambda-v3-40)). Whether two modules built in parallel collide on 8081 is an inference from the fixed port (medium confidence, M2); modules built one after another do not collide. Use the `mock-event-server.*` key names: the guide documents them (https://quarkus.io/version/3.40/guides/aws-lambda), and the start-up code reads only those (medium confidence, from source at tag 3.40.1.1: https://github.com/quarkusio/quarkus/tree/3.40.1.1/extensions/amazon-lambda).

Ask: "Does the build run module tests in parallel? If yes set `quarkus.lambda.mock-event-server.test-port=0` per module."

## 5. Runtime mode per module

JVM, JVM + SnapStart and native are mutually exclusive and are decided per Lambda in [Lambda C1](../../developing-quarkus-amazon-lambda-v3-40/blueprints/ask-first-decisions.md#c1-jvm-snapstart-or-native). In a layout with option B or C one `function.zip` has one mode. Native extras (`src/main/zip.native/`, `quarkus.native.march` for the HTTP extensions) stay in the module that chose native.

Ask: "Which mode per function? Then apply it per module."
