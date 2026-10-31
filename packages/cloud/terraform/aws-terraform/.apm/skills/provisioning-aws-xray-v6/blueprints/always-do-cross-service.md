# Always-Do — Tracing in Other Services and IAM (cross-references)

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources read 2026-10-23. No HCL here: the exact argument
shapes are owned by the sibling skills.

## 5. Tracing in Other Services and IAM

| Service | Terraform knob | AWS page statements | Owning skill |
|---|---|---|---|
| Lambda | see provisioning-aws-lambda-v6 | `Active` sends traces for sampled requests; default without `Active` is `PassThrough`, which forwards the header but does not send traces; sampling 1 request/s + 5 %, not configurable; tracing mode cannot change on a published version; execution role needs `xray:PutTraceSegments` and `xray:PutTelemetryRecords` (in `AWSXRayDaemonWriteAccess`). Source: https://docs.aws.amazon.com/lambda/latest/dg/services-xray.html | provisioning-aws-lambda-v6 |
| API Gateway | see provisioning-aws-api-gateway-v6 | "X-Ray only supports tracing for REST APIs through API Gateway"; redeploy after enabling. Source: https://docs.aws.amazon.com/xray/latest/devguide/xray-services-apigateway.html | provisioning-aws-api-gateway-v6 |
| Step Functions | see provisioning-aws-step-functions-v6 | Role needs `xray:PutTraceSegments`, `PutTelemetryRecords`, `GetSamplingRules`, `GetSamplingTargets`; no X-Ray for Distributed Map child executions. Source: https://docs.aws.amazon.com/step-functions/latest/dg/concepts-xray-tracing.html | provisioning-aws-step-functions-v6 |

Security Hub related controls (https://docs.aws.amazon.com/securityhub/latest/userguide/securityhub-controls-reference.html):
APIGateway.3 (REST API stages should have AWS X-Ray tracing enabled) and Lambda.7 (Lambda functions
should have AWS X-Ray active tracing enabled), both low severity. The reference has no `XRay.*`
controls (medium confidence, absence of evidence).

IAM (https://docs.aws.amazon.com/xray/latest/devguide/security_iam_id-based-policy-examples.html;
policy authoring belongs to provisioning-aws-iam-v6):

- `AWSXRayDaemonWriteAccess` allows `xray:PutTraceSegments`, `PutTelemetryRecords`, `GetSamplingRules`,
  `GetSamplingTargets`, `GetSamplingStatisticSummaries` on `*`.
- Other managed policies: `AWSXrayReadOnlyAccess`, `AWSXrayFullAccess`, `AWSXrayCrossAccountSharingConfiguration`.
- Resource-level permissions exist only for `Create/Get/Update/DeleteGroup` and `Create/Update/DeleteSamplingRule`.
- Sampling-rule ARN uses the rule name (no ID); group ARNs include a generated unique ID.

Encryption keys are owned by provisioning-aws-kms-v6; dashboards and alarms by provisioning-aws-cloudwatch-v6.
