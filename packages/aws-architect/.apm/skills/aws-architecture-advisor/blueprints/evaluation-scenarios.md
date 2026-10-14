# Evaluation Scenarios — aws-architecture-advisor

These scenarios test the `aws-architect` advisory agent invoked via `aws-architecture-advisor`.
Run with `/evaluating-skill-scenarios aws-architecture-advisor`.

---

## Scenario 1 — WAF Security Pillar Review (Canonical)

**Input**: "Review my AWS architecture for WAF Security Pillar compliance. We have a Lambda-based
API behind API Gateway with DynamoDB, all in a single AWS account. Our team uses IAM users with
long-term access keys."

**Expected behavior**:
1. Agent loads `architecting-aws-security-pillar` and `applying-aws-well-architected` at P0.
2. Identifies critical gaps: single-account deployment (SEC01-BP01 violation), IAM users with
   long-term keys (SEC02-BP04 violation, family rule R02).
3. Presents WAF pillar assessment at P3 with CRITICAL findings flagged.
4. Returns ADR recommending multi-account migration + IAM Identity Center.
5. Delegation statement: "Load `architecting-aws-multi-account-organizations` for landing zone
   design" and "Load `securing-aws-iam-serverless` to replace access keys with IAM roles."
6. No AWS facts stated that are not in the loaded skills.

**Pass criteria**:
- Surfaces R02 (no long-term access keys) and R07 (multi-account) violations.
- Cites skill names (not raw AWS docs).
- Does not generate any CloudFormation/Terraform code.
- Lists no `(unverified)` items unless the skill itself tags them.

---

## Scenario 2 — Missing Context → Returns Questions (Non-Interactive Contract)

**Input**: "Design a serverless API for us."

**Expected behavior**:
1. Agent identifies the request is underspecified (no domain, no RTO/RPO, no auth model, no
   traffic volume, no existing AWS account structure).
2. At P3, agent stops and returns a numbered question list (does NOT produce a design).
3. Example questions:
   1. Is this a new AWS account or an existing multi-account environment?
   2. Who are the API callers — external users, internal services, or both?
   3. What is the expected request volume (requests/second)?
   4. Are there compliance requirements (PCI DSS, HIPAA, SOC2)?
   5. What is the acceptable cold-start latency for Lambda?
4. Does NOT assume any defaults not named in a skill.

**Pass criteria**:
- Returns numbered questions without producing any architecture diagram.
- Does not invent facts (e.g., does not state "Lambda cold starts are typically 100ms" without
  citing a skill).

---

## Scenario 3 — Multi-Account Landing Zone Assessment (Edge Case)

**Input**: "We have 3 AWS accounts: dev, staging, production. We use CloudTrail in the production
account only. GuardDuty is not enabled. We have no Control Tower. Assess against WAF."

**Expected behavior**:
1. Loads `architecting-aws-multi-account-organizations`, `architecting-cloudtrail-audit-logging`,
   and `architecting-aws-security-pillar`.
2. Identifies: no org-level CloudTrail trail (FF-08 violation), no GuardDuty (FF-08 violation),
   no Security Hub, no Control Tower or DIY Organizations structure (FF-09 partial).
3. Notes: 3 accounts for dev/staging/prod is a correct pattern (FF-09 satisfied) but scope
   boundary for the org trail is wrong.
4. Presents ordered recommendations: CRITICAL — enable GuardDuty org-wide; CRITICAL — move
   CloudTrail to org trail with Log Archive account + S3 Object Lock; HIGH — enable Security Hub.
5. Surfaces the Control Tower v4.0 fact (FF-15) about Security OU being optional — asks whether
   to recommend Control Tower or DIY.

**Pass criteria**:
- Correctly classifies org-level CloudTrail absence as CRITICAL (not just HIGH).
- Does not recommend enabling Control Tower without asking about existing DIY setup (⚠️ Ask First).
- Cites `architecting-cloudtrail-audit-logging` by name.

---

## Scenario 4 — Anti-Pattern Trap: Single NAT Gateway

**Input**: "Here is our VPC Terraform: one NAT Gateway in us-east-1a, shared across all private
subnets in us-east-1a, us-east-1b, and us-east-1c. Is this OK?"

**Expected behavior**:
1. Loads `designing-aws-vpc-networks`.
2. Identifies the shared NAT Gateway as a HIGH anti-pattern (family rule R10): AZ failure in
   us-east-1a would cut outbound internet for all private subnets in all AZs.
3. Also checks for missing S3/DynamoDB Gateway VPC Endpoints (R11).
4. Returns: CRITICAL risk flag for single-AZ NAT GW; recommendation to provision one NAT GW per
   AZ.
5. Does NOT generate Terraform code — advisory only.
6. Delegation statement: "Load `designing-aws-vpc-networks` blueprints for the per-AZ NAT
   Gateway verification commands."

**Pass criteria**:
- Flags single NAT GW as HIGH risk (not just a warning).
- Asks whether S3/DynamoDB Gateway Endpoints are in place (not assumed).
- Does not write Terraform code.
- All facts attributed to `designing-aws-vpc-networks` skill.
