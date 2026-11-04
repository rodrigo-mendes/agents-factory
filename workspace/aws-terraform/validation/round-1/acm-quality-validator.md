# Quality validation, round 1: provisioning-aws-acm-v6

Date: 2026-10-22. Scope: `packages/aws-terraform/.apm/skills/provisioning-aws-acm-v6/` (8 files).
Rubric: hybrid-format-checklist, tag-notation-and-registers, evidence-rule, skill-frontmatter.
Grounding sources: `research_AWS_ACM_tf-aws-v6.md`, `_family_facts_v6.md` (F1-F16).

## Verdict

HIGH 0, MEDIUM 6, LOW 8. The skill is mostly well grounded, with no wrong facts found. The `-v6` suffix was not flagged, as instructed.

## Structure (objective)

| Check | Result |
|---|---|
| Frontmatter: only name and description, name equals folder, description quoted, contains "Use when", under 300 characters | pass (about 265 characters) |
| SKILL.md length | 124 lines. This is above the 100-200 line target's lower bound, so it passes |
| Blueprint lengths (limit 160) | pass: 14, 106, 90, 16, 145, 72, 107 |
| Blueprint set | always-do-patterns, never-do-patterns, topic blueprints, unverified-and-risks and evaluation-scenarios are all present |
| Evaluation scenarios | 4: canonical, edge, rejection, trap |
| Absolute paths, `.github`, relative dates | none found by grep |
| Version Context table with Source column, Quick Navigation, three-tier guardrails, Quick Reference | present |
| Always Do bullets with no inline URL | same convention as the validated VPC reference, so not flagged |

## Grounding sample (34 claims)

"R" = research section. Result "OK" means the claim is in the research or F-facts and the tag is correct.

| # | Claim (location) | Result |
|---|---|---|
| 1 | `~> 1.16` / `~> 6.69` (SKILL.md:44) | OK, F1/F3/F6 |
| 2 | 6.57.0 withdrawn (SKILL.md:18, :80) | OK, F4 |
| 3 | `region` default, forces replacement, `id@region` (SKILL.md:19) | OK, F5 |
| 4 | `private_key_wo` needs TF >= 1.11 and `identity` needs >= 1.12 (SKILL.md:20) | OK, R1 and F11 |
| 5 | 198-day validity (SKILL.md:21) | OK, [8] |
| 6 | DNS + `aws_route53_record` `for_each` + validation (SKILL.md:46) | OK, R5 |
| 7 | Reference `aws_acm_certificate_validation.<n>.certificate_arn` downstream (SKILL.md:48) | OK, R4 |
| 8 | `create_before_destroy` on in-use replacement (SKILL.md:50) | OK, R3 |
| 9 | Tag certificates, ACM.3 (SKILL.md:52) | OK, R10 |
| 10 | CloudFront viewer certificate in us-east-1 (SKILL.md:54) | OK, R6. The `region` alternative is untagged, see MEDIUM-6 |
| 11 | `private_key_wo` + `_version` for imports (SKILL.md:56) | OK, [3]. This is documented in the provider page, not inferred |
| 12 | `early_renewal_duration` of 60 days or more (SKILL.md:58) | OK, derived from "no effect under 60 days". The bullet bundles two claims |
| 13 | `most_recent` or `tags` when several match (SKILL.md:60) | `tags` disambiguation is not in the research, see MEDIUM-4 |
| 14 | EMAIL: 8 emails, 72h, no switch to DNS (SKILL.md:67) | OK on content. The cited source is misattributed, see LOW-5 |
| 15 | `export` default DISABLED, extra charge (SKILL.md:68) | OK, [3] |
| 16 | CT logging row (SKILL.md:69) | OK on content. Source misattributed, see LOW-5 |
| 17 | `allow_overwrite` default false, "not recommended" (SKILL.md:70) | OK, [12] |
| 18 | Import-only key algorithms (SKILL.md:71) | OK, [8] |
| 19 | `private_key` stored in state (SKILL.md:77) | OK, [3] |
| 20 | Do not pin ACM certificates (SKILL.md:78) | OK, [10] |
| 21 | CNAME deletion stops renewal (SKILL.md:79) | OK, [11] |
| 22 | Alias on Route 53 record (SKILL.md:81) | Fact OK (F14). Never tier is overstated, see LOW-4 |
| 23 | `validation_method` not on imported certs (SKILL.md:83) | OK, [3] |
| 24 | Quick Reference: 75m timeout, 72h, quotas, ACM.1/2/3 (SKILL.md:94-100) | OK, [4], [11], [10b], [15] |
| 25 | Quick Reference: renewal 45 days; events 30/15/7/3/1 (SKILL.md:97) | OK, tagged M4, user guide treated as authoritative |
| 26 | PCA defaults (SKILL.md:102) | OK, [6] |
| 27 | 6.47.0 and 6.51.0 changelog entries (SKILL.md:110) | OK, R2 |
| 28 | Upgrade path `init -upgrade` (SKILL.md:112) | OK, F8 |
| 29 | HCL comment "requestable: RSA_2048, EC_prime256v1, EC_secp384r1" (public:34) | OK, [8] |
| 30 | CloudFront imported cert, 24h (import:27) | OK, [13] |
| 31 | PCA quota 200 per Region (import:54) | Citation does not match the research, see MEDIUM-3 |
| 32 | Import `id` / `identity` forms (import:77-84) | OK. "Use one of the two forms, not both" (import:90) is unsourced, see MEDIUM-5 |
| 33 | Wildcard and apex give an identical CNAME (never:91) | OK, [11]. The `allow_overwrite` question is tagged M2 |
| 34 | `# WRONG` blocks (never §1, §4, §5, §7, §8, §9) | OK. No removed or deprecated arguments appear outside WRONG blocks |

## Findings

### HIGH

None.

### MEDIUM

1. **Data source `key_types` omitted.** Research R8 says `key_types` matters because ACM does not return all key types by default.
   - The skill never mentions it (SKILL.md:101, import:57-70).
   - Its own canonical example creates an EC certificate (public:34).
   - The skill's data-source example (import:64-68) has no `key_types`, so a lookup of such a certificate can silently miss it.
   - Fix: add the gotcha to Quick Reference and to import §6. It is documented in the research, so tag it High.
   - Escalate to HIGH if you treat omissions that cause wrong output as HIGH.
2. **`allow_overwrite` tier inconsistency.**
   - SKILL.md:70 puts it in Ask First.
   - `never-do-patterns.md:13` and `never-do-certificates.md:89-95` list it as a Never pattern.
   - That Never section has no WRONG block and carries a (medium confidence) item, which breaks the evidence rule that Never rows are High only.
   - Fix: move §6 out of the Never blueprint, or restate it with High content only (default false, doc says "not recommended"). Keep the M2 caveat in Ask First.
3. **PCA quota citation mismatch (import:54-55).**
   - The research sources "200 private CAs per Region; deleted CAs count" to [10b].
   - The skill cites the `acmpca_certificate_authority` provider page, which the research does not show as the source.
   - Fix: cite the correct page, or tag the claim.
4. **`tags` as a disambiguator in an Always bullet (SKILL.md:60).** The research says only that `tags` is an exact match, not that it resolves multiple matches. Fix: reword to "`most_recent = true`, or `tags`/`types`/`key_types` filters narrow the match (tags is an exact match)", or tag it.
5. **Unsourced and untagged statements.**
   - "Use one of the two `import` forms per resource, not both" (import:90) is not in the research.
   - `create_before_destroy` on the imported certificate (import:21) extends the documented in-use replacement note without saying so.
   - Fix: source or tag both.
6. **`region = "us-east-1"` as an equal alternative for CloudFront (SKILL.md:54, :82; never:108; public:77-79) is untagged.**
   - Research R6 offers it as valid, derived from F5.
   - F16 treats the same alias-versus-`region` inference for WAFv2 CloudFront as (medium confidence).
   - Fix: tag consistently with F16, or confirm against the provider page that `region` plus CloudFront needs no alias.

### LOW

1. **Register hygiene (unverified-and-risks.md:19-21, :42).**
   - U2-U4 are "not stated in this skill", so they have no tag use and no mapping row. They are orphan register entries.
   - There is no I-section.
   - The mapping column header is "Tag text", not "Tag text used in the skill".
   - Otherwise every tag has a real mapping row and the IDs are well formed: U1 and M4 map to SKILL.md, M1 and M3 to public §2/§3, M2 to never §6.
2. **Index claims are inaccurate.**
   - `never-do-patterns.md:4` says every entry has a `# WRONG` block, but §2 and §6 do not.
   - `always-do-patterns.md:3` says "complete HCL", but `data.aws_route53_zone.this`, `aws_route53_record.cf_validation` and `aws_lb_listener` are undefined or elided.
3. **Incomplete HCL (never:140-143).** The CORRECT backend block has no bucket or key.
4. **Overstated Never row (SKILL.md:81).** The research calls the alias on a Route 53 record "harmless but unnecessary". Move it to a note, or word it as "unnecessary" rather than Never.
5. **Misattributed sources in Ask First (SKILL.md:67, :69).**
   - "Cannot switch to DNS" comes from the dns-validation page.
   - "Not settable on imported" comes from the provider page.
   - Both rows cite the best-practices page.
6. **M3 not surfaced in SKILL.md.**
   - The same-Region claim for the second validation resource (public:95-96) is tagged only in prose at public:79.
   - The HCL comment "same Region as the certificate" (public:96) is untagged.
   - Eval scenario 2 makes it a hard must_pass.
   - Fix: add (medium confidence) in the comment, or mention M3 in the Quick Reference.
7. **Canonical example uses `EC_prime256v1` (public:34).** U1 says the default `key_algorithm` is unverified, and ALB support for EC is not sourced. Consider the default algorithm, or note that EC also affects the data-source lookup (MEDIUM-1).
8. **Wildcard plus apex gap (public:41-54).**
   - The `for_each` pattern, keyed by domain, produces duplicate identical records for wildcard plus apex.
   - Fix: add a pointer to the Ask First `allow_overwrite` row.

## Specific checks requested

| Check | Result |
|---|---|
| Second `aws_acm_certificate_validation` with `provider = aws.us_east_1` | Tagged (medium confidence) in prose and mapped to M3 (public:79). The HCL comment is untagged (LOW-6) |
| `private_key_wo` sourcing | Documented in [3] (research R3), not inferred. No tag is needed. The `create_before_destroy` extension is not sourced (MEDIUM-5) |
| Every (unverified) / (medium confidence) tag maps to a real register id and file/section | Yes, 5 of 5 |
| Orphan rows | U2-U4 (LOW-1) |
| Research legacy-claims-wrong not reproduced | Confirmed. Grep for `$400`, `ResourceInUse` and `CKV_` appears only in the register notes. The legacy settings appear only inside WRONG blocks and eval traps |
| Removed or deprecated arguments outside WRONG blocks | None found |
| ACM user guide authoritative for renewal windows (M4) | Yes. SKILL.md:97 and the register state it, and the 45-day / 30-15-7-3-1 values match [14] |
