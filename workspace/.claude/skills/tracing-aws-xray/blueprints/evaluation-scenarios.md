# Evaluation Scenarios — tracing-aws-xray

Skill under test: `tracing-aws-xray`
Research base: `StoryBeat/docs/research_cloud_AWS_X-Ray_Distributed_Tracing_2026.md` (2026-08-31)

---

## Scenario 1 — Canonical: New Lambda + API Gateway Instrumentation

```json
{
  "skills": ["tracing-aws-xray"],
  "query": "I need to add distributed tracing to a new serverless web application: API Gateway REST → Lambda → DynamoDB. The stack is Python. What are the exact steps to instrument it with X-Ray?",
  "expected_behavior": [
    "Specifies ADOT Managed Lambda Layer for Python (not the legacy X-Ray SDK)",
    "Instructs enabling TracingConfig Mode=Active per Lambda function (not accepting PassThrough default)",
    "Confirms API Gateway REST stage active tracing (notes HTTP APIs are NOT supported)",
    "Explains that DynamoDB appears as an Inferred Segment; does not instruct instrumenting DynamoDB directly",
    "References centralized sampling rules in the X-Ray console (not local SDK config)",
    "Provides AWSXRayDaemonWriteAccess as the only required IAM policy for the Lambda execution role",
    "Mentions the CloudWatch OTel Endpoint as the destination (HTTP 1.1 only; gRPC not supported)"
  ]
}
```

---

## Scenario 2 — Canonical: ECS Fargate Instrumentation

```json
{
  "skills": ["tracing-aws-xray"],
  "query": "Our Java microservice runs on ECS Fargate. How do I add X-Ray distributed tracing to the task definition?",
  "expected_behavior": [
    "Prescribes ADOT Collector sidecar container (not X-Ray Daemon) in the task definition",
    "Specifies image: public.ecr.aws/aws-observability/aws-otel-collector:latest",
    "Instructs exporting OTel from app container to http://localhost:4317 (gRPC) or http://localhost:4318 (HTTP)",
    "Requires a dedicated taskRoleArn (separate from task execution role) with AWSXRayDaemonWriteAccess + SSM permissions",
    "Does not instruct using the legacy X-Ray Daemon sidecar",
    "Mentions verification: aws ecs describe-task-definition to confirm sidecar and taskRoleArn are present"
  ]
}
```

---

## Scenario 3 — Edge Case: Container-Image Lambda Cannot Use Lambda Layers

```json
{
  "skills": ["tracing-aws-xray"],
  "query": "We deploy Lambda functions as container images. We tried attaching the ADOT Managed Lambda Layer but it doesn't seem to apply. How do we get ADOT auto-instrumentation working?",
  "expected_behavior": [
    "Correctly identifies that Lambda Layers are not supported for container-image Lambda deployments",
    "Instructs baking the ADOT layer contents into the Dockerfile during the Docker build process",
    "Specifies setting AWS_LAMBDA_EXEC_WRAPPER=/opt/otel-instrument as an environment variable on the function",
    "Mentions attaching CloudWatchLambdaApplicationSignalsExecutionRolePolicy if Application Signals is required",
    "Does not suggest workarounds that involve the Lambda Layers attachment mechanism"
  ]
}
```

---

## Scenario 4 — Edge Case: API Gateway HTTP API Requires X-Ray

```json
{
  "skills": ["tracing-aws-xray"],
  "query": "The team wants to enable X-Ray active tracing on our API Gateway HTTP API stage. How do we do it?",
  "expected_behavior": [
    "Clearly states that X-Ray active tracing is NOT supported for API Gateway HTTP APIs or WebSocket APIs — only REST APIs",
    "Does not provide steps to enable X-Ray on an HTTP API stage",
    "Offers two alternatives: (1) migrate to REST API type if X-Ray service map visibility is required; (2) instrument at the compute layer (Lambda/ECS) if HTTP API type must be retained",
    "Asks the team to clarify whether the visibility gap at the API Gateway layer is acceptable",
    "Does not invent a workaround that would silently produce no traces"
  ]
}
```

---

## Scenario 5 — Misuse / Anti-Pattern Trap: PII in Annotations

```json
{
  "skills": ["tracing-aws-xray"],
  "query": "I want to add the user's email address and session token to X-Ray annotations so I can search for specific user traces. Is this the right approach?",
  "expected_behavior": [
    "Flags this as a CRITICAL anti-pattern — annotations are indexed and searchable by any IAM principal with AWSXrayReadOnlyAccess",
    "Explains there is no field-level access control within X-Ray annotations",
    "Warns about GDPR Article 25 and PCI-DSS data protection compliance violations",
    "Instructs using hashed identifiers (e.g., hash(user_id)) for correlation annotations, not raw email or tokens",
    "Instructs using put_metadata() for non-sensitive debug data that does not need to be searchable",
    "Recommends enabling CMK encryption to protect trace data at rest"
  ]
}
```

---

## Scenario 6 — Misuse / Anti-Pattern Trap: Sampling Cost Shock

```json
{
  "skills": ["tracing-aws-xray"],
  "query": "We want to capture every single request for debugging. We set Rate=1.0 in our Lambda ADOT SDK config and we're now seeing very high X-Ray costs. What went wrong?",
  "expected_behavior": [
    "Identifies the root cause: local sampling rule with Rate=1.0 causes each Lambda execution environment to run its own independent reservoir",
    "Explains the cost model: $5.00 per million traces recorded, with unbounded growth at 100% sampling",
    "Identifies a second risk: if using collector-less ADOT, the default parentbased_always_on sampler also produces 100% trace capture",
    "Instructs removing all local sampling rule JSON files from SDK and Collector config",
    "Instructs defining rules centrally in the X-Ray console with appropriate reservoir and fixed-rate values",
    "Suggests Transaction Search as the correct mechanism for full-fidelity per-request debugging, with explicit acknowledgment of CloudWatch Logs ingestion cost",
    "Provides the temporary debugging pattern: highest-priority scoped rule with Rate=1.0 on a specific URL path, deleted after debugging"
  ]
}
```
