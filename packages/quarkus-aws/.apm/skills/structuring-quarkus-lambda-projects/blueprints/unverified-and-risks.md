# Unverified Register, Risks and Bibliography

No research of its own: every statement comes from a neighbour skill (researched 2026-10-28 unless noted), a family fact or a repository rule, and keeps their tag. Back to [SKILL.md](../SKILL.md).

## Contents

- [Version-lifetime risk](#version-lifetime-risk)
- [Unverified items](#unverified-items)
- [Medium-confidence items](#medium-confidence-items)
- [Tag to register mapping](#tag-to-register-mapping)
- [Source Bibliography](#source-bibliography)

## Version-lifetime risk

- Quarkus 3.40 LTS released 2026-09-30, community-maintained until 2027-09-30; patch 3.40.1.1 (2026-10-19). Quarkus 4.0.0 is "Upcoming" with no date (High; https://quarkus.io/releases). Reject Quarkus 4 content.
- `quarkus-amazon-lambda-http` and `-rest` are preview: "backward compatibility is not guaranteed" (High; https://quarkus.io/version/3.40/guides/aws-lambda-http). A layout built on them (option B of the Lambda granularity decision) may change on upgrade.
- Quarkiverse 3.23.0 is the only 3.23.x on Central and is built on Quarkus 3.40.0; running it on 3.40.1.1 is not stated on a page (medium confidence; https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-services-parent/3.23.0/quarkus-amazon-services-parent-3.23.0.pom).
- OpenSpec v1.15.0; no v1.15.1+ as of 2026-10-28 (https://github.com/Fission-AI/OpenSpec/releases).
- Terraform targets named here are pointers; they live in the rule `aws-terraform-project-config` (Terraform 1.17+ admitted by `~> 1.16` but not verified there).

## Unverified items

4 unverified items (do not assert them).

| ID | Item | Carried from | Impact and workaround |
|---|---|---|---|
| U1 | Effect on start time and memory of keeping every `@Named` handler bean in each Lambda built from one module (option C); no page read states it | `refactoring-quarkus-java` (`@Named` as unremovable root) and the Lambda guide; the combination is this skill's inference | Measure on a deployed function before choosing option C |
| U2 | Exact failure message and phase when a library module holds beans and has no bean index | `refactoring-quarkus-java` (only the rule is stated) | Do not quote a message; add the index |
| U3 | Handler value for a native build: the guide does not state it | `developing-quarkus-amazon-lambda-v3-40` (packaging blueprint) | Take it from the Lambda skill; do not assert one here |
| U4 | Whether the `java25` runtime identifier is confirmed for a Quarkus 3.40 Lambda; the Lambda skill treats it as an Ask First (C2) | `developing-quarkus-amazon-lambda-v3-40` (Ask First C2) | Prefer `java21` or `java17.al2023`; ask before using `java25` |

## Medium-confidence items

5 medium-confidence items.

| ID | Item | Why medium |
|---|---|---|
| M1 | Directory names `functions/`, `shared/`, `infra/`, module naming, `[Functionality]Lambda` file pattern, the layout tree, handler at the package root, test placement | Team convention; no source skill states a Maven multi-module layout for Quarkus Lambda |
| M2 | Parallel module tests collide on the fixed test port 8081; `test-port=0` avoids it | Inference from the stated default and the stated meaning of `0` (random); the build's parallelism is the user's choice |
| M3 | `.gitignore` entries for `.terraform/`, `*.tfstate*`, `*.tfplan` | Standard Terraform practice; the AWS Terraform rule read states only that `.terraform.lock.hcl` must be committed and not ignored |
| M4 | Pairing a native build with `provisioning`/runtime `provided.al2023` | Inference: the guide does not name the runtime (runtime table: https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html) |
| M5 | Illustrative trees, the example `quarkus.index-dependency.*` keys and the worked example paths | Shapes come from the cited skills; the concrete module names are examples |

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (unverified) start time effect of option C | SKILL.md Ask First; ask-first 1 | U1 |
| (unverified) bean-index failure message | never-do N8 | U2 |
| (medium confidence) team convention for names and layout | SKILL.md header, Repository layout and Quick Reference; assets yml header | M1 |
| (medium confidence) parallel port collision | SKILL.md Ask First; ask-first 4 | M2 |
| (medium confidence) state, plan, `.terraform/` and `target/` ignore entries; not committing state | SKILL.md note under Always Do; always-do 7; never-do N7 | M3 |
| (medium confidence) native pairing with `provided.al2023` | always-do 2 | M4 |
| (medium confidence) illustrative trees and keys | always-do 3, 4; loader notes | M5 |
| (unverified) native handler value not stated by the guide | always-do 2 | U3 |
| (unverified) `java25` runtime | always-do 2; assets yml `jvm_runtimes` comment | U4 |
| (medium confidence) team practice block: handler at package root, test placement, no hardcoded packages or paths | SKILL.md Team practice; always-do 3, 5; never-do N1, T1 | M1 |

## Source Bibliography

All read 2026-10-28 by the source skills; this skill re-fetched nothing.

| # | Source | Used for |
|---|---|---|
| S1 | https://quarkus.io/guides/aws-lambda | build output, handler, `quarkus.lambda.handler`, native `bootstrap`, zip folders |
| S2 | https://quarkus.io/version/3.40/guides/aws-lambda-http | preview status, one HTTP framework, extension per gateway |
| S3 | https://quarkus.io/version/3.40/guides/cdi-reference | bean discovery in dependencies, unremovable roots (via `refactoring-quarkus-java`) |
| S4 | https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html | runtime identifiers (via the Lambda skill) |
| S5 | https://github.com/Fission-AI/OpenSpec | `openspec/` layout |
| S6 | https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/common-features.html | Quarkiverse BOM |
| S7 | https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.31 | removal of `quarkus-test-amazon-lambda` |
| S8 | https://developer.hashicorp.com/terraform/language/files/dependency-lock | commit `.terraform.lock.hcl` (via the rule `aws-terraform-project-config`) |

Neighbour skills used: `developing-quarkus-amazon-lambda-v3-40` (packaging blueprint), `developing-quarkus-amazon-lambda-http-v3-40`, `testing-quarkus-amazon-lambda-v3-40`, `refactoring-quarkus-java` (package taxonomy), `structuring-camel-quarkus-projects` (shape only). Family facts were verified by the orchestrator on 2026-10-28 and are cited by URL above (the family-facts file is provenance only, not shipped). Community sources: none used.
