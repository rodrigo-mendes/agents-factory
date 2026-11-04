# Quality validation, round 2: provisioning-aws-organizations-v6

Target: packages/aws-terraform/.apm/skills/provisioning-aws-organizations-v6/ (9 files).
Limits of this run: WebFetch and a shell are not available. verify_skill.py was NOT run, and the raw organizations_account page could NOT be fetched. Item 2 is checked against research section 5 only. Line numbers are from reading the files.

Counts: HIGH 0, MEDIUM 2, LOW 4. Overall: passes the HIGH gate. Never rows are not yet one-to-one with the blueprint (N-1).

## Round-1 items

| Item | Result | Evidence |
|---|---|---|
| H1 depends_on Never row | FIXED | grep finds no depends_on in SKILL.md or never-do-*. Only unverified-and-risks.md:24 (U5, "registered only, skill makes no claim"). The former section 4 is gone from never-do-provider.md (now 3 sections). The mapping rows for it are gone. |
| M-1 U3 tag consistency | FIXED, small residue | The same tag "(unverified: absence of evidence)" appears at SKILL.md:121, register U3 (:22) and the mapping row (:60). The residue is N-3. |
| M-2 delegated-admin clause | FIXED | The Always Do bullet at SKILL.md:50 is clean. The clause is now an Ask First row at :83, tagged (medium confidence), M5. always-do-foundation.md:9-10 is clean. |
| M-3 console-org caveat in bullet | FIXED | The Always Do bullet at SKILL.md:66 is clean. The caveat is in the Ask First row at :84, tagged M3. |
| M-4 example-only markers | FIXED | always-do-foundation.md:51 and :107, always-do-policies.md:82, never-do-organization.md:103 and :111 are all marked "example value" or "example value only". |
| M-5 terraform test | FIXED, residue N-5 | always-do-policies.md:111-135 is labelled "illustrative example", has a variables{} block, and asserts the documented SCP 10,240 limit. Syntax is valid. |
| M-6 absence-of-evidence tags | FIXED | SKILL.md:125 and :127 carry "(medium confidence, absence of evidence)". Register M4 (:34) and the mapping row (:59) exist. |
| M-7 return_organization_only | FIXED | It moved to the Ask First row at SKILL.md:85. The Always Do list no longer has it, so it no longer conflicts with roots[0].id (:54). |
| M-8 orphan U4/U6 | FIXED | unverified-and-risks.md:63 "Registered only: U4, U5, U6; listed for traceability". The U4/U5/U6 rows also say "registered only". |
| L-1 identity URL | FIXED | SKILL.md:22 cites the vpc page, which is the F11 URL. |
| L-2 import IDs sources | FIXED | SKILL.md:110 cites the attachment page and says the other IDs are on the pages in the bibliography. |
| L-3 status URL | FIXED | SKILL.md:70 now cites the organization page. |
| L-4 "medium" as severity | FIXED | SKILL.md:120 says "moderate". A grep for bare "medium" finds only the heading at unverified-and-risks.md:27. |
| L-5 mapping header | FIXED | unverified-and-risks.md:49 reads "Tag text used in the skill". |
| L-6 encrypt = true | FIXED | always-do-foundation.md:26 says "example setting". |
| L-7 attachment comment | FIXED | always-do-policies.md:29 reads "Step 1 ... Step 2: add the root attachment below only after testing". |
| L-8 main-branch cap | NOT FIXED | Unchanged. See N-2. It needs an orchestrator decision. |

## Never rows, one-to-one check (requested)
- The "closure quota is 10%" row is gone. The 10% claim now appears only as a must_not in evaluation-scenarios.md:51, which is fine.
- SKILL.md Never table (:92-99) has 8 rows: region, FullAWSAccess, RCP limits, management account, role_name, skip_destroy, dynamodb_table, pin 6.57.0.
- never-do-patterns.md index (:8-16) has 9 entries, and the blueprints have 6 (never-do-organization) + 3 (never-do-provider) = 9 sections.
- The extra entry is "deprecated status attribute" (never-do-provider.md:5, index :14). It is NOT in the SKILL.md Never table. It appears only as an Always Do bullet (:70). So Never rows do NOT equal blueprint entries one-to-one: 8 vs 9 (N-1).
- The other 8 map one-to-one, in order, with sources. All 8 rows are High (documented behaviour or quota). None rests on absence of evidence, a medium item or an unverified item. The alternatives are High as well.
- The Always Do bullets (:46-70) are all single-claim, with one URL and no tagged caveats. Medium or unverified items sit only in Ask First or blueprints.

## Item 2: aws_organizations_account additions
The raw page could not be fetched, so this is checked against research section 5 (a read of that page).
- close_on_deletion not supported for GovCloud: SKILL.md:78. Matches research :67.
- By default destroy only removes the account from the organization: SKILL.md:78 and foundation :91. Matches research :76.
- CLOSE_ACCOUNT_QUOTA_EXCEEDED, then close the account manually: SKILL.md:78. Matches research :77.
- create_govcloud gives govcloud_id, and the GovCloud account is managed only by importing it: SKILL.md:78. Matches research :68.
- The additions are in Ask First (correct tier) and the eval scenario 2 criteria agree with them. The wording "closure quotas are enforced" is a mild paraphrase and is acceptable.
- Status: consistent with the research, NOT confirmed against the live page.

## New findings

MEDIUM
- N-1. Never rows are not one-to-one (see above). Fix: add a Never row for "reading the deprecated status attribute" (alternative: read state) with the account page URL, or drop the entry from never-do-patterns.md and never-do-provider.md. Also update the nav line at SKILL.md:37.
- N-2. Carry-over of round-1 L-8. Several Always Do bullets (:50, :52, :54, :58, :60, :68, :70) and Never rows (:92, :96, :97) cite only raw main-branch provider pages. The evidence rule caps "unversioned/main-branch" pages at medium. The register L2 and line 14 say only that raw main is used and may run ahead. The family convention treats these pages as High. Decide at family level: either record it in the family rules as accepted, or add one coverage-limit sentence in SKILL.md Version Context. No wrong fact results from it.

LOW
- N-3. The U3 tag text is "(unverified: absence of evidence)", which is not a rule tag. The rule's tag is "(medium confidence, absence of evidence)", and the research calls U3 medium. It is consistent everywhere, so the only issue is the notation. Optional: move U3 to the medium table.
- N-4. unverified-and-risks.md:61 is a loose duplicate mapping row ("as listed above", U2, U1). It duplicates rows :51-52. Delete it.
- N-5. The terraform test asserts on the test's own input (`scp_json = "{}"`), so it passes regardless of the module. It also uses `management_account_role_arn`, which is used at foundation:33 but never declared in any snippet. The closing note (:137) mentions only scp_json. Terraform's behaviour for undeclared variables in a test variables{} block is unverified here. Suggest adding "declare all variables used in the snippets" to the note.
- N-6. SKILL.md:99-100 has no blank line before "## Quick Reference". verify_skill.py was not run.

## Grounding sample (new claims, 38 checked, none rechecked from round 1)
Wrong: 0. Unsourced and untagged: 0 above LOW (the "enforced" paraphrase only). Checked against research sections 1-8, the facts file and the bibliography:
1. Throttling 2 rps / 1 rps (SKILL.md:117).
2. Resource policy 40,000 chars.
3. Accounts 10 / OUs 2000 / depth 5.
4. 5 concurrent creations; 3 concurrent closures.
5. Timeouts 10 min.
6. Default policy type SCP.
7-12. Import IDs: o-, ou-, account ID or `<id>_<ALLOW|DENY>`, p-, `<target>:<policy>`, `<account>/<principal>`, rp-.
13. Account.2 High, rule account-part-of-organizations.
14. Account.1 moderate (research "Medium", remapped under the notation rule).
15. RCP 5120 / 5, with RCPFullAWSAccess counting.
16. Disabling the SCP type detaches all SCPs and re-enabling restores only FullAWSAccess.
17. Allow list needs an explicit Allow at every level.
18. Account must exist 4 days before removal.
19. SCPs apply to delegated-admin member accounts.
20. The 12 policy types (list counted, matches).
21. Data source target_id forms, the `filter` argument and the `ids` output.
22. The 7 filter values.
23. Email must not belong to another account.
24. Resource policy has content and tags.
25. delegated_administrator has account_id and service_principal.
26. AWS recommends enabling integrations through each service's own console.
27. SCPs do not affect service-linked roles or resource-based policies directly.
28. Terraform 1.16.6 and 1.17.0 stable since 2026-10-21 (F1, F2).
29. The register parenthetical "no breaking changes to validate, S3 backend, lock file, required_version" (F2).
30. 6.57.0 withdrawn (F4).
31. Tests in `tests/` with mock_provider and command = plan (F10).
32. Identity import needs Terraform >= 1.12.0 (F11).
33. Service Quotas lookups in us-east-1.
34. Member root user covered by SCPs.
35. Min 1 SCP, and the last one cannot be removed.
36. skip_destroy on the attachment means destroy will not detach.
37. Policy-type dependencies: INSPECTOR_POLICY needs inspector2.amazonaws.com, SECURITYHUB_POLICY needs securityhub.amazonaws.com.
38. Deny list is the low-friction default.

## Other checks
- Tags: plain notation, no bold or brackets. Every tag used has a mapping row (except the duplicate in N-4). Register ids are U/M/L only. No F#, M#-family, W# or research ids in shipped text. The only internal ids are the skill's own register ids (L2, L3).
- Frontmatter: name and description only; name matches the folder.
- SKILL.md is 145 lines.
- No evidence of absolute local paths or .github references in the files read.
- Eval file: 5 scenarios, deterministic, grounded.

## Priority
1. Resolve N-1 (add the status Never row to SKILL.md, or drop it from the blueprints).
2. Decide N-2 at family level.
3. Clean up N-3 to N-6, then run verify_skill.py.
