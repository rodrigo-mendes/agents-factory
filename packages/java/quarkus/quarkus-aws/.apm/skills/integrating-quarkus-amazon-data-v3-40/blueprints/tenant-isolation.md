# Tenant Isolation Primitives

Back to [SKILL.md](../SKILL.md). Fetched 2026-10-28. Each AWS primitive below is High; applying it to a tenant id is a composition no single AWS page shows (medium confidence). Family rule 6 applies: the tenant comes from the verified token, never from the path alone. IaC for the policies belongs to `provisioning-aws-dynamodb-v6` and `provisioning-aws-s3-v6`; data modelling to `designing-dynamodb-nosql`; IAM design to `securing-aws-iam-serverless`. The model choice is Ask First: [C4](./ask-first-data-decisions.md#c4-tenant-isolation-model).

## Contents

- [A8. LeadingKeys for DynamoDB](#a8-leadingkeys-for-dynamodb)
- [A9. S3 prefix policy variable](#a9-s3-prefix-policy-variable)
- [Limits of these primitives](#limits-of-these-primitives)
- [Per-request tenant clients](#per-request-tenant-clients)

## A8. LeadingKeys for DynamoDB

`dynamodb:LeadingKeys` "Represents the first key attribute of a table—in other words, the partition key… you must use the `ForAllValues` modifier when using `LeadingKeys` in a condition." Example 2 on the AWS page: "The list of actions does not include permissions for `Scan` because `Scan` returns all items regardless of the leading keys." Policy variables need `"Version":"2012-10-17"`. A variable with no value makes `StringEquals` and `StringLike` not match, "and the policy statement does not take effect" ([DynamoDB conditions](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/specifying-conditions.html), [IAM policy variables](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_variables.html)).

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["dynamodb:GetItem","dynamodb:BatchGetItem","dynamodb:Query",
               "dynamodb:PutItem","dynamodb:UpdateItem","dynamodb:DeleteItem","dynamodb:BatchWriteItem"],
    "Resource": ["arn:aws:dynamodb:us-west-2:123456789012:table/GameScores"],
    "Condition": { "ForAllValues:StringEquals": { "dynamodb:LeadingKeys": ["${www.amazon.com:user_id}"] } }
  }]
}
```

Using a tenant identifier instead of a user id as the leading-key value, sourced from `${aws:PrincipalTag/<tenant-tag>}` on a tenant-scoped session, is an application of these two pages (medium confidence).

## A9. S3 prefix policy variable

The IAM page shows `"Resource": ["arn:aws:s3:::amzn-s3-demo-bucket/${aws:PrincipalTag/team}/*"]` and, on `s3:ListBucket`, `"Condition": {"StringLike": {"s3:prefix": ["${aws:PrincipalTag/team}/*"]}}`; the S3 example bucket policies page shows the same per-folder shape for `home/JohnDoe/` ([IAM policy variables](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_variables.html), [S3 example policies](https://docs.aws.amazon.com/AmazonS3/latest/userguide/example-bucket-policies.html)).

```json
{
  "Version": "2012-10-17",
  "Statement": [
    { "Effect": "Allow", "Action": ["s3:ListBucket"],
      "Resource": ["arn:aws:s3:::amzn-s3-demo-bucket"],
      "Condition": {"StringLike": {"s3:prefix": ["${aws:PrincipalTag/team}/*"]}} },
    { "Effect": "Allow", "Action": ["s3:GetObject","s3:PutObject"],
      "Resource": ["arn:aws:s3:::amzn-s3-demo-bucket/${aws:PrincipalTag/team}/*"] }
  ]
}
```

Using a tenant prefix with the same technique is the same application step as A8 (medium confidence).

## Limits of these primitives

- `LeadingKeys` with `StringEquals` matches the whole partition key value. Restricting a partition key that only starts with the tenant id (for example `TENANT#t1#...`) would need `StringLike` with a wildcard, which no AWS page shows for `LeadingKeys` (unverified).
- AWS whitepapers (both marked "for historical reference only") say "the tenant identifier would be in the leading key, constraining access to data for a given tenant" and "the fact that a tenant user is authenticated does not mean that your system has achieved isolation" (medium confidence). Sources: [pooled storage](https://docs.aws.amazon.com/whitepapers/latest/saas-tenant-isolation-strategies/pooled-storage-isolation-strategies.html), [tenant isolation](https://docs.aws.amazon.com/whitepapers/latest/saas-architecture-fundamentals/tenant-isolation.html).
- Prescriptive Guidance (agentic multi-tenant) describes acquiring "tenant-scoped credentials from the AWS Identity and Access Management (IAM) service" ([enforcing tenant isolation](https://docs.aws.amazon.com/prescriptive-guidance/latest/agentic-ai-multitenant/enforcing-tenant-isolation.html)).
- Silo option quota: initial 2,500 tables per Region ([service quotas](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/ServiceQuotas.html)).
- Observability for tenants: log `requestId` and `tenantId` without PII and keep metric dimensions bounded (family rule 7).

## Per-request tenant clients

A tenant-scoped session needs credentials other than the plain execution role. How a Quarkus Lambda builds per-request tenant-scoped clients from the injected singletons is not documented by Quarkiverse 3.23.x (unverified). Do not invent a recipe; ask the user (C4).
