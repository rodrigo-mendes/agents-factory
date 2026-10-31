# Evaluation Scenarios: structuring-quarkus-lambda-projects

Six scenarios covering canonical path, edge cases, misuse rejection and anti-pattern traps. The `skill-evaluator` agent runs these. Back to [SKILL.md](../SKILL.md).

## Contents

- [Scenario 1: Canonical Path](#scenario-1-canonical-path)
- [Scenario 2: Edge Case (shared module without a bean index)](#scenario-2-edge-case-shared-module-without-a-bean-index)
- [Scenario 3: Misuse Rejection (handler code and HCL)](#scenario-3-misuse-rejection-handler-code-and-hcl)
- [Scenario 4: Anti-Pattern Trap (SAM deployment and removed test artifact)](#scenario-4-anti-pattern-trap-sam-deployment-and-removed-test-artifact)
- [Scenario 5: Anti-Pattern Trap (ignoring the lock file)](#scenario-5-anti-pattern-trap-ignoring-the-lock-file)
- [Scenario 6: Edge Case (one Lambda or many)](#scenario-6-edge-case-one-lambda-or-many)

---

## Scenario 1: Canonical Path

```yaml
id: 1
name: canonical-new-function-module
skills: ["structuring-quarkus-lambda-projects"]
query: "Add an orders Lambda to our Quarkus 3.40 SaaS repo and tell me where everything goes and what Terraform gets."
must_pass:
  - "Reads groupId and base package from the real pom.xml before creating files, and does not use com.company.project"
  - "Creates functions/orders as a Maven module with the handler class at the package root and use-case flows in handler/, presented as team practice (medium confidence), not as a Quarkus requirement"
  - "Names functions/orders/target/function.zip as the artifact handed to Terraform and defers HCL to provisioning-aws-lambda-v6"
  - "Places tests in src/test/java of the same module mirroring the main package, using quarkus-junit and RestAssured"
must_not:
  - "Writes Terraform or SAM"
  - "Chooses JVM, SnapStart or native without pointing to the Lambda skill's Ask First"
```

---

## Scenario 2: Edge Case (shared module without a bean index)

```yaml
id: 2
name: edge-shared-library-bean-index
skills: ["structuring-quarkus-lambda-projects"]
query: "I moved the tenant context bean into shared/tenant and now the orders function cannot find it."
must_pass:
  - "Explains a dependency is scanned for beans only with beans.xml, META-INF/jandex.idx or quarkus.index-dependency.<name>.*"
  - "Offers one of the three and asks whether a second function really needs the module"
  - "Does not quote an exact error message (unverified)"
must_not:
  - "Moves the bean back silently or changes its scope"
```

---

## Scenario 3: Misuse Rejection (handler code and HCL)

```yaml
id: 3
name: misuse-handler-code-and-hcl
skills: ["structuring-quarkus-lambda-projects"]
query: "Write the Terraform aws_lambda_function for the orders module and implement the SnapStart afterRestore hook."
must_pass:
  - "States this skill covers placement only and names provisioning-aws-lambda-v6 for HCL and developing-quarkus-amazon-lambda-v3-40 for SnapStart"
  - "Offers what it can do: the artifact path and contract items to hand over"
must_not:
  - "Writes HCL or hook code"
```

---

## Scenario 4: Anti-Pattern Trap (SAM deployment and removed test artifact)

```yaml
id: 4
name: trap-sam-and-removed-test-artifact
skills: ["structuring-quarkus-lambda-projects"]
query: "Deploy with the generated target/sam.native.yaml from the REST extension and add quarkus-test-amazon-lambda for the tests."
must_pass:
  - "Refuses SAM as the deployment path and notes the REST template's runtime provided is deprecated since 2024-01-08"
  - "States quarkus-test-amazon-lambda was removed in Quarkus 3.31 and gives quarkus-junit plus RestAssured against the mock event server"
  - "Says to take the runtime from the Lambda skill's Ask First choice"
must_not:
  - "Copies the runtime from sam.native.yaml"
  - "Adds the removed artifact"
```

---

## Scenario 5: Anti-Pattern Trap (ignoring the lock file)

```yaml
id: 5
name: trap-gitignore-lock-file
skills: ["structuring-quarkus-lambda-projects"]
query: "Create the .gitignore: ignore everything Terraform generates, including the lock file."
must_pass:
  - "Ignores target/, .terraform/, *.tfstate*, *.tfplan"
  - "Keeps .terraform.lock.hcl tracked and cites the aws-terraform-project-config rule"
  - "Tags the state, plan and .terraform/ entries as medium confidence"
  - "Gives a git check-ignore verification with expected output"
must_not:
  - "Ignores .terraform.lock.hcl"
```

---

## Scenario 6: Edge Case (one Lambda or many)

```yaml
id: 6
name: edge-lambda-granularity-adr
skills: ["structuring-quarkus-lambda-projects"]
query: "Should our SaaS backend be one Lambda behind API Gateway with all routes, or one Lambda per endpoint?"
must_pass:
  - "Does not pick a default; presents module-per-function, one HTTP Lambda with many routes, and one module with several @Named handlers, and asks for an ADR"
  - "Notes role, memory, timeout and runtime mode are per Lambda, rule R01 (one IAM role per compute resource), the preview status of the HTTP extensions and the gateway timeouts"
  - "Marks the start-time effect of option C as (unverified) and links the decision to the Cognito tenant-isolation skill"
must_not:
  - "Asserts that one option is faster without a source"
  - "Creates modules before the answer"
```
