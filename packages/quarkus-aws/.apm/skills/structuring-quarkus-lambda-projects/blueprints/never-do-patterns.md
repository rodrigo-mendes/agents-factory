# Never-Do Patterns

Back to [SKILL.md](../SKILL.md). Quarkus 3.40.1.1. Each item has the correct alternative beside it.

## Contents

- [N1. Hardcoded paths and packages (team practice, medium confidence M1)](#n1-hardcoded-paths-and-packages)
- [N2. Two HTTP frameworks in one module](#n2-two-http-frameworks-in-one-module)
- [N3. Deploying from generated SAM files](#n3-deploying-from-generated-sam-files)
- N4: not used (numbering gap kept so N5-N8 ids stay stable)
- [N5. Handler renamed without the property](#n5-handler-renamed-without-the-property)
- [N6. Removed test artifact](#n6-removed-test-artifact)
- [N7. Ignoring the lock file](#n7-ignoring-the-lock-file)
- [N8. Library module without a bean index](#n8-library-module-without-a-bean-index)
- [Team practice T1 (outside the Never Do tier)](#team-practice-t1-handler-inside-a-sub-package)

## N1. Hardcoded paths and packages

Team practice, not a Quarkus or AWS fact (medium confidence, M1 in the register); listed here for the example, not in the SKILL.md Never Do tier.

```text
🚫 WRONG: functions/orders/src/main/java/com/company/project/OrdersLambda.java   (placeholder package)
✅ CORRECT: functions/orders/src/main/java/org/acme/saas/orders/OrdersLambda.java (from the real pom.xml)
```

## N2. Two HTTP frameworks in one module

Source: [HTTP skill](../../developing-quarkus-amazon-lambda-http-v3-40/SKILL.md) ("unexpected conflicts and errors").

```xml
<!-- 🚫 WRONG -->
<artifactId>quarkus-rest</artifactId>
<artifactId>quarkus-reactive-routes</artifactId>
<!-- ✅ CORRECT: one of quarkus-rest, quarkus-reactive-routes, quarkus-undertow -->
```

## N3. Deploying from generated SAM files

```text
🚫 WRONG: sam deploy --template target/sam.jvm.yaml            (reference output; REST sam.native.yaml uses Runtime: provided, deprecated 2024-01-08)
✅ CORRECT: Terraform input = functions/orders/target/function.zip; HCL in provisioning-aws-lambda-v6
```

`sam local invoke --template target/sam.jvm.yaml --event payload.json` as a local smoke test is allowed (needs Docker; [packaging blueprint](../../developing-quarkus-amazon-lambda-v3-40/blueprints/packaging-and-artifact-contract.md)).

## N5. Handler renamed without the property

```java
// 🚫 WRONG: @Named("orders") renamed to @Named("order-api") while application.properties still says
//          quarkus.lambda.handler=orders
// ✅ CORRECT: class name, CDI name and quarkus.lambda.handler (or QUARKUS_LAMBDA_HANDLER) change in one step
```

Source: [aws-lambda guide](https://quarkus.io/guides/aws-lambda) via `refactoring-quarkus-java`.

## N6. Removed test artifact

```xml
<!-- 🚫 WRONG: removed in Quarkus 3.31, last Central version 3.30.8 -->
<artifactId>quarkus-test-amazon-lambda</artifactId>
<!-- ✅ CORRECT: quarkus-junit + RestAssured against the mock event server -->
```

## N7. Ignoring the lock file

```gitignore
# 🚫 WRONG
.terraform.lock.hcl
# ✅ CORRECT: commit .terraform.lock.hcl
```

Impact: provider versions move unreviewed (rule `aws-terraform-project-config`, rule 4). Not committing state, plans or `.terraform/` is standard Terraform practice but no AWS Terraform rule read lists it (medium confidence, M3 in the register).

## N8. Library module without a bean index

```text
🚫 WRONG: shared/tenant has CDI beans, no beans.xml, no jandex.idx, no quarkus.index-dependency.* in the function
          -> the beans are not discovered
✅ CORRECT: add one of the three
```

Source: [CDI reference](https://quarkus.io/version/3.40/guides/cdi-reference) via `refactoring-quarkus-java`. The exact failure message is not recorded (unverified, U2 in the register).

## Team practice T1: handler inside a sub-package

Not a Quarkus or AWS fact and not a Never Do rule (medium confidence, M1 in the register). Follow it in a new repo; in an existing one ask first.

```text
Avoid: .../orders/handler/OrdersLambda.java      (handler/ is for use-case flows)
Prefer: .../orders/OrdersLambda.java  +  .../orders/handler/CreateOrderFlow.java
```
