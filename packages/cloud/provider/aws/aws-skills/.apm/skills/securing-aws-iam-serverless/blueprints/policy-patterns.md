# Policy Patterns — securing-aws-iam-serverless

Full IAM policy JSON examples with ❌ wrong and ✅ correct side-by-side.
Source: `research_cloud_AWS_IAM_Security_Serverless_2026.md` (2026-08-28)

---

## Pattern 1: Lambda execution role — least privilege

### ❌ WRONG — Wildcard action + resource
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "*",
      "Resource": "*"
    }
  ]
}
```
Risk: Full account compromise if function code or dependencies are tampered with.

### ✅ CORRECT — Scoped to exact actions and specific ARNs
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject"],
      "Resource": "arn:aws:s3:::my-bucket/prefix/*"
    },
    {
      "Effect": "Allow",
      "Action": ["dynamodb:PutItem", "dynamodb:GetItem"],
      "Resource": "arn:aws:dynamodb:us-east-1:111122223333:table/my-table"
    },
    {
      "Effect": "Allow",
      "Action": ["secretsmanager:GetSecretValue"],
      "Resource": "arn:aws:secretsmanager:us-east-1:111122223333:secret:my-key-*"
    }
  ]
}
```

### Execution role trust policy (Lambda)
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

---

## Pattern 2: Service-principal resource-based policy — confused-deputy conditions

### ❌ WRONG — Service principal grant with no source condition
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "s3.amazonaws.com"
      },
      "Action": "lambda:InvokeFunction",
      "Resource": "*"
    }
  ]
}
```
Risk: Any account that can configure S3 can invoke your Lambda function.

### ✅ CORRECT — SourceAccount + SourceArn conditions (Lambda resource-based policy)
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "s3.amazonaws.com"
      },
      "Action": "lambda:InvokeFunction",
      "Resource": "arn:aws:lambda:us-east-1:111122223333:function:my-fn",
      "Condition": {
        "StringEquals": {
          "aws:SourceAccount": "111122223333"
        },
        "ArnLike": {
          "aws:SourceArn": "arn:aws:s3:::my-bucket"
        }
      }
    }
  ]
}
```

### ✅ CORRECT — EventBridge rule triggering Lambda
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "events.amazonaws.com"
      },
      "Action": "lambda:InvokeFunction",
      "Resource": "arn:aws:lambda:us-east-1:111122223333:function:my-fn",
      "Condition": {
        "StringEquals": {
          "aws:SourceAccount": "111122223333"
        },
        "ArnLike": {
          "aws:SourceArn": "arn:aws:events:us-east-1:111122223333:rule/my-rule"
        }
      }
    }
  ]
}
```

---

## Pattern 3: OIDC trust policy for GitHub Actions CI/CD

### ❌ WRONG — Only aud validated; any GitHub repo can assume the role
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::111122223333:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        }
      }
    }
  ]
}
```
Risk: Any GitHub Actions workflow in any repository can assume this role.

### ✅ CORRECT — aud + sub scoped to specific repo and branch
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::111122223333:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
          "token.actions.githubusercontent.com:sub": "repo:MyOrg/my-repo:ref:refs/heads/main"
        }
      }
    }
  ]
}
```

---

## Pattern 4: DynamoDB per-user isolation — ABAC with LeadingKeys

### Execution role / identity-pool role policy
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:Query"
      ],
      "Resource": "arn:aws:dynamodb:us-east-1:111122223333:table/user-data",
      "Condition": {
        "ForAllValues:StringEquals": {
          "dynamodb:LeadingKeys": "${aws:PrincipalTag/userId}"
        }
      }
    }
  ]
}
```
Note: `Scan` is intentionally excluded — it cannot be scoped by LeadingKeys and would expose all users' data.

Session tags are passed by Cognito identity pool, mapping the user's Cognito `sub` to `aws:PrincipalTag/userId`. The DynamoDB partition key must be the Cognito user ID for this condition to enforce isolation.

---

## Pattern 5: SCP — deny actions outside approved Region (Sep 2025 full IAM language)

### ✅ Condition-based SCP with full IAM language (Sep 2025)
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyNonApprovedRegions",
      "Effect": "Deny",
      "NotAction": [
        "iam:*",
        "sts:*",
        "organizations:*",
        "support:*",
        "trustedadvisor:*",
        "cloudfront:*",
        "route53:*",
        "waf:*"
      ],
      "Resource": "*",
      "Condition": {
        "StringNotEquals": {
          "aws:RequestedRegion": ["us-east-1", "eu-west-1"]
        },
        "BoolIfExists": {
          "aws:PrincipalIsAWSService": "false"
        }
      }
    }
  ]
}
```
Note: `BoolIfExists: aws:PrincipalIsAWSService = false` prevents the SCP from blocking AWS-service-to-service calls that originate from global services.
