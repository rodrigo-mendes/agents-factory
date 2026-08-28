# AWS SAM (Serverless Application Model) — Architecture Knowledge Base

---

## Metadata

```yaml
Full_Name: "AWS Serverless Application Model (SAM)"
Cloud_Provider: "AWS"
Architecture_Domain: "SAM — Serverless Infrastructure as Code"
Target_Edition: "AWS SAM 2024 (Transform: AWS::Serverless-2016-10-31, SAM CLI 1.x)"
Architecture_Context: "Serverless application development lifecycle — defining, building, testing, deploying, and managing serverless applications using declarative IaC with CloudFormation extension"
Official_Source_URL: "https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/what-is-sam.html"
Output_Format: Markdown
Primary_Audience: Cloud Architects and Tech Leads
Research_Date: "2026-05-28"
Currency_Threshold: "2027-05-28 — review required after this date due to SAM CLI release velocity and resource type additions"
```

---

## Executive Summary

AWS Serverless Application Model (AWS SAM) is an open-source IaC framework that extends AWS CloudFormation with shorthand syntax specifically designed for serverless application development. SAM consists of two primary components: the **SAM template specification** (an abstract CloudFormation extension using the `Transform: AWS::Serverless-2016-10-31` macro) and the **SAM CLI** (a command-line tool for local development, testing, building, and deploying serverless applications). SAM templates reduce serverless infrastructure code by 5–10x compared to raw CloudFormation — a 23-line SAM template can define what would require 200+ lines of CloudFormation, including Lambda functions, API Gateway endpoints, DynamoDB tables, and IAM permissions.

The 2024 edition of SAM consolidated several architecturally significant capabilities: **SAM Connectors** (`AWS::Serverless::Connector`) for declarative, least-privilege permission composition between resources; **SAM Accelerate** (`sam sync`) for rapid cloud development workflows that bypass full CloudFormation deployments for code changes; **WebSocket API support** (`AWS::Serverless::WebSocketApi`); **GraphQL API support** (`AWS::Serverless::GraphQLApi`); **CapacityProvider** resource for ECS integration; enhanced multi-environment configuration via `samconfig.toml`/`samconfig.yaml` with TOML and YAML format support; and **OIDC authentication** for deployment without long-lived AWS credentials. The SAM CLI now supports local testing with Docker containers, remote invocation of deployed resources (`sam remote invoke`), response streaming for Lambda functions, and integration with Terraform for local Lambda testing.

The three most critical architecture guardrails for SAM-based serverless applications are: (1) **always use SAM Connectors or scoped SAM Policy Templates instead of inline wildcard IAM policies** — SAM's permission abstractions generate least-privilege policies automatically, eliminating the blast radius of overly permissive roles; (2) **always define a `samconfig.toml` with environment-specific configurations** — this ensures deterministic deployments across dev/staging/prod without parameter drift; (3) **never use `sam sync` against production stacks** — SAM Accelerate bypasses CloudFormation change sets and causes drift, making it unsafe for production environments where `sam deploy` with `--confirm-changeset` is mandatory.

---

## Cloud Architecture Glossary

```
Term: SAM Transform
Definition: The CloudFormation macro declaration `Transform: AWS::Serverless-2016-10-31` that identifies a template as an AWS SAM template. During deployment, CloudFormation invokes this transform to expand SAM shorthand syntax into full CloudFormation resource definitions.
Provider Docs Section: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-specification-template-anatomy.html
Architect Usage: Every SAM template must include this Transform declaration. It enables the use of AWS::Serverless::* resource types. Additional transforms (e.g., AWS::LanguageExtensions) must be listed before the serverless transform.
Common Confusion: The transform version "2016-10-31" is the specification version, NOT the year of last update. SAM resources and capabilities are continuously updated independently of this version string.

Term: Globals Section
Definition: A SAM-specific template section (no CloudFormation equivalent) where shared properties for all serverless functions, APIs, HTTP APIs, simple tables, state machines, and capacity providers are declared. Resources inherit these properties unless explicitly overridden.
Provider Docs Section: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-specification-template-anatomy-globals.html
Architect Usage: Use Globals to define shared Runtime, MemorySize, Timeout, Tracing, Environment variables, and Tags across all functions. Reduces template duplication and ensures consistency. Map properties are merged (function-level values extend global maps); scalar properties are replaced (function-level overrides global).
Common Confusion: Not all resource properties can be set in Globals. Only a subset of properties for each resource type are supported. Check the documentation for the supported Globals properties per resource type.

Term: SAM Connector
Definition: An abstract resource type (`AWS::Serverless::Connector`) or embedded resource attribute (`Connectors:`) that declaratively provisions IAM permissions between a source and destination resource. Supports `Read` and `Write` permission types.
Provider Docs Section: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/managing-permissions-connectors.html
Architect Usage: Use Connectors instead of manually writing IAM policies between resources. They automatically compose least-privilege policies for the specific connection. Embedded syntax places `Connectors:` on the source resource referencing destination by `Id`. Standalone syntax uses `AWS::Serverless::Connector` type.
Common Confusion: Connectors only support specific source/destination resource combinations. Not all AWS resource types are supported as sources or destinations — check the supported connections matrix before assuming connector availability.

Term: SAM Policy Template
Definition: Pre-built, parameterized IAM policy templates provided by SAM that grant scoped permissions to Lambda functions. Referenced in the `Policies` property of `AWS::Serverless::Function` using a shorthand name (e.g., `DynamoDBCrudPolicy`, `S3ReadPolicy`, `SQSPollerPolicy`).
Provider Docs Section: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-policy-templates.html
Architect Usage: Always prefer SAM Policy Templates over inline IAM policy documents. They generate least-privilege policies scoped to specific resources. Each template accepts resource ARN parameters, preventing wildcard access.
Common Confusion: SAM Policy Templates are NOT the same as AWS Managed Policies. Policy Templates are SAM-specific abstractions that generate inline policies during transformation. AWS Managed Policies are standalone IAM policies referenced by ARN.

Term: SAM Accelerate (sam sync)
Definition: A development workflow feature of the SAM CLI that syncs local changes to the cloud using the quickest available method — AWS service APIs for code changes (bypassing CloudFormation) or CloudFormation deployments for infrastructure changes. Activated via `sam sync --watch`.
Provider Docs Section: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/using-sam-cli-sync.html
Architect Usage: Use exclusively in development environments. `sam sync` uses direct Lambda API updates for code changes (fast, sub-second sync) but causes CloudFormation drift. Never use against production stacks. The `--watch` flag enables file system monitoring for automatic sync.
Common Confusion: `sam sync` ≠ `sam deploy`. The sync command is for rapid development iteration; deploy is for production-grade CloudFormation deployments with change sets, rollback support, and drift-free state management.

Term: AutoPublishAlias
Definition: A property on `AWS::Serverless::Function` that instructs SAM to automatically detect code changes, publish a new function version, and update a named alias to point to the latest version. Required for gradual deployment via CodeDeploy.
Provider Docs Section: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/automating-updates-to-serverless-apps.html
Architect Usage: Set `AutoPublishAlias: live` (or custom alias name) on functions that require canary/linear deployments. This enables `DeploymentPreference` configuration for traffic shifting. Function invocations must target the alias (not $LATEST) to benefit from gradual rollouts.
Common Confusion: AutoPublishAlias creates a Lambda alias, NOT a Route53 alias. It is unrelated to DNS. The alias is a pointer to a specific Lambda function version enabling traffic-shifting during deployments.

Term: DeploymentPreference
Definition: A property on `AWS::Serverless::Function` that configures gradual deployment using AWS CodeDeploy. Supports Canary, Linear, and AllAtOnce traffic-shifting strategies with optional pre/post-traffic hooks and CloudWatch alarm-based rollback.
Provider Docs Section: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-property-function-deploymentpreference.html
Architect Usage: Configure `Type: Canary10Percent10Minutes` (or similar) for production functions. Define `Alarms` for error rate monitoring and `Hooks` for validation functions. Requires `AutoPublishAlias` to be set. SAM automatically provisions the CodeDeploy application and deployment group.
Common Confusion: DeploymentPreference requires that the function's `AutoPublishAlias` property is configured. Without it, SAM cannot create versions for CodeDeploy to shift traffic between.

Term: samconfig.toml / samconfig.yaml
Definition: A project-level configuration file that stores default parameter values for AWS SAM CLI commands. Supports multiple named environments (e.g., `default`, `prod`, `staging`) with command-specific and global settings.
Provider Docs Section: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-config.html
Architect Usage: Commit samconfig to version control. Define environment-specific blocks (`[default]`, `[prod]`, `[staging]`) with deployment parameters (stack name, region, capabilities, S3 bucket). Use `--config-env` to select environment at deploy time. Prevents parameter drift between environments.
Common Confusion: The samconfig file does NOT replace CloudFormation Parameters. It configures SAM CLI commands, not template parameter values. Template parameters are passed via `parameter_overrides` within samconfig or via `--parameter-overrides` at the command line.

Term: sam local
Definition: A family of SAM CLI subcommands (`sam local invoke`, `sam local start-api`, `sam local start-lambda`, `sam local generate-event`) that simulate the Lambda execution environment locally using Docker containers. Enables local debugging, API testing, and event generation without deploying to AWS.
Provider Docs Section: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/using-sam-cli-local-testing.html
Architect Usage: Use for development and unit testing. `sam local invoke` runs a single function invocation. `sam local start-api` creates a local HTTP server mimicking API Gateway. Requires Docker. Supports custom events, environment variable overrides, and debugger attachment (step-through debugging via IDE).
Common Confusion: `sam local` does NOT replicate all AWS service behaviors. IAM permissions, VPC networking, service integrations (e.g., DynamoDB Streams triggers), and concurrency limits are NOT simulated locally. Use `sam remote invoke` for testing against real AWS infrastructure.

Term: Nested Applications
Definition: SAM's mechanism for composing applications from reusable components by embedding `AWS::Serverless::Application` resources that reference other SAM templates (from local paths, S3, or AWS Serverless Application Repository).
Provider Docs Section: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-template-nested-applications.html
Architect Usage: Use to decompose large serverless architectures into independently deployable modules (e.g., auth stack, API stack, processing stack). Each nested app becomes a CloudFormation nested stack. Pass outputs between stacks using the `GetAtt` intrinsic function.
Common Confusion: Nested applications are deployed as CloudFormation nested stacks, NOT separate CloudFormation stacks. They share the lifecycle of the parent stack. For truly independent lifecycle management, use separate SAM projects deployed as separate stacks with cross-stack references.

Term: sam remote invoke
Definition: A SAM CLI command that invokes deployed AWS resources (Lambda functions, Step Functions state machines, Kinesis streams, SQS queues) directly in the cloud, streaming responses and logs back to the local terminal.
Provider Docs Section: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/using-sam-cli-remote-invoke.html
Architect Usage: Use for integration testing against real AWS infrastructure. Supports Lambda response streaming, custom event payloads, and log tailing. Preferred over `sam local invoke` when testing service integrations, IAM permissions, VPC connectivity, or environment-specific behavior.
Common Confusion: `sam remote invoke` invokes the DEPLOYED resource, not local code. Local code changes must be deployed (via `sam sync` or `sam deploy`) before they can be tested with `sam remote invoke`.
```

---

## Architecture Guardrails

### ✅ Mandatory Patterns

**Use SAM Transform Declaration**
- Pillar Alignment: Operational Excellence — Infrastructure as Code
- Why: The Transform declaration enables CloudFormation to process SAM shorthand syntax, reducing template complexity by 5–10x and eliminating manual resource wiring errors
- AWS Services: AWS CloudFormation (Transform macro), AWS SAM specification
- Architecture Decision:
  Every SAM template MUST begin with `Transform: AWS::Serverless-2016-10-31`. When combining with other transforms (e.g., `AWS::LanguageExtensions`), declare them as a list with LanguageExtensions FIRST:
  ```yaml
  Transform:
    - AWS::LanguageExtensions
    - AWS::Serverless-2016-10-31
  ```
- Verification:
  Run `sam validate` to verify template syntax. Run `sam build` to confirm the template can be processed. Check CloudFormation console → Stack → Template tab to verify transform expansion.
- Source: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-specification-template-anatomy.html

---

**Use SAM Connectors or Policy Templates for IAM Permissions**
- Pillar Alignment: Security — Least-Privilege Access
- Why: SAM Connectors and Policy Templates automatically generate scoped IAM policies, eliminating wildcard permissions and reducing blast radius. Manual IAM policies in serverless templates are the #1 source of over-privileged functions.
- AWS Services: AWS IAM, AWS SAM Connectors (`AWS::Serverless::Connector`), SAM Policy Templates
- Architecture Decision:
  Use embedded Connectors for inter-resource permissions:
  ```yaml
  Resources:
    ProcessOrderFunction:
      Type: AWS::Serverless::Function
      Connectors:
        OrderTableConn:
          Properties:
            Destination:
              Id: OrdersTable
            Permissions:
              - Read
              - Write
      Properties:
        Handler: src/process-order.handler
        Runtime: nodejs20.x
    OrdersTable:
      Type: AWS::Serverless::SimpleTable
  ```
  Use Policy Templates for service-specific access:
  ```yaml
  Properties:
    Policies:
      - DynamoDBCrudPolicy:
          TableName: !Ref OrdersTable
      - SQSPollerPolicy:
          QueueName: !GetAtt OrderQueue.QueueName
  ```
- Verification:
  After deployment, inspect the generated IAM role in IAM Console → Roles → `{StackName}-{FunctionLogicalId}Role-*`. Verify no wildcard `*` in Actions or Resources. Use `sam validate` with `--lint` to catch policy issues pre-deployment.
- Source: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/managing-permissions-connectors.html

---

**Define samconfig with Environment-Specific Configurations**
- Pillar Alignment: Operational Excellence — Reproducible Deployments
- Why: A committed samconfig file ensures deterministic deployments across environments, prevents parameter drift, and encodes deployment decisions (region, capabilities, stack name) as version-controlled configuration.
- AWS Services: AWS SAM CLI, AWS CloudFormation
- Architecture Decision:
  Create `samconfig.toml` at project root with environment-specific blocks:
  ```toml
  version = 0.1

  [default]
  [default.global.parameters]
  stack_name = "myapp-dev"
  region = "us-east-1"

  [default.build.parameters]
  cached = true
  parallel = true

  [default.deploy.parameters]
  capabilities = "CAPABILITY_IAM"
  confirm_changeset = true
  resolve_s3 = true

  [prod]
  [prod.global.parameters]
  stack_name = "myapp-prod"
  region = "us-east-1"

  [prod.deploy.parameters]
  capabilities = "CAPABILITY_IAM"
  confirm_changeset = true
  fail_on_empty_changeset = false
  ```
  Deploy to specific environments: `sam deploy --config-env prod`
- Verification:
  Verify file exists at project root alongside `template.yaml`. Confirm all environments match expected deployment targets. Verify `confirm_changeset = true` is set for production environments.
- Source: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-config.html

---

**Use Globals Section for Shared Function Configuration**
- Pillar Alignment: Operational Excellence — Consistency, Reliability — Uniform Configuration
- Why: The Globals section eliminates configuration drift between functions by declaring shared properties once. Without it, divergent timeout, memory, or runtime settings across functions create inconsistent behavior and debugging complexity.
- AWS Services: AWS Lambda, Amazon API Gateway
- Architecture Decision:
  Define consistent defaults for all functions in the Globals section:
  ```yaml
  Globals:
    Function:
      Runtime: nodejs20.x
      MemorySize: 256
      Timeout: 30
      Tracing: Active
      Environment:
        Variables:
          ENVIRONMENT: !Ref Environment
          LOG_LEVEL: INFO
      Tags:
        project: myapp
        managed-by: sam
    Api:
      TracingEnabled: true
      Cors:
        AllowOrigin: "'*'"
        AllowMethods: "'GET,POST,PUT,DELETE,OPTIONS'"
        AllowHeaders: "'Content-Type,Authorization'"
  ```
  Override at the function level only when a specific function requires different settings.
- Verification:
  After deployment, inspect Lambda functions in the Console to verify Runtime, MemorySize, Timeout, and Environment variables match expected Globals. Use `sam validate` to catch schema errors.
- Source: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-specification-template-anatomy-globals.html

---

**Configure Gradual Deployments for Production Functions**
- Pillar Alignment: Reliability — Safe Deployments, Operational Excellence — Change Management
- Why: All-at-once Lambda deployments to production risk immediate, full-traffic impact if a bug is introduced. Gradual deployments with canary/linear traffic shifting and automated rollback via CloudWatch alarms limit blast radius.
- AWS Services: AWS Lambda, AWS CodeDeploy, Amazon CloudWatch
- Architecture Decision:
  ```yaml
  Resources:
    PaymentFunction:
      Type: AWS::Serverless::Function
      Properties:
        Handler: src/payment.handler
        Runtime: nodejs20.x
        AutoPublishAlias: live
        DeploymentPreference:
          Type: Canary10Percent10Minutes
          Alarms:
            - !Ref PaymentFunctionErrorAlarm
            - !Ref PaymentFunctionLatencyAlarm
          Hooks:
            PreTraffic: !Ref PreTrafficValidation
            PostTraffic: !Ref PostTrafficValidation

    PaymentFunctionErrorAlarm:
      Type: AWS::CloudWatch::Alarm
      Properties:
        MetricName: Errors
        Namespace: AWS/Lambda
        Statistic: Sum
        Period: 60
        EvaluationPeriods: 1
        Threshold: 1
        ComparisonOperator: GreaterThanOrEqualToThreshold
        Dimensions:
          - Name: FunctionName
            Value: !Ref PaymentFunction
          - Name: Resource
            Value: !Sub "${PaymentFunction}:live"
  ```
- Verification:
  After deployment, check CodeDeploy Console → Applications → `ServerlessDeploymentApplication-*`. Verify deployment group exists with correct alarm configuration. Simulate a failure to confirm automatic rollback triggers.
- Source: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/automating-updates-to-serverless-apps.html

---

**Validate Templates Before Deployment**
- Pillar Alignment: Operational Excellence — Pre-Deployment Validation
- Why: Template syntax errors, invalid resource properties, and misconfigured permissions discovered at deploy time waste CI/CD cycles and risk partial stack failures. Pre-deployment validation catches these errors locally.
- AWS Services: AWS SAM CLI, AWS CloudFormation Linter (cfn-lint)
- Architecture Decision:
  Include validation in every CI pipeline and local development workflow:
  ```bash
  # Validate SAM template syntax
  sam validate --lint

  # Build to verify code can be packaged
  sam build

  # Optional: Run cfn-lint for deeper CloudFormation validation
  cfn-lint template.yaml
  ```
  Integrate `sam validate --lint` as a pre-commit hook or CI gate.
- Verification:
  Run `sam validate --lint` against the template. Zero errors should be returned. If using cfn-lint, verify no E-level (error) findings.
- Source: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-cli-command-reference-sam-validate.html

---

### ⚠️ Architectural Decisions

**IaC Tool Selection: SAM vs CDK vs CloudFormation vs Terraform**
- Options:

  | Option | AWS Service/Tool | Optimizes | Sacrifices | Best When |
  |--------|-----------------|-----------|------------|-----------|
  | AWS SAM | SAM CLI + CloudFormation Transform | Developer velocity for serverless, local testing, minimal code | Flexibility for non-serverless resources, programmatic logic | Purely or primarily serverless workloads, team prefers declarative YAML |
  | AWS CDK | CDK CLI + CloudFormation | Type safety, programmatic composition, reusable constructs, full AWS resource coverage | Simplicity for small serverless projects, YAML readability | Complex architectures mixing serverless with non-serverless, teams proficient in TypeScript/Python/Java |
  | Raw CloudFormation | CloudFormation CLI/Console | Full control, no abstraction layers, maximum explicitness | Development speed for serverless, template verbosity | Enterprise governance requiring explicit resource definitions, non-serverless workloads |
  | Terraform | Terraform CLI | Multi-cloud portability, mature state management, large ecosystem | AWS-native integration depth, local Lambda testing (limited SAM CLI support) | Multi-cloud strategy, existing Terraform investment, team prefers HCL |

- Cost Profile: All options are free tooling. CloudFormation has no deployment charges. CDK and SAM add no additional costs beyond CloudFormation. Terraform may require Terraform Cloud for team state management ($).
- Lock-in Assessment: SAM and CDK lock into CloudFormation as the deployment engine. Terraform maintains portability but sacrifices SAM's local testing and Connector abstractions. SAM templates can include raw CloudFormation resources, reducing lock-in risk.
- Architect Instruction: "Ask which IaC tool the team currently uses when the project includes both serverless and non-serverless resources, or when multi-cloud is a requirement."
- Source: https://docs.aws.amazon.com/prescriptive-guidance/latest/choose-iac-tool/aws-sam.html

---

**API Type: REST API vs HTTP API**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|------------|-----------|------------|-----------|
  | `AWS::Serverless::Api` (REST API) | API Gateway REST API | Feature richness (request validation, WAF, usage plans, API keys, caching, request/response transformations) | Cost (3.5x more expensive), latency (slightly higher) | Enterprise APIs requiring throttling per client, request transformation, WAF protection, or API key-based access control |
  | `AWS::Serverless::HttpApi` (HTTP API) | API Gateway HTTP API | Cost (70% cheaper), latency (lower), simplicity, JWT authorizer built-in | No WAF integration, no usage plans, no API keys, no caching, limited request validation | Internal APIs, microservice-to-microservice communication, JWT-authenticated modern apps, cost-sensitive workloads |

- Cost Profile: HTTP API at ~$1.00/million requests vs REST API at ~$3.50/million requests. HTTP API is the clear default for cost optimization.
- Lock-in Assessment: Both are API Gateway. Migration between them requires template changes (different SAM resource types and event source configurations) but no application code changes.
- Architect Instruction: "Ask which API type to use when the application requires WAF integration, API key management, or request/response transformation. Default to HttpApi otherwise."
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html

---

**Deployment Strategy: sam deploy vs sam sync vs CI/CD Pipeline**
- Options:

  | Option | Mechanism | Optimizes | Sacrifices | Best When |
  |--------|-----------|-----------|------------|-----------|
  | `sam sync --watch` | Direct AWS API + CloudFormation (hybrid) | Development speed, sub-second code sync, automatic change detection | Safety (causes drift), auditability, rollback | Local development and rapid iteration against a dev stack |
  | `sam deploy --guided` | Full CloudFormation change set | Safety, change visibility, rollback support, drift-free | Deployment speed (minutes per deployment) | Staging/production deployments, manual releases |
  | `sam pipeline init` + CI/CD | CodePipeline/GitHub Actions/GitLab CI | Automation, consistency, approval gates, multi-environment promotion | Initial setup complexity, pipeline maintenance | Production environments, team collaboration, audit trails |

- Cost Profile: `sam sync` and `sam deploy` cost nothing beyond CloudFormation/resource costs. CI/CD pipelines add CodePipeline/CodeBuild costs (~$1/pipeline/month + build minutes).
- Lock-in Assessment: `sam deploy` uses standard CloudFormation. CI/CD pipelines can use any system (GitHub Actions, GitLab CI, Jenkins) — SAM is not locked to AWS CI/CD services.
- Architect Instruction: "Ask whether this stack targets development, staging, or production before recommending a deployment strategy. Never recommend `sam sync` for production."
- Source: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-deploying.html

---

**Traffic Shifting Strategy: Canary vs Linear vs AllAtOnce**
- Options:

  | Option | Traffic Pattern | Optimizes | Sacrifices | Best When |
  |--------|----------------|-----------|------------|-----------|
  | `Canary10Percent10Minutes` | 10% immediately → 100% after 10 min | Fast validation with limited blast radius | Full deployment speed (10 min minimum) | Functions with clear error signals (error rate, latency) |
  | `Linear10PercentEvery1Minute` | 10% increments every 1 min | Gradual rollout with progressive confidence | Total deployment time (10 min to full) | High-traffic functions where gradual observation is valuable |
  | `AllAtOnce` | 100% immediately | Deployment speed | Safety (full traffic impact on failure) | Non-critical functions, internal tools, or when pre-traffic hook provides sufficient validation |

- Cost Profile: CodeDeploy is free for Lambda deployments. Canary/Linear add deployment duration (alarm evaluation windows) but no $ cost.
- Lock-in Assessment: Requires `AutoPublishAlias` + `DeploymentPreference`. Removing gradual deployments is a template change only.
- Architect Instruction: "Ask what RTO/blast radius tolerance exists for this function before selecting a deployment preference type."
- Source: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/automating-updates-to-serverless-apps.html

---

**Template Organization: Monolith vs Nested Applications vs Separate Stacks**
- Options:

  | Option | Mechanism | Optimizes | Sacrifices | Best When |
  |--------|-----------|-----------|------------|-----------|
  | Single template | One `template.yaml` | Simplicity, single deployment unit, easy cross-resource references | Blast radius (all-or-nothing deploys), template size limits (1MB), team collaboration | Small applications (< 20 resources), single-team ownership |
  | Nested Applications | `AWS::Serverless::Application` referencing child templates | Modularity, component reuse, logical separation | Shared lifecycle (parent stack controls child), debugging complexity, nested stack limits (500 resources total) | Medium applications (20–100 resources), shared component libraries |
  | Separate Stacks | Independent SAM projects with cross-stack references (`Fn::ImportValue`) | Independent lifecycles, team autonomy, blast radius isolation, no size limits per stack | Cross-stack dependency management, eventual consistency on outputs, deployment ordering | Large applications (100+ resources), multi-team ownership, independently scalable domains |

- Cost Profile: No cost difference — all deploy via CloudFormation.
- Lock-in Assessment: All approaches use CloudFormation. Migration between them requires restructuring templates but not application code.
- Architect Instruction: "Ask how many teams own this application and whether components have independent release cadences before recommending template organization."
- Source: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-template-nested-applications.html

---

### 🚫 Anti-Patterns

**Using `sam sync` Against Production Stacks**
- Risk Level: CRITICAL
- Why: `sam sync` uses direct AWS service APIs (Lambda UpdateFunctionCode) to bypass CloudFormation, causing infrastructure drift. The deployed state no longer matches the CloudFormation template, breaking rollback capability, drift detection, and change auditability. Violates Operational Excellence pillar — "Make frequent, small, reversible changes."
- Instead:
  Use `sam deploy --confirm-changeset` for production deployments. Configure CI/CD pipelines with `sam pipeline init` for automated, auditable deployments with approval gates.
- Detection:
  CloudFormation Console → Stack → Drift detection. If drift is detected on Lambda function code or configuration, `sam sync` was likely used. Also check: SAM CLI prompts "The sync command should only be used against a development stack" — if this was bypassed, production drift exists.
- Impact: Deployment rollback failure | Silent configuration drift | Audit trail gaps | Compliance violation
- Source: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/using-sam-cli-sync.html

---

**Inline Wildcard IAM Policies in SAM Templates**
- Risk Level: CRITICAL
- Why: Defining inline IAM policies with `Action: "*"` or `Resource: "*"` on Lambda functions violates least-privilege and expands blast radius. A compromised function with wildcard permissions can access any resource in the account. SAM provides Connectors and Policy Templates specifically to avoid this. Violates Security pillar — "Apply least-privilege access."
- Instead:
  Use SAM Connectors for inter-resource permissions:
  ```yaml
  Connectors:
    MyConn:
      Properties:
        Destination:
          Id: MyTable
        Permissions:
          - Read
          - Write
  ```
  Use SAM Policy Templates for service access:
  ```yaml
  Policies:
    - DynamoDBCrudPolicy:
        TableName: !Ref MyTable
  ```
- Detection:
  Run `sam validate --lint`. Search template for `"*"` in Policy Action/Resource fields. Use IAM Access Analyzer to evaluate deployed policies.
- Impact: Data breach | Privilege escalation | Lateral movement | Compliance violation
- Source: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-policy-templates.html

---

**Deploying Without `confirm_changeset` in Production**
- Risk Level: HIGH
- Why: Without change set confirmation, `sam deploy` immediately applies all changes including potentially destructive operations (resource replacements, deletions). The operator has no opportunity to review what will change before execution. Violates Operational Excellence pillar — "Anticipate failure."
- Instead:
  Always set `confirm_changeset = true` in samconfig for production environments:
  ```toml
  [prod.deploy.parameters]
  confirm_changeset = true
  ```
  Or use `sam deploy --confirm-changeset` explicitly.
- Detection:
  Review `samconfig.toml` for production environment blocks. Verify `confirm_changeset = true` is set. In CI/CD pipelines, verify the deploy step includes `--confirm-changeset` or has a manual approval gate.
- Impact: Accidental resource deletion | Service outage | Data loss from unreviewed replacements
- Source: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-cli-command-reference-sam-deploy.html

---

**Hardcoding AWS Account IDs, Regions, or Secrets in Templates**
- Risk Level: HIGH
- Why: Hardcoded values make templates non-portable across environments, expose sensitive information in version control, and violate the 12-factor app principle of externalizing configuration. Violates Security pillar and Operational Excellence pillar.
- Instead:
  Use CloudFormation Parameters, pseudo-parameters, and dynamic references:
  ```yaml
  Parameters:
    Environment:
      Type: String
      AllowedValues: [dev, staging, prod]

  Resources:
    MyFunction:
      Type: AWS::Serverless::Function
      Properties:
        Environment:
          Variables:
            ACCOUNT_ID: !Ref AWS::AccountId
            REGION: !Ref AWS::Region
            SECRET_ARN: !Sub "arn:aws:secretsmanager:${AWS::Region}:${AWS::AccountId}:secret:myapp/${Environment}/db-credentials"
  ```
  Pass environment-specific values via `parameter_overrides` in samconfig.
- Detection:
  Search template for 12-digit numbers (account IDs), `us-east-1`/`eu-west-1` (hardcoded regions), or any string resembling API keys/passwords. Use `git-secrets` or similar tools in pre-commit hooks.
- Impact: Secret exposure | Environment coupling | Failed cross-account deployments | Compliance violation
- Source: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/best-practices.html

---

**Using `$LATEST` for Production Function Invocations**
- Risk Level: HIGH
- Why: Invoking `$LATEST` in production means any deployment immediately receives 100% traffic with no rollback path. It makes gradual deployments impossible and prevents consistent behavior during deployments (a request mid-deployment could hit either old or new code). Violates Reliability pillar — "Manage change in automation with safe deployments."
- Instead:
  Configure `AutoPublishAlias` to create a stable alias pointing to versioned code:
  ```yaml
  Properties:
    AutoPublishAlias: live
    DeploymentPreference:
      Type: Canary10Percent10Minutes
  ```
  All production invocations (API Gateway, EventBridge, Step Functions) should target the alias, not `$LATEST`.
- Detection:
  Check API Gateway integrations — if the Lambda integration URI does not include a qualifier (`:live` or version number), it invokes `$LATEST`. Check EventBridge rules, SNS subscriptions, and Step Functions for unqualified function ARNs.
- Impact: Service instability during deployments | No rollback capability | Inconsistent behavior
- Source: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/automating-updates-to-serverless-apps.html

---

**Skipping `sam build` Before Deployment**
- Risk Level: MEDIUM
- Why: Deploying directly without `sam build` risks uploading stale artifacts, unresolved dependencies, or platform-incompatible binaries (e.g., building Python C extensions on macOS for Lambda's Amazon Linux). `sam build` resolves dependencies, compiles code, and creates the correct deployment artifact structure.
- Instead:
  Always run `sam build` (or `sam build --use-container` for platform-specific dependencies) before `sam deploy`:
  ```bash
  sam build --cached --parallel
  sam deploy --config-env prod
  ```
  For native dependencies (C extensions, compiled languages), use container builds:
  ```bash
  sam build --use-container
  ```
- Detection:
  Check CI pipeline definition — verify `sam build` step exists before `sam deploy`. If Lambda functions fail with import errors or binary incompatibilities, `sam build` was likely skipped or run without `--use-container`.
- Impact: Deployment with missing dependencies | Runtime import errors | Platform-incompatible binaries | Stale code in production
- Source: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-building.html

---

## Cloud-Native Design Patterns

**Event-Driven Serverless API Pattern**
- Category: Communication
- Problem: Building a scalable REST/HTTP API that handles varying request loads without provisioning or managing servers, with minimal infrastructure definition.
- Solution on AWS:
  ```yaml
  Transform: AWS::Serverless-2016-10-31
  Globals:
    Function:
      Runtime: nodejs20.x
      MemorySize: 256
      Timeout: 30
      Tracing: Active

  Resources:
    GetItemsFunction:
      Type: AWS::Serverless::Function
      Properties:
        Handler: src/handlers/get-items.handler
        Events:
          GetItems:
            Type: HttpApi
            Properties:
              Path: /items
              Method: GET
      Connectors:
        ItemsTableConn:
          Properties:
            Destination:
              Id: ItemsTable
            Permissions:
              - Read

    ItemsTable:
      Type: AWS::Serverless::SimpleTable
  ```
  SAM automatically provisions: Lambda function, HTTP API endpoint, API Gateway integration, Lambda permission, and IAM role with DynamoDB read access.
- Services Used: API Gateway (HTTP API), Lambda, DynamoDB, IAM
- When to Apply: CRUD APIs, microservice endpoints, webhook receivers, BFF (Backend for Frontend) layers
- When NOT to Apply: Long-running connections (WebSocket preferred), sub-10ms latency requirements (cold starts), binary payload processing (API Gateway 10MB limit)
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Operational | Zero server management, auto-scaling, pay-per-request | Cold start latency (100ms–5s), API Gateway limits (10MB payload, 30s timeout) |
  | Cost | $0 at zero traffic, linear scaling cost | Per-request pricing more expensive than EC2 at sustained high volume (>1M req/day) |
  | Development | 23 lines of SAM to full API | Local testing limitations, debugging distributed requests across services |

- Complements: DynamoDB single-table design, Lambda Powertools, CloudWatch structured logging
- Source: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/what-is-sam-overview.html

---

**Asynchronous Event Processing Pattern**
- Category: Resilience / Scalability
- Problem: Processing events from multiple sources (S3 uploads, SQS messages, EventBridge events) reliably with automatic retry, dead-letter handling, and backpressure management.
- Solution on AWS:
  ```yaml
  Resources:
    ProcessUploadFunction:
      Type: AWS::Serverless::Function
      Properties:
        Handler: src/process-upload.handler
        Runtime: python3.12
        Timeout: 300
        Events:
          S3Upload:
            Type: S3
            Properties:
              Bucket: !Ref UploadBucket
              Events: s3:ObjectCreated:*
              Filter:
                S3Key:
                  Rules:
                    - Name: prefix
                      Value: uploads/
        EventInvokeConfig:
          MaximumRetryAttempts: 2
          DestinationConfig:
            OnFailure:
              Type: SQS
              Destination: !GetAtt DeadLetterQueue.Arn

    UploadBucket:
      Type: AWS::S3::Bucket

    DeadLetterQueue:
      Type: AWS::SQS::Queue
      Properties:
        MessageRetentionPeriod: 1209600  # 14 days
  ```
- Services Used: Lambda, S3, SQS (DLQ), EventBridge (optional)
- When to Apply: File processing, image/video transformation, data ETL, notification dispatch, event-driven workflows
- When NOT to Apply: Synchronous request-response patterns, sub-second processing requirements
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Reliability | Automatic retries, DLQ for failed events, eventual delivery guarantee | Eventual consistency, retry storms on systematic failures |
  | Scalability | Automatic concurrency scaling, no queue consumer management | Concurrency limits may throttle during spikes (configure reserved concurrency) |
  | Observability | EventInvokeConfig destinations provide success/failure routing | Debugging async flows requires distributed tracing (X-Ray) |

- Complements: Lambda Dead Letter Queues, EventBridge event buses, Step Functions for orchestration
- Source: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-property-function-eventsource.html

---

**Queue-Based Load Leveling Pattern**
- Category: Scalability / Resilience
- Problem: Protecting downstream services from traffic spikes by buffering requests through a queue, processing at a controlled rate with batch processing and partial failure handling.
- Solution on AWS:
  ```yaml
  Resources:
    OrderQueue:
      Type: AWS::SQS::Queue
      Properties:
        VisibilityTimeout: 180  # 6x function timeout
        RedrivePolicy:
          deadLetterTargetArn: !GetAtt OrderDLQ.Arn
          maxReceiveCount: 3

    OrderDLQ:
      Type: AWS::SQS::Queue
      Properties:
        MessageRetentionPeriod: 1209600

    ProcessOrderFunction:
      Type: AWS::Serverless::Function
      Properties:
        Handler: src/process-order.handler
        Runtime: nodejs20.x
        Timeout: 30
        ReservedConcurrentExecutions: 10  # Rate-limit downstream calls
        Events:
          OrderQueueEvent:
            Type: SQS
            Properties:
              Queue: !GetAtt OrderQueue.Arn
              BatchSize: 10
              MaximumBatchingWindowSeconds: 5
              FunctionResponseTypes:
                - ReportBatchItemFailures
  ```
- Services Used: SQS, Lambda (Event Source Mapping), SQS (DLQ)
- When to Apply: Order processing, payment processing, external API calls with rate limits, database write buffering
- When NOT to Apply: Real-time synchronous responses required, message ordering critical (use FIFO queue variant)
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Resilience | Buffering absorbs spikes, DLQ captures failures, batch retry with bisect | Added latency (buffering window), eventual consistency |
  | Scalability | ReservedConcurrentExecutions controls downstream rate | Manual tuning of batch size, concurrency, and visibility timeout |
  | Cost | SQS $0.40/million requests, Lambda per-invocation | Additional queue infrastructure, DLQ monitoring overhead |

- Complements: ReportBatchItemFailures for partial batch success, SQS FIFO for ordering, Step Functions for complex orchestration
- Source: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-property-function-sqs.html

---

**Scheduled Task Pattern**
- Category: Scalability
- Problem: Running periodic tasks (cleanup jobs, report generation, health checks) without managing cron servers, ensuring exactly-once execution per schedule window.
- Solution on AWS:
  ```yaml
  Resources:
    DailyReportFunction:
      Type: AWS::Serverless::Function
      Properties:
        Handler: src/daily-report.handler
        Runtime: python3.12
        Timeout: 900
        MemorySize: 1024
        Events:
          DailySchedule:
            Type: ScheduleV2
            Properties:
              ScheduleExpression: "cron(0 8 * * ? *)"
              ScheduleExpressionTimezone: "America/Sao_Paulo"
              RetryPolicy:
                MaximumRetryAttempts: 2
                MaximumEventAgeInSeconds: 3600
  ```
- Services Used: EventBridge Scheduler, Lambda
- When to Apply: Report generation, data cleanup, health checks, scheduled notifications, batch processing triggers
- When NOT to Apply: Sub-minute scheduling (minimum 1-minute granularity), tasks requiring guaranteed completion (use Step Functions)
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Operational | No cron server management, automatic retry | Lambda 15-minute timeout limits job duration |
  | Reliability | EventBridge Scheduler guarantees at-least-once delivery | No built-in distributed lock (use DynamoDB conditional writes for idempotency) |

- Complements: Step Functions for long-running jobs, DynamoDB for execution state tracking
- Source: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-property-function-schedulev2.html

---

## Security Architecture

**IAM Permission Management via SAM Abstractions**
- AWS Services: IAM (auto-generated roles/policies), SAM Connectors, SAM Policy Templates
- Architecture:
  SAM provides three layers of permission management, from most abstract to most explicit:
  1. **Connectors** (highest abstraction): Declare intent (`Read`/`Write` between resources) → SAM generates scoped IAM policies
  2. **Policy Templates** (medium abstraction): Reference pre-built, parameterized policies by name → SAM generates inline policies
  3. **Inline Policies** (lowest abstraction): Write raw IAM policy documents → SAM attaches to the function's execution role

  Always prefer the highest applicable abstraction. Fall back to inline policies only when Connectors/Policy Templates don't cover the specific service or permission pattern.
- Compliance Alignment: SOC2 CC6.1 (Logical and Physical Access Controls), AWS Well-Architected Security Pillar SEC3 (Manage permissions)
- Source: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-permissions.html

---

**Secrets and Configuration Management**
- AWS Services: AWS Secrets Manager, AWS Systems Manager Parameter Store, Lambda Environment Variables
- Architecture:
  ```yaml
  Resources:
    MyFunction:
      Type: AWS::Serverless::Function
      Properties:
        Environment:
          Variables:
            # Non-sensitive config: direct value or parameter reference
            TABLE_NAME: !Ref ItemsTable
            ENVIRONMENT: !Ref Environment
            # Sensitive config: dynamic reference to Secrets Manager
            DB_SECRET_ARN: !Sub "arn:aws:secretsmanager:${AWS::Region}:${AWS::AccountId}:secret:${Environment}/db-creds"
        Policies:
          - AWSSecretsManagerGetSecretValuePolicy:
              SecretArn: !Sub "arn:aws:secretsmanager:${AWS::Region}:${AWS::AccountId}:secret:${Environment}/db-creds-*"
  ```
  **Rules**:
  - Never store secrets in environment variables directly
  - Pass secret ARN/name via environment variable, resolve at runtime via SDK
  - Use SAM Policy Template `AWSSecretsManagerGetSecretValuePolicy` for scoped access
  - Use Parameter Store for non-sensitive configuration (feature flags, endpoints)
- Compliance Alignment: SOC2 CC6.6 (System Boundaries), PCI-DSS Requirement 3 (Protect Cardholder Data)
- Source: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-policy-templates.html

---

**API Authorization Patterns**
- AWS Services: Amazon Cognito, API Gateway (JWT Authorizer, Lambda Authorizer, IAM Authorization)
- Architecture:
  ```yaml
  Resources:
    MyApi:
      Type: AWS::Serverless::HttpApi
      Properties:
        Auth:
          DefaultAuthorizer: MyCognitoAuth
          Authorizers:
            MyCognitoAuth:
              AuthorizationScopes:
                - openid
                - profile
              IdentitySource: $request.header.Authorization
              JwtConfiguration:
                issuer: !Sub "https://cognito-idp.${AWS::Region}.amazonaws.com/${UserPool}"
                audience:
                  - !Ref UserPoolClient

    PublicFunction:
      Type: AWS::Serverless::Function
      Properties:
        Events:
          Public:
            Type: HttpApi
            Properties:
              ApiId: !Ref MyApi
              Path: /public
              Method: GET
              Auth:
                Authorizer: NONE  # Override default auth for public endpoints
  ```
  **Decision**:
  - Use JWT authorizer (HTTP API) for standard OAuth2/OIDC flows — simplest, lowest latency
  - Use Lambda authorizer for custom auth logic (API keys, legacy tokens, IP whitelisting)
  - Use IAM authorization for service-to-service calls (SigV4)
- Compliance Alignment: SOC2 CC6.1, OWASP API Security Top 10 (API2:2023 Broken Authentication)
- Source: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-property-httpapi-httpapiauth.html

---

## Operational Patterns

**Local Development and Testing Workflow**
- Operational Domain: Change Management / Testing
- AWS Services: SAM CLI (`sam local invoke`, `sam local start-api`, `sam local generate-event`), Docker
- Architecture:
  Development workflow leveraging SAM CLI local testing:
  ```bash
  # 1. Initialize project
  sam init --runtime python3.12 --app-template hello-world

  # 2. Generate test events
  sam local generate-event apigateway http-api-proxy > events/api-event.json

  # 3. Invoke function locally with event
  sam local invoke GetItemsFunction --event events/api-event.json --env-vars env.json

  # 4. Start local API for integration testing
  sam local start-api --warm-containers EAGER --port 3000

  # 5. Sync to dev environment for cloud testing
  sam sync --watch --stack-name myapp-dev
  ```
  **Key configuration** (`env.json` for local environment variables):
  ```json
  {
    "GetItemsFunction": {
      "TABLE_NAME": "local-items-table",
      "ENVIRONMENT": "local",
      "LOG_LEVEL": "DEBUG"
    }
  }
  ```
- Cost Profile: Zero AWS cost for local testing (Docker only). `sam sync` incurs standard resource costs.
- Automation: Add `sam local invoke` with test events to CI pipeline as integration tests. Use `sam build --cached` to speed up incremental builds.
- Source: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/using-sam-cli-local-testing.html

---

**CI/CD Pipeline Pattern**
- Operational Domain: Change Management
- AWS Services: SAM CLI (`sam pipeline init`), CodePipeline, CodeBuild, CloudFormation, S3
- Architecture:
  SAM-native CI/CD pipeline structure:
  ```bash
  # Initialize pipeline configuration
  sam pipeline init --bootstrap

  # Generated pipeline stages:
  # 1. Source (GitHub/CodeCommit trigger)
  # 2. Build (sam build)
  # 3. Test (sam local invoke with test events, unit tests)
  # 4. Deploy to Staging (sam deploy --config-env staging --no-confirm-changeset)
  # 5. Integration Tests against Staging
  # 6. Manual Approval Gate
  # 7. Deploy to Production (sam deploy --config-env prod --confirm-changeset)
  ```
  **samconfig.toml for multi-environment CI/CD**:
  ```toml
  version = 0.1

  [default.global.parameters]
  stack_name = "myapp-dev"

  [staging.global.parameters]
  stack_name = "myapp-staging"

  [staging.deploy.parameters]
  capabilities = "CAPABILITY_IAM"
  confirm_changeset = false
  resolve_s3 = true
  parameter_overrides = "Environment=staging"

  [prod.global.parameters]
  stack_name = "myapp-prod"

  [prod.deploy.parameters]
  capabilities = "CAPABILITY_IAM"
  confirm_changeset = true
  resolve_s3 = true
  fail_on_empty_changeset = false
  parameter_overrides = "Environment=prod"
  ```
- Cost Profile: Low — CodePipeline ~$1/pipeline/month, CodeBuild ~$0.005/build-minute
- Automation: `sam pipeline init --bootstrap` scaffolds the pipeline definition and creates required IAM roles, S3 buckets, and ECR repositories for the deployment pipeline.
- Source: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/deploying-options.html

---

**Observability with SAM**
- Operational Domain: Observability
- AWS Services: AWS X-Ray, Amazon CloudWatch, Lambda Powertools
- Architecture:
  Enable tracing and structured logging via Globals:
  ```yaml
  Globals:
    Function:
      Tracing: Active
      LoggingConfig:
        LogFormat: JSON
        ApplicationLogLevel: INFO
        SystemLogLevel: WARN
        LogGroup: !Sub "/aws/lambda/${AWS::StackName}"

  Resources:
    MyFunction:
      Type: AWS::Serverless::Function
      Properties:
        Handler: src/handler.handler
        Layers:
          - !Sub "arn:aws:lambda:${AWS::Region}:017000801446:layer:AWSLambdaPowertoolsPythonV3-python312-x86_64:4"
        Environment:
          Variables:
            POWERTOOLS_SERVICE_NAME: my-service
            POWERTOOLS_METRICS_NAMESPACE: MyApp
  ```
  **Post-deployment monitoring**:
  ```bash
  # Tail function logs in real-time
  sam logs --name MyFunction --stack-name myapp-dev --tail

  # View deployed resources and endpoints
  sam list resources --stack-name myapp-dev
  sam list endpoints --stack-name myapp-dev
  ```
- Cost Profile: X-Ray tracing: $5/million traces sampled. CloudWatch Logs: $0.50/GB ingested. Minimal for typical serverless workloads.
- Automation: `sam logs --tail` for real-time debugging. CloudWatch Alarms for automated alerting. X-Ray service map for distributed tracing.
- Source: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-monitoring.html

---

## Reference Architectures

**Three-Tier Serverless Web Application**
- Context: RESTful web application with API layer, business logic, and data persistence
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | API | API Gateway (HttpApi) | HTTP routing, CORS, JWT auth |
  | Compute | Lambda | Business logic execution |
  | Data | DynamoDB (SimpleTable) | NoSQL data persistence |
  | Auth | Cognito | User authentication, JWT issuance |
  | CDN | CloudFront | Static asset delivery, API caching |
  | Storage | S3 | Static frontend hosting |

- Key Decisions:
  - HttpApi vs REST API (cost vs features)
  - Single-table DynamoDB vs relational (query patterns)
  - Monolith Lambda vs function-per-route (cold starts vs maintainability)
- Scaling Path:
  1. Start: Single function, SimpleTable, HttpApi
  2. Growth: Function-per-route, DynamoDB with GSIs, CloudFront caching
  3. Scale: Multi-region with DynamoDB Global Tables, Route53 latency routing, separate stacks per domain
- Source: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/what-is-sam-overview.html

---

**Event-Driven Processing Pipeline**
- Context: Asynchronous data processing triggered by file uploads, message queues, or scheduled events
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Ingestion | S3 / SQS / EventBridge | Event source and buffering |
  | Processing | Lambda | Transform, validate, enrich |
  | Orchestration | Step Functions (StateMachine) | Multi-step workflow coordination |
  | Storage | DynamoDB / S3 | Processed data persistence |
  | Notification | SNS / SES | Completion notifications |
  | Error Handling | SQS (DLQ) | Failed event capture |

- Key Decisions:
  - SQS vs EventBridge for event routing (point-to-point vs fan-out)
  - Lambda direct vs Step Functions orchestration (simple vs complex workflows)
  - Batch size and concurrency tuning for throughput vs cost
- Scaling Path:
  1. Start: S3 → Lambda → DynamoDB with DLQ
  2. Growth: SQS buffering, batch processing, Step Functions for multi-step
  3. Scale: Kinesis for streaming, parallel processing with Map state, cross-region replication
- Source: https://docs.aws.amazon.com/prescriptive-guidance/latest/choose-iac-tool/aws-sam.html

---

## SAM Resource Types Reference

| SAM Resource Type | Generates | Purpose |
|-------------------|-----------|---------|
| `AWS::Serverless::Function` | Lambda Function + IAM Role + Event Source Mappings + Permissions | Serverless compute |
| `AWS::Serverless::Api` | API Gateway REST API + Stages + Deployments | REST API with full feature set |
| `AWS::Serverless::HttpApi` | API Gateway HTTP API + Stages | Lightweight, low-cost HTTP API |
| `AWS::Serverless::WebSocketApi` | API Gateway WebSocket API | Bidirectional real-time communication |
| `AWS::Serverless::GraphQLApi` | AWS AppSync GraphQL API | GraphQL endpoint with resolvers |
| `AWS::Serverless::SimpleTable` | DynamoDB Table (single-key) | Simple key-value storage |
| `AWS::Serverless::StateMachine` | Step Functions State Machine + IAM Role | Workflow orchestration |
| `AWS::Serverless::LayerVersion` | Lambda Layer Version | Shared code/dependencies across functions |
| `AWS::Serverless::Application` | CloudFormation Nested Stack | Modular application composition |
| `AWS::Serverless::Connector` | IAM Policies/Roles | Declarative permissions between resources |
| `AWS::Serverless::CapacityProvider` | ECS Capacity Provider | ECS/Fargate integration |

---

## SAM CLI Command Reference

| Command | Purpose | Environment |
|---------|---------|-------------|
| `sam init` | Initialize new project from template | Any |
| `sam validate --lint` | Validate template syntax and best practices | Any |
| `sam build` | Resolve dependencies and create deployment artifacts | Any |
| `sam build --use-container` | Build inside Docker for platform compatibility | Any |
| `sam local invoke` | Invoke function locally with event | Development |
| `sam local start-api` | Start local HTTP server mimicking API Gateway | Development |
| `sam local start-lambda` | Start local Lambda endpoint for SDK testing | Development |
| `sam local generate-event` | Generate sample event payloads for testing | Development |
| `sam deploy --guided` | Interactive deployment with change set review | Staging/Prod |
| `sam deploy --config-env prod` | Deploy using environment-specific config | Production |
| `sam sync --watch` | Auto-sync local changes to cloud (dev only) | Development |
| `sam remote invoke` | Invoke deployed resources in the cloud | Development/Staging |
| `sam logs --tail` | Stream function logs in real-time | Any |
| `sam list resources` | List deployed stack resources | Any |
| `sam list endpoints` | List deployed API endpoints | Any |
| `sam pipeline init --bootstrap` | Scaffold CI/CD pipeline configuration | Setup |
| `sam delete` | Delete deployed CloudFormation stack | Any |

---

## Scenario Coverage

**Standard Case**: Serverless REST API with CRUD operations
- Approach: `AWS::Serverless::Function` with `HttpApi` events + `AWS::Serverless::SimpleTable` + Connectors for permissions. Use Globals for shared config. Deploy via `sam deploy --guided` → CI/CD pipeline with `sam pipeline init`.
- Key Decisions: HttpApi vs Api resource type, single-function vs function-per-route, DynamoDB access patterns (single-table design vs multiple tables)

**Edge Case**: Multi-region active-active serverless with shared state
- Approach: Separate SAM stacks per region deployed via CI/CD pipeline. DynamoDB Global Tables for shared state. Route53 latency-based routing to regional API endpoints. Cross-stack references for shared resources (e.g., Cognito User Pool in primary region).
- Complexity: SAM does not natively orchestrate multi-region deployments — requires CI/CD pipeline with parallel deployment steps targeting different regions.

**Anti-Pattern Case**: Team wants to use `sam sync` in production for "faster deployments"
- Clarification: Ask "What is your rollback strategy if a deployment causes errors? How do you audit what was deployed and when?" — then explain that `sam sync` causes CloudFormation drift, breaks rollback, and eliminates change auditability. Redirect to gradual deployments with `DeploymentPreference` + `AutoPublishAlias` for production safety with visibility.
