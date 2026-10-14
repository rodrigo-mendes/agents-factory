---
name: aws-security-baseline
description: "AWS security baseline guardrails for IaC artifacts (Terraform, CloudFormation, SAM, CDK). Use when editing or reviewing AWS infrastructure-as-code files."
applyTo: "**/*.tf,**/*.yaml,**/*.yml,**/*.json"
---

# AWS Security Baseline Guardrails

Technical facts live in the aws-skills (`packages/aws-skills/.apm/skills/`). This rule states
what to check and where to look; it does not duplicate skill bodies. Tags `(unverified)` and
`(medium confidence)` from a skill apply here too.

Source family rules: R01–R06 from `workspace/aws/_family_rules_v2026.md`.

## Always

- **R01 — One IAM role per compute resource.** Each Lambda function, ECS task definition, and
  EC2 Auto Scaling group references a dedicated IAM role with least-privilege permissions.
  Skill: `securing-aws-iam-serverless` (SEC-AD-3).

- **R02 — No long-term static access keys.** IaC templates must not define `AWS::IAM::AccessKey`
  or Terraform `aws_iam_access_key` resources for human identities. All human access via IAM
  Identity Center.
  Skill: `architecting-aws-security-pillar` (SEC-AD-2).

- **R03 — No hardcoded credentials.** Environment variables, parameter values, and Lambda
  function configurations must not contain literal AWS access keys, secret keys, or passwords.
  Use Secrets Manager references or SSM Parameter Store SecureString.
  Skill: `securing-aws-secrets-certificates`, `securing-aws-iam-serverless`.

- **R04 — Encryption at rest enabled on all sensitive data stores.** S3 buckets must declare
  `BucketEncryption` (KMS or SSE-S3 minimum). RDS instances must set `StorageEncrypted: true`.
  DynamoDB server-side encryption must be enabled. EBS volumes must use encrypted snapshots.
  Skill: `architecting-aws-security-pillar` (SEC-AD-5).

- **R05 — Encryption in transit enforced.** ALB listeners on port 80 must redirect to 443.
  S3 bucket policies must include a Deny on `aws:SecureTransport = false`. API Gateway stages
  must enforce TLS.
  Skill: `architecting-aws-security-pillar` (SEC07).

- **R06 — Confused-deputy conditions on service-principal resource-based policies.** Any
  resource-based policy granting a service principal (`*.amazonaws.com`) must include
  `aws:SourceArn` or `aws:SourceAccount` condition. No naked `*` principal grants.
  Skill: `securing-aws-iam-serverless`.

## Ask First

- **KMS CMK vs. AWS-managed key** — ask data classification before deciding. CMK for
  regulated/restricted data; AWS-managed key for lower tiers. See `securing-aws-secrets-certificates`.

- **WAF rule group selection** — ask traffic profile and compliance requirements before choosing
  managed vs. custom rule groups. See `securing-aws-waf-web-acls`.

- **Shield Advanced** — ask whether the workload is a high-value target (financial, gaming,
  DDoS-sensitive) before recommending Shield Advanced (cost-impacting). See
  `protecting-workloads-ddos-shield`.

## Never

- Wildcard (`*`) actions or resources in IAM policies without accompanying Deny conditions and
  explicit justification → use IAM Access Analyzer policy generation from CloudTrail.

- Security Groups with `0.0.0.0/0` inbound on port 22 or 3389 → use Systems Manager Session
  Manager exclusively. See `securing-vpc-network-access`.

- Internet-facing ALB or CloudFront distribution without AWS WAF → attach WAF with at minimum
  the AWS Managed Rules Core Rule Set. See `securing-aws-waf-web-acls`.

- Storing AWS credentials in Lambda environment variables → use execution role + Secrets Manager.
  See `securing-aws-iam-serverless`.
