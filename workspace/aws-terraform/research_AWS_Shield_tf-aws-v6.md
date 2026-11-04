# Research — AWS Shield with Terraform 1.16.x + hashicorp/aws 6.x

> Research date: **2026-10-23**. Status: **COMPLETE** (unit `shield`, flat fan-out, no sub-agents).
> Resource docs read from upstream raw markdown (`hashicorp/terraform-provider-aws`, `main`) per F12.
> Coverage reference only (not a source): `workspace/terraform/research_AWS_Shield_aws-v6.x.md` (6.47.0, Terraform 1.7 — EOL). Claims found wrong are listed in §8.

## 1. Version Context

| Item | Value | Source |
|---|---|---|
| Terraform CLI | `required_version = "~> 1.16"` (1.16.6); 1.17.0 stable but not targeted | F1, F2 |
| hashicorp/aws | latest 6.70.0 (2026-10-21 in CHANGELOG); constraint `version = "~> 6.69"`; CHANGELOG top heading is `6.71.0 (Unreleased)` | F3; [2] |
| Withdrawn | 6.57.0 — never pin | F4 |
| Region model | Shield Advanced is **global**: the enhanced-region guide lists exactly `* Shield Advanced (\`aws_shield_*\`)` under "Global services" → no `region` argument, no `@region` import | F14; [1] |
| Carve-outs | **None found.** None of the 8 `aws_shield_*` resource pages ([3]–[10]) documents a `region` argument or any region statement in prose; region appears only in examples (via `data.aws_region.current.region` to build EIP/IAM ARNs). Unlike WAFv2/Route 53 Resolver (F16), no Shield carve-out exists | [3]–[10] |
| Identity import | not documented on Shield pages; import IDs below are the classic `id` strings | [3]–[10] |

```hcl
terraform {
  required_version = "~> 1.16"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 6.69" }
  }
}
```

## 2. Provider 6.x changes for Shield

- **6.0.0 upgrade guide (F13):** no mention of Shield; no `aws_shield_*` breaking change is documented. [11]
- **CHANGELOG 6.40.0 → 6.70.0:** no entry mentions `aws_shield_*` or `data.aws_shield_*` (two chunks read: 6.70.0→6.55.0 and 6.54.0→6.40.0, covering the required 6.48.0→6.70.0 range). [2]
- Conclusion: Shield resource schemas are stable across 6.48.0–6.70.0 per the CHANGELOG (high confidence).

## 3. `aws_shield_subscription` [5]

- Arguments (all optional): `auto_renew` — `ENABLED` | `DISABLED`, default `ENABLED`; `skip_destroy` — when `true`, destroy leaves `auto_renew` unchanged and only removes from state.
- Attribute: `id` = AWS account ID.
- WARNING on page: subscribing "requires a 1 year subscription commitment with a monthly fee" (links AWS Shield pricing).
- Destroy behaviour: destroy sets `auto_renew = DISABLED`; auto-renew can only be disabled in the **last 30 days** of the subscription; to unsubscribe outside that window, contact AWS Support.
- Import: account ID (`import { to = aws_shield_subscription.example, id = "<account-id>" }`).
- AWS side [14]: "You must subscribe to Shield Advanced for each AWS account that you want to protect. You do not need to subscribe to Shield Standard." Unsubscribing requires AWS Support; disabling auto-renewal uses `UpdateSubscription` / `update-subscription`. Billing: Organizations members are billed to the payer account; one subscription price covers all subscribed accounts in a consolidated-billing family. [14][15]
- Recommendation (inference from the documented destroy semantics, medium confidence): set `skip_destroy = true` and `lifecycle { prevent_destroy = true }` on production subscriptions.

## 4. `aws_shield_protection` [3]

- Required: `name` (friendly name), `resource_arn` (ARN of the resource to protect). Optional: `tags` (provider `default_tags` supported; `tags_all` exported).
- Attributes: `id`, `arn`.
- Supported resource types listed on page: CloudFront distributions, Elastic Load Balancing load balancers, Global Accelerator accelerators, Elastic IP addresses, Route 53 hosted zones.
- AWS list [13]: CloudFront distributions (incl. staging distributions of a protected primary in continuous deployment); Route 53 hosted zones; Global Accelerator **standard** accelerators; EC2 Elastic IPs; EC2 instances via EIP association; ALB; Classic LB; **NLB only "through associations to Amazon EC2 Elastic IP addresses"** → protect the NLB's EIP allocation ARN, not the NLB ARN (the "NLB?" in scope resolved).
- "Shield Advanced doesn't automatically protect your resources" — each must be explicitly protected (or via Firewall Manager Shield Advanced policy). [13][14]
- No NOTE/WARNING blocks; no forces-new statements documented on the page.
- Import: protection `id`.
- Example on page builds EIP ARN: `arn:${partition}:ec2:${region}:${account}:eip-allocation/${aws_eip.x.id}`.

## 5. `aws_shield_protection_group` [4]

| Arg | Req | Notes |
|---|---|---|
| `protection_group_id` | Yes | name of the group; also import ID |
| `aggregation` | Yes | examples use `MAX`, `MEAN`, `SUM`; full enum not listed on page |
| `pattern` | Yes | examples use `ALL`, `ARBITRARY`, `BY_RESOURCE_TYPE`; full enum not listed |
| `members` | No | ARNs; **required when `pattern = "ARBITRARY"`, must not be set otherwise** |
| `resource_type` | No | **required when `pattern = "BY_RESOURCE_TYPE"`, must not be set otherwise**; example `ELASTIC_IP_ALLOCATION` |
| `tags` | No | default_tags supported |

- Attributes: `protection_group_arn`, `tags_all`. No NOTE blocks. Import: `protection_group_id`.
- Full enum lists for `aggregation`/`pattern`/`resource_type` are not on the TF page (see M2).
- AWS: automatic L7 mitigation "does not interact with protection groups" — mitigations are applied per resource. [17]

## 6. Association / response resources

### 6.1 `aws_shield_protection_health_check_association` [6]
- Required: `health_check_arn` (Route 53 health check ARN), `shield_protection_id`. Attribute `id`.
- Import: `<shield_protection_id>+<health_check_arn>` (e.g. `ff95…669a+arn:aws:route53:::healthcheck/3742…`).
- AWS [16]: health-based detection works with **any resource type except Route 53 hosted zones**; L3/L4 benefit for NLB, EIP, Global Accelerator; L7 benefit for CloudFront and ALB. The health check **must report healthy when associated**, must be relevant to the resource, and must not be deleted while used. "Health checks are required for Shield Response Team (SRT) proactive engagement support." Shield Advanced doesn't manage health checks for you.

### 6.2 `aws_shield_drt_access_role_arn_association` [7]
- Required: `role_arn` — ARN of the role the SRT uses; attach managed policy `AWSShieldDRTAccessPolicy` before the request. No extra attributes.
- Timeouts: create/update/delete 30m. Import: account ID.

### 6.3 `aws_shield_drt_access_log_bucket_association` [8]
- Required: `log_bucket` (S3 bucket with logs to share), `role_arn_association_id` (ID of the role ARN association). No extra attributes.
- Timeouts: create/delete 30m. Import: `log_bucket` name.

### 6.4 `aws_shield_application_layer_automatic_response` [9]
- Required: `resource_arn` — "CloudFront Distributions and ALBs only at this time"; `action` — `COUNT` or `BLOCK`.
- Timeouts: create/update/delete 30m. Import section **not present** on the page (U1).
- AWS [17]: works only with WAF v2 web ACLs (requires a web ACL associated with the resource); adds a Shield-managed rule group using **150 WCUs**; baseline takes 24 h–30 days after web ACL association; for ALBs behind CloudFront, enable on the CloudFront distribution instead.
- ⚠️ **AWS deprecation note** [17]: "Starting March 26, 2026, the Anti-DDoS Managed Rule Group (Anti-DDOS AMR) for AWS WAF becomes the default solution for protection against HTTP request flood attacks … It supersedes the Layer 7 Auto Mitigation (L7AM) feature." Existing customers can keep L7AM; new customers needing it must contact AWS Support. → Prefer the Anti-DDoS AMR in `aws_wafv2_web_acl` for new designs; treat this resource as legacy (Ask-First).

### 6.5 `aws_shield_proactive_engagement` (legacy-checklist item) [10]
- Required: `enabled` (bool), `emergency_contact` blocks (`email_address` required; `phone_number` optional, `+` and up to 15 digits; `contact_notes` optional). At least one contact must have a phone number.
- NOTE: contacts defined here **replace** any contacts already configured in AWS. Import: account ID.
- Requires health checks per AWS [16].

### 6.6 Not researched
- `aws_shield_subscription` has no separate `auto_renew` resource — `auto_renew` is an argument (§3). `data.aws_shield_protection` not fetched (L2).

## 7. AWS guidance

### 7.1 Standard vs Advanced
- "All AWS customers benefit from the automatic protection of Shield Standard, at no additional charge." Standard defends against common network/transport-layer DDoS; Route 53 hosted zones, CloudFront and Global Accelerator standard accelerators get comprehensive L3/L4 protection. [12] Shield Standard needs no Terraform resource.
- Shield Advanced: paid subscription; 1-year commitment with monthly fee stated on the TF page [5]; specific dollar amount **not verified** on a fetched official page (U2).

### 7.2 Relation to AWS WAF [15][17]
- Subscription covers standard WAF fees (web ACL, rules, base request price) for Shield-protected resources, up to 1,500 WCUs and default body size; up to 50 billion requests/month; includes the Layer 7 Anti-DDoS Amazon Managed Rule group. Not covered: WAF on unprotected resources, Bot Control, CAPTCHA, >1,500 WCUs, larger body inspection.
- L7 protection = WAF web ACL + your own rate-based rule; automatic mitigation adds the 150-WCU rule group.
- WAFv2 is regional (F16); CloudFront-scope web ACLs need us-east-1 (F16).

### 7.3 Best practices (official)
- Protect resources explicitly (no automatic protection) [13]; use Firewall Manager to automate subscriptions/protections across an organization — it supports all protected types **except Route 53 and Global Accelerator** [14].
- Associate a healthy, relevant Route 53 health check with each protection except hosted zones; required for proactive engagement [16].
- For NLB, protect via EIP [13]. For ALB behind CloudFront, enable automatic mitigation on CloudFront [17].
- Grant SRT access with a role carrying `AWSShieldDRTAccessPolicy` [7].

### 7.4 Security Hub controls
- The Security Hub controls reference ([18], read in full across two chunks on 2026-10-23) contains **no control whose ID or title mentions Shield**; no `ShieldAdvanced.*` prefix exists. `https://docs.aws.amazon.com/securityhub/latest/userguide/shield-controls.html` returned only a title (no body). → **`ShieldAdvanced.1` does not exist** in the current reference (medium confidence, M1). Related visibility path: Firewall Manager Shield Advanced policy findings flow into Security Hub [19].

## 8. Legacy-file claims found wrong or unsupported
1. "Every `aws_shield_protection` must be paired with `aws_shield_protection_health_check_association`" — wrong for Route 53 hosted zones (not supported) [16]. Its own later note listing supported types omits NLB; AWS says any type except hosted zones [16].
2. "Every CloudFront/ALB protection must be paired with `aws_shield_application_layer_automatic_response`" (CRITICAL) — outdated: since 2026-03-26 AWS designates the Anti-DDoS AMR as default and L7AM as superseded [17].
3. "$3,000/month" — not stated on any fetched official page (U2); cannot be used.
4. NLB protection shown via EIP — correct; but legacy implies `aws_lb` ARN generally works for ELB; AWS: NLB only via EIP [13].
5. Backend `dynamodb_table` locking — deprecated (F7); use `use_lockfile = true`.
6. `required_version = ">= 1.7"`, `~> 6.0` — superseded by F1/F3.
7. "Shield metrics only in us-east-1" — not verified (U3).
8. Proactive-engagement "apply error without DRT role" — not documented on the TF page (U4); AWS states health checks are required [16].

## 9. Unverified / medium confidence / limits
- **U1** Import ID for `aws_shield_application_layer_automatic_response` — not on page.
- **U2** Shield Advanced monthly price amount (pricing page not fetched).
- **U3** Shield CloudWatch metrics region (us-east-1) claim from legacy.
- **U4** Hard API dependency of proactive engagement on DRT role association.
- **M1** Absence of Security Hub Shield controls — reference read fully but `shield-controls.html` body did not render.
- **M2** Full enums for protection group `aggregation`/`pattern`/`resource_type` taken from examples only (`MAX|MEAN|SUM`, `ALL|ARBITRARY|BY_RESOURCE_TYPE`).
- **M3** `skip_destroy` + `prevent_destroy` combination is an inference from documented destroy semantics.
- **L1** CHANGELOG chunks before 6.40.0 not read (outside scope).
- **L2** `data.aws_shield_protection` not covered.
- **L3** Shield pricing and Firewall Manager Shield policy resources (`aws_fms_policy`) not researched.

## 10. Security note
No prompt-injection or AI-directed instructions observed in any fetched page. (One fetch of `ddos-subscribe-shield-advanced.html` returned only a title and the tool appended "general knowledge" pricing text — discarded, not used as a source.)

## Source Bibliography
All fetched 2026-10-23.
1. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown
2. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
3. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/shield_protection.html.markdown
4. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/shield_protection_group.html.markdown
5. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/shield_subscription.html.markdown
6. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/shield_protection_health_check_association.html.markdown
7. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/shield_drt_access_role_arn_association.html.markdown
8. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/shield_drt_access_log_bucket_association.html.markdown
9. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/shield_application_layer_automatic_response.html.markdown
10. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/shield_proactive_engagement.html.markdown
11. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
12. https://docs.aws.amazon.com/waf/latest/developerguide/ddos-standard-summary.html
13. https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary-protected-resources.html
14. https://docs.aws.amazon.com/waf/latest/developerguide/enable-ddos-prem.html
15. https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary.html
16. https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-health-checks.html
17. https://docs.aws.amazon.com/waf/latest/developerguide/ddos-automatic-app-layer-response.html
18. https://docs.aws.amazon.com/securityhub/latest/userguide/securityhub-controls-reference.html
19. https://docs.aws.amazon.com/waf/latest/developerguide/ddos-viewing-multiple-accounts.html
20. https://docs.aws.amazon.com/waf/latest/developerguide/shield-chapter.html
