# Quality validation, provisioning-aws-shield-v6 (round 1)

Target: packages/aws-terraform/.apm/skills/provisioning-aws-shield-v6/ (SKILL.md 138 lines; 7 blueprints, all under 160 lines).
Method: read every file, compared against research_AWS_Shield_tf-aws-v6.md and _family_facts_v6.md, then sampled 40 claims. No WebFetch spot checks were done; all verdicts are against the research file. Targets were not modified.

Counts: HIGH 0 | MEDIUM 3 | LOW 6

## Specific checks

| Check | Result |
|---|---|
| Shield Advanced is global, no `region` on `aws_shield_*` | Pass. Matches research section 1 (guide lists `aws_shield_*` under Global services). `region` appears only inside `# WRONG` blocks and the S3 backend. |
| Automatic response legacy after 2026-03-26 | Pass. Sourced to the AWS doc (research 6.4, [17]). The skill does not turn it into a prohibition and keeps it as Ask First. |
| NLB only through EIP allocation ARN | Pass. Matches research 4 ([13]). The ARN format matches the research example. |
| Never row "does not interact with protection groups" | See MEDIUM-2. The wording is not overstated, but the row is weak as a Never row. |
| No $3,000 or other price | Pass. `$3,000` appears only in eval scenario 4 as a user-supplied trap with `must_not`. SKILL.md, ask-first and risks say only "1 year commitment, monthly fee" plus (unverified) U2. |
| HCL argument names | Pass. All names exist in the research (`auto_renew`, `skip_destroy`, `name`, `resource_arn`, `protection_group_id`, `aggregation`, `pattern`, `members`, `resource_type`, `health_check_arn`, `shield_protection_id`, `role_arn`, `log_bucket`, `role_arn_association_id`, `enabled`, `emergency_contact{email_address,phone_number,contact_notes}`). Nothing deprecated or removed appears outside `# WRONG`. `data.aws_region.current.region` matches F15. |
| Tags and register | Mostly pass; see LOW-1 and LOW-2. Plain notation is used throughout. No bold or bracket tags. No F# or M# ids in shipped text (grep: 0 hits other than the `M1-M3` register ids, which are legitimate). |
| Research section 8 legacy claims | Pass. None reproduced as fact. Legacy items 1 to 4 appear only in corrected form. |

## Claims sampled (40)

Pass, in the research and matching: 1 TF `~> 1.16`; 2 provider `~> 6.69` and latest 6.70.0; 3 6.57.0 withdrawn; 4 global; 5 no region in prose; 6 protection does not happen automatically; 7 NLB via EIP; 8 per-account subscription; 9 Shield Standard needs no subscription; 10 `members` and `ARBITRARY`; 11 `resource_type` and `BY_RESOURCE_TYPE`; 12 hosted zones excluded from health check; 13 health check must be healthy, relevant and not deleted; 14 `AWSShieldDRTAccessPolicy`; 15 `use_lockfile` (F7); 16 FM supports all types except Route 53 and Global Accelerator; 17 destroy sets `auto_renew = DISABLED` in the last 30 days and otherwise needs Support; 18 proactive contacts replace existing ones; 19 one contact needs a phone number; 20 150 WCU; 21 automatic response needs a WAFv2 web ACL; 22 import ID formats (account ID, `<id>+<arn>`, bucket name, `protection_group_id`); 23 timeouts 30m; 24 exports `id`/`arn`/`protection_group_arn`/`tags_all`; 25 `COUNT`/`BLOCK`; 26 CloudFront and ALB only; 27 no Security Hub control, tagged M1; 28 enums tagged M2; 29 `skip_destroy` + `prevent_destroy` tagged M3; 30 Terraform 1.17.0 stable 2026-10-21 (F2); 31 v7 planned (F3); 32 `>= 6.0` for reusable modules (F6); 33 `name` deprecated on `data.aws_region` (F15); 34 no Shield entry in the upgrade guide; 35 no Shield entry in the CHANGELOG 6.40 to 6.70; 36 health checks required for proactive engagement; 37 the proactive engagement DRT dependency is untagged and sits in U4; 38 the price is U2.

Not in the research or facts: 39 and 40 (see MEDIUM-1 and LOW-3).

## Findings

### MEDIUM

**MEDIUM-1. Unsourced upgrade procedure stated as fact.** SKILL.md:125: "Upgrade path: move to latest 5.x, get a clean plan, set `~> 6.0`, run `terraform init -upgrade`." This is not in the research (the research section 2 only says no Shield change exists) or in the facts file, and it is untagged. It is also not sourced to the upgrade guide cited three lines above, which implies sourcing. Fix: cite the upgrade-guide section if it contains it, otherwise tag it (unverified) and register it, or delete it. The section already has all its sourced content without this line.

**MEDIUM-2. Never row on protection groups and L7 mitigation (SKILL.md:93).** The row does not overstate the source. The research quotes [17] as "does not interact with protection groups", and the row says exactly that. Two problems remain:
- It is not a Terraform failure mode. The ❌ "Expect protection groups to change L7 automatic mitigation" describes an expectation, not an action. The alternative "Plan mitigations per resource" is a paraphrase of the research ("mitigations are applied per resource") and is not a named official recommendation.
- It has no `# WRONG` entry in never-do-shield.md (that file has 6 entries against 8 SKILL.md Never rows) and is not listed in never-do-patterns.md. The AWS page is also an unversioned "latest" page, so under the evidence rule it caps at medium confidence, which Never rows may not carry.
Fix: move it to a blueprint note or an Ask First row about `aws_shield_application_layer_automatic_response`, which is already legacy and Ask First. Or reword it as an action ("Rely on a protection group to scope automatic mitigation") with the quote and a blueprint entry.

**MEDIUM-3. Always bullet overstates and contains caveats (SKILL.md:64, mirrored in always-do-detection-response.md:5-10 and eval scenario 2).** "Associate a healthy, relevant Route 53 health check with each protection except hosted zones." The research (6.1, 7.3) says health-based detection works with any type except hosted zones. It states the benefit as L3/L4 for NLB, EIP and Global Accelerator and as L7 for CloudFront and ALB. It makes health checks required only for proactive engagement. Research section 8 item 1 rejected the legacy "every protection must be paired" claim; "each protection except hosted zones" restores the same universal. The bullet also carries caveats ("healthy, relevant"), which the evidence rule moves to Ask First. Fix: change the bullet to "Associate a health check via `aws_shield_protection_health_check_association` for resources where health-based detection applies (any type except hosted zones)", and put the healthy/relevant requirements in the Never row that already exists (SKILL.md:91). Move the proactive-engagement dependency to Ask First.

### LOW

**LOW-1. Mapping table shape.** unverified-and-risks.md:50 combines two tags (M2 and M1) in one row, which breaks one row per tag. The column header is `Tag text` rather than `Tag text used in the skill` (line 43). Split the row and rename the column.

**LOW-2. Register rows without a text tag.** U1 and U3 are not asserted anywhere in the skill. That is fine and the status column says so, but there is no `Irresolvable (I1..)` section, and the checklist does not require one. Consider removing U1 and U3 or marking them "coverage only".

**LOW-3. Unsourced re-verification policy.** unverified-and-risks.md:7-8: "Re-verify ... after 30 days" has no source. It is a team policy, so label it as such.

**LOW-4. Quick Reference row over-generalizes.** SKILL.md:106 lists "ELB" as supported, but the NLB exception (own Always bullet and Never row) is nowhere in that row. Add "(NLB via its EIP only)".

**LOW-5. Unsourced HCL details.** always-do-subscription-protection.md:25 (`encrypt = true`) and :22-23 (bucket, key, region literals) are placeholders not in the research. They are harmless backend boilerplate, so mark them as illustrative in a comment.

**LOW-6. Guide pages read from `main`.** The region guide and the resource pages were fetched from the `main` branch (the family F12 method). Under the evidence rule, "main-branch" pages are medium confidence, yet the Never rows (SKILL.md:88, 92) are tiered High. This is a family-wide convention shared with the validated VPC reference, so it needs no change in this unit. A family-level decision is needed on whether main-branch provider docs count as versioned for 6.70.0.

## Format and structure

- Frontmatter: only `name` and `description`. The description is quoted, under 300 characters, and has "Use when". The name equals the folder. The `-v6` suffix is approved.
- SKILL.md has a Version Context table with a Source column, Quick Navigation, the ✅/⚠️/🚫 tiers and a Quick Reference, and it is 138 lines.
- Evaluation scenarios: 4 (canonical, edge, rejection, trap), all with `must_pass` and `must_not`.
- The sibling skills named in the description and Ask First (waf, cloudfront, route53 `-v6`) exist in packages/aws-terraform/.apm/skills/.
- No absolute paths, no relative dates and no `$` prices (except the eval trap).
- I did not run `scripts/verify_skill.py`; the caller should run it.
