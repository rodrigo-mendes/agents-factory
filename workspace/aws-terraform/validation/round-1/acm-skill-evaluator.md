# Evaluation report: provisioning-aws-acm-v6 (round 1)

Method: no sub-agents. I answered each scenario myself using only SKILL.md and its linked blueprints, then judged the answer. Source files: SKILL.md, always-do-public-certificates.md, always-do-import-private-lookup.md, never-do-certificates.md, unverified-and-risks.md.

## Summary

| Scenario | must_pass | must_not | Verdict |
|---|---|---|---|
| 1 Canonical public cert + Route 53 | 8/8 | 3/3 OK | PASS |
| 2 CloudFront edge case | 5/5 | 3/3 OK | PASS |
| 3 Misuse: imported cert | 4/4 | 3/3 OK | PASS |
| 4 Anti-pattern trap | 5/5 | 4/4 OK | PASS (one flag) |

Overall: 22/22 must_pass and 13/13 must_not OK. All four scenarios PASS.

## Scenario 1: Canonical

The response is built from always-do-public-certificates.md §1 and §2.

must_pass:
- PASS: `required_version = "~> 1.16"` and `version = "~> 6.69"` (public §1).
- PASS: `validation_method = "DNS"` (§2).
- PASS: `aws_route53_record` with `for_each` over `domain_validation_options` (§2).
- PASS: `aws_acm_certificate_validation` with `certificate_arn` and `validation_record_fqdns` (§2).
- PASS: the listener uses `aws_acm_certificate_validation.this.certificate_arn`. The §2 snippet has the comment "# waits for issuance".
- PASS: `lifecycle { create_before_destroy = true }` (§2).
- PASS: `tags = { Name = ... }` (§2, Security Hub ACM.3).
- PASS: no `provider` or `region` on the record. §2 says "the record needs no provider alias and no region".

must_not:
- OK: the listener does not reference `aws_acm_certificate.this.arn`.
- OK: `allow_overwrite` is not set. It appears in SKILL.md Ask-First and never-do §6.
- OK: no 6.57.0 pin.

## Scenario 2: CloudFront

must_pass:
- PASS: request or import in `us-east-1` for viewer HTTPS (public §3, never-do §7).
- PASS: the two options are `provider = aws.us_east_1` and `region = "us-east-1"` (public §3).
- PASS: `aws_acm_certificate_validation.cf` carries `provider = aws.us_east_1`, "same Region as the certificate" (§3).
- PASS: `cf_validation` records take no alias. Never-do §5 says "Route 53 is global" and public §3 says "take no alias".
- PASS: never-do §7 says "for CloudFront-to-ELB origin HTTPS any Region works".

must_not:
- OK: the certificate is not created in eu-west-1.
- OK: no alias on the record.
- OK: I tagged the same-Region validation requirement "(medium confidence)", inferred (register M3), not as explicitly documented.

## Scenario 3: Misuse rejection

must_pass:
- PASS: never-do §8 says "`validation_method` must not be set for imported certificates".
- PASS: use `private_key_wo` + `private_key_wo_version` because `private_key` "is stored in state" (never-do §1, SKILL.md Never Do).
- PASS: "write-only argument (Terraform >= 1.11)" (never-do §1, import §4).
- PASS: "Imported certificates are not eligible for managed renewal — re-import before expiry" (import §4, Quick Reference).

must_not: all OK. I did not recommend `private_key`, accept `validation_method`, or claim auto-renewal.

## Scenario 4: Anti-pattern trap

must_pass:
- PASS: `>= 1.7` becomes `~> 1.16` and `dynamodb_table` becomes `use_lockfile = true` (never-do §9, public §1).
- PASS: Route 53 is global, so the alias is unnecessary (never-do §5).
- PASS (flag below): `allow_overwrite` defaults to `false` and is "not recommended for most environments" (never-do §6, SKILL.md Ask-First).
- PASS: the 198-day validity is "an AWS service change, not a provider change", and the 6.0.0 upgrade guide has no `aws_acm_*` entries (SKILL.md section "5.x to 6.x Migration").
- PASS: do not delete the validation CNAMEs because "deleting the CNAME stops renewal" (never-do §3, SKILL.md Never Do).

must_not: all OK.
- `dynamodb_table` is flagged as deprecated.
- `allow_overwrite` is not accepted as required.
- CNAME deletion is rejected.
- The 198-day validity is not attributed to the provider.

## Ambiguous or criterion issues

1. Scenario 4, criterion 3 says `allow_overwrite` "is not required". The research does not support that strongly. never-do §6 says a wildcard plus apex produces an identical CNAME, and whether the provider example sets `allow_overwrite = true` for it is unconfirmed (M2). So it may be genuinely needed in that case. The skill's actual position is "default false, not recommended, ask first". The criterion should be softened to "not required by default; ask before enabling". My answer passed because I could say "not required by default", but a strict judge could mark the absolute claim as unsourced.
2. Scenario 2, must_not 3 depends on the M3 "(medium confidence)" tag being carried into the answer. It is checkable, since the tag sits right in public §3.
3. Scenario 1 never states the ALB listener's arguments (`# ...`). That is fine for the criteria but leaves the HTTPS listener snippet skeletal.

## Fixes needed

- No skill fixes are required for these scenarios.
- Optional: reword Scenario 4 must_pass #3 in `blueprints/evaluation-scenarios.md` as described in item 1.
- Optional: add a short `allow_overwrite` note on the wildcard-plus-apex collision to never-do §6 if the research can confirm it. This would close M2.
