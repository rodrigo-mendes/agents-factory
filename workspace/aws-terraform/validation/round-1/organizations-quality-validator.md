# Quality validation, round 1: provisioning-aws-organizations-v6

Target: packages/aws-terraform/.apm/skills/provisioning-aws-organizations-v6/ (9 files).
Research: workspace/aws-terraform/research_AWS_Organizations_tf-aws-v6.md. Facts: _family_facts_v6.md.
Limits of this run: no shell, so verify_skill.py was NOT run. WebFetch was not available, so the raw provider page for organizations_organization was NOT fetched. Everything below is checked against the research file and the policy blueprints. Line numbers were taken by reading the files.

Counts: HIGH 1, MEDIUM 8, LOW 8. Overall: close to passing; one evidence-rule violation blocks it.

## Format checks
- Frontmatter has only name and description. The description is quoted, about 250 characters, and contains "Use when". The name equals the folder. The -v6 suffix is approved. Pass.
- SKILL.md is 147 lines (limit 100-200). The largest blueprint is 136 lines (limit 160). Pass.
- Anchors and links in SKILL.md, always-do-patterns.md and never-do-patterns.md resolve by manual check. No absolute paths, no .github/ path, no relative dates found in the files I read.
- Never-Do rows 1-9 are sourced. Row 10 is not (see H1).

## HIGH

H1. SKILL.md:100 (Never Do, depends_on row) breaks the evidence rule. The row is tagged "(unverified)" and gives no URL. The evidence rule says Never Do is High rows only, and the alternative must be High too. The alternative "Reference attributes" has no source either.
- The row is research legacy claim W8 (U5), which the research says no source supports. Its only support is a one-line inference in the research ("references create implicit dependencies").
- The same problem repeats in never-do-provider.md:66-85 (section 4, with a WRONG block) and in never-do-patterns.md:17.
- Fix: delete the row and the section. Keep only the U5 register entry. If the "redundant depends_on" advice is wanted, put it in Ask First or a blueprint tagged (medium confidence). If the row is removed, also remove the matching tag-to-register rows in unverified-and-risks.md:56-57.

## MEDIUM

M-1. unverified-and-risks.md:55 and :22 plus SKILL.md:123. The Security Hub org-controls row carries "(medium confidence)" in the text. The register lists U3 under the Unverified table with status "(unverified)". The evidence rule requires the same tag everywhere. The research calls U3 medium. Also, absence of evidence should read "(medium confidence, absence of evidence)". Fix: move U3 to the medium table, or retag the text consistently.

M-2. SKILL.md:50. The Always Do bullet adds "(or a delegated administrator where AWS allows it)". The cited account page only says account management must be done from the root account. The delegated-admin clause is the research author's inference. It is untagged, and it is also a caveat inside an Always Do bullet. Fix: drop the clause from the bullet and move it to Ask First as (medium confidence). The same clause appears at always-do-foundation.md:9-10.

M-3. SKILL.md:68 and always-do-policies.md:44-46. The Always Do bullet is sourced, but the bullet carries a caveat about console organizations after 2026-07-10. The Terraform-created case is the research's M3 inference. It is correctly tagged only in the blueprint. Fix: remove the caveat from the bullet and move it to Ask First. Also leave "Terraform needs it" out of the bullet.

M-4. always-do-foundation.md:50-57 and 107. The strings `securityhub.amazonaws.com` and `OrganizationAccountAccessRole` are used as examples but are not marked example-only. The same applies to securityhub.amazonaws.com in always-do-policies.md:80-83, and to OrganizationAccountAccessRole in never-do-organization.md:103 and :111. The research documents the SECURITYHUB_POLICY principal dependency, so the principal is grounded. It is not grounded as a recommended default. The role name is not in the research at all. The research also says AWS prefers enabling integrations through each service's own console. Fix: add a comment "example value only" on each use.

M-5. always-do-policies.md:111-125. The terraform test example is not in the research. The research and F10 only support the generic claim that .tftest.hcl runs with mock_provider and command = plan. The assert on feature_set == "ALL" is the author's own example and is not labelled as such.
- It is valid syntax, but nearly tautological: the config sets "ALL" itself.
- It will fail if run against the skill's own snippets, because `var.accounts` and `var.management_account_role_arn` have no defaults and the test has no `variables {}` block.
- Fix: label it "illustrative example", add a `variables {}` block or defaults, and keep the Source comment for the generic claim only.

M-6. SKILL.md:129-130. "The CHANGELOG ... has no entries" and "The 6.0.0 guide has no entries" are absence-of-evidence claims, untagged. They come from main-branch or unversioned pages. Per the evidence rule they should read "(medium confidence, absence of evidence)". Fix: add the tag, and add a register row (new M) with a mapping row.

M-7. SKILL.md:79, 84, 85. Ask First rows contain caveats and URLs, which is the expected form. But SKILL.md:52-56 (Always Do) are bullets that also mix in caveats (the "when you do not need roots" part). The return_organization_only bullet at line 54 conflicts with the Always Do bullet at line 56, which needs roots[0].id (the foundation blueprint at :62-64 says it makes roots[0].id unavailable). Fix: move return_organization_only to Ask First. See also L-8.

M-8. The register's mapping table is missing a mapping row for the L3 note at SKILL.md:133 (an L id, not a tag, so only a mild breach). More important: the unverified table keeps U4 and U6 as "not cited in this skill". They are orphan U-rows with no tag anywhere. Fix: delete U4 and U6, or add one sentence in a blueprint that uses them. The research §10 lists them, so keeping them is acceptable if a note says "listed for traceability".

## LOW

L-1. SKILL.md:22. The identity-import row cites the organization resource page. F11 cites the vpc page. The research cites B4-B10 for the identity schema. The claim "Terraform >= 1.12.0" is in F11, so it is supported, but the URL cited is not the F11 URL. Cite the organization page only for the identity schema claim.

L-2. SKILL.md:112. The Import IDs row lists six import forms but cites only the policy attachment page. Cite per resource, or write "pages recorded in the bibliography".

L-3. SKILL.md:72. "Read state, not status, on organization and account attributes" cites only the account page. The organization page documents the deprecation of status on accounts[] and non_master_accounts[]. Add the organization URL.

L-4. SKILL.md:122 and unverified-and-risks.md:78. "Medium" is used as a Security Hub severity. The notation rule says never to write the bare word "medium" for severity (it collides with confidence tags). Write "moderate".

L-5. Tag mapping table column headers in unverified-and-risks.md:47 are "Tag text | Where | Register id". The policy requires "Tag text used in the skill". Rename the first column.

L-6. always-do-foundation.md:26 adds `encrypt = true` in the S3 backend. It is not in the research or F7. Mark it as an example setting or remove it.

L-7. always-do-policies.md:29-38. The attachment test_ou and root both exist at once, but the comment says "then move target_id to the root". Rewrite the comment so the two-step intent is clear.

L-8. Evidence rule: all provider-doc claims are read from raw main-branch markdown, which the rule caps at medium confidence ("main-branch example, partly read page"). The family's reference skill probably does the same. If it does, accept this as a family-level convention. Otherwise add a one-line coverage limit. L2 in the register already says raw main was used.

## Known-risk results
(a) Never Do and unverified: confirmed, see H1.
(b) Quota and behaviour values all match the research:
- SCP 10,240 chars and 10 attached; RCP 5,120 and 5 (SKILL.md:93, :114-115, never-do-organization.md:52-54).
- Closure quota "20% or 250, whichever is higher, max 1,000 per 30 days" (SKILL.md:97, :118).
- skip_destroy on the policy removes from state only; on the attachment destroy will not detach (SKILL.md:96, always-do-policies.md:47-48).
- CONSOLIDATED_BILLING to ALL needs approval only from invited accounts, then Console finalization, perpetual diff until done (SKILL.md:79).
No wrong facts found.
(c) Region: no `region` argument on any aws_organizations_* resource. `region` appears only in provider/backend config and `# WRONG` blocks (never-do-organization.md:15, :17). Pass. One note: the provider block sets `region = "us-east-1"` with the comment "Organizations is hosted in us-east-1". That is grounded in the research hosting row. It is not stated as a requirement. Pass.
(d) Example markers: see M-4 and M-5. The feature_set assert is valid HCL for a plan-time check but is not research-backed and is not labelled as the author's example.
(e) return_organization_only: the research documents it as an optional argument on organization (§3, from page B4), so the skill's treatment is grounded in the research. I could NOT verify it against the raw provider page (no WebFetch). The treatment is consistent between SKILL.md and the foundation blueprint. See M-7 for the Always Do placement.
(f) Tags and register: plain tag notation used throughout, no bold or brackets. No F#/M# family or research ids in shipped text; the only internal references are "L3" (SKILL.md:133) and "(L2)" (unverified-and-risks.md:14), which are the skill's own register ids. Every tag used has a mapping row. See M-1 (U3 inconsistency) and M-8 (orphan U4/U6). Research §9 W1-W8: W1, W2 and W4 appear only as corrections (Never rows 3, 7, 6 and eval scenario 4), which is acceptable. W8 is reproduced as a Never rule (H1). W3, W5 and W6 appear as correct facts.

## Eval file
Five scenarios (canonical, edge, rejection, trap, billing edge). The checklist needs at least four types, which are covered. Criteria are deterministic and judgeable. Every must_pass is grounded in the research. Scenario 1 has seven must_pass criteria, which is long but each is checkable. No change required.

## Grounding sample
About 36 claims were sampled (Always Do 14, Ask First 7, Never Do 10, Quick Reference 12, HCL comments 10). All trace to the research except these: delegated-admin provider clause (M-2), encrypt = true (L-6), terraform test assertion (M-5), OrganizationAccountAccessRole name (M-4), depends_on (H1), the root-SCP Terraform inference (M-3, tagged in the blueprint only).

## Priority
1. Fix H1 (remove the depends_on Never Do row, section and register mapping).
2. Fix M-1 to M-6.
3. Then re-run verify_skill.py (not run here).
