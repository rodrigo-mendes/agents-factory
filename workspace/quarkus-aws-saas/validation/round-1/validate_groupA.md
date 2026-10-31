# Round 1 VALIDATE — group A (quality-validator, 2026-10-28; saved by orchestrator from the inline report)

| Skill | Score | HIGH | MED | LOW |
|---|---|---|---|---|
| developing-quarkus-amazon-lambda-v3-40 (U1) | 91.0 | 0 | 3 | 3 |
| developing-quarkus-amazon-lambda-http-v3-40 (U2) | 89.5 | 1 | 1 | 4 |
| securing-quarkus-lambda-cognito-v3-40 (U3) | 91.0 -> 85.0 after re-triage | 0 -> 1 | 3 -> 2 | 3 |
| integrating-quarkus-amazon-data-v3-40 (U4) | 88.0 | 1 | 2 | 2 |
| testing-quarkus-amazon-lambda-v3-40 (U6) | 91.0 | 0 | 3 | 3 |

HIGH (orchestrator re-check: all confirmed)
- U2 SKILL.md:53/:81/:98 + build-output:19, always-do:94, never-do:84, scenarios:114 — `enable-security` default `false` stated untagged in Always/Never; family fact tags the default (medium). Fix: Always/Never on guide text ("opt-in; add =true"); tag default in Quick Ref/config/scenario; register row.
- U4 SKILL.md:58-59 — Always Do bullets embed (medium confidence) (tenant use of LeadingKeys / S3 prefix). Fix: keep High parts in Always Do; tenant application stays in Ask First C4.
- U3 (raised from MEDIUM by orchestrator after verifying AWS access-token page) SKILL.md:49, always-do 32-35, K2, scenario 27 — Principal name `cognito:username` holds only for ID tokens; access tokens carry `username`, M2M tokens neither username nor cognito:groups. Fix: caveat in K2/pattern 2/Option A: with access tokens the guide's Principal path does not match (Quarkus behaviour unverified); identify users by `sub`; M2M → no roles from cognito:groups.

MEDIUM / LOW (to fix in the same pass where mechanical)
- U1: java25 untagged in ✅ (never-do:54) and in migration-notes:20, packaging:57, scenarios:91 (rule 9); dev-port alias still (unverified) → (medium) per family fact (migration-notes:13, packaging:71, register U4 → M); LOW: rollback consequence of 14-day snapshot deletion; Maven 3.9.16 tag align with U2; "Default candidate" wording (rule 11).
- U2: Always Do 8 / Never Do 2 rest on L4-summarised source → tag (medium) or move; cite exact file URL; LOW: Maven tag, migration-notes:12 runtime wording, ask-first "Default" wording, unsourced "Never configure A and B".
- U3: N7/N4 ✅ use Option B code (rule 9); map-cognito-to-roles / cognito-role-claim / claim-matcher defaults untagged vs enable-security tagged (same page, partial read); LOW: B/B2 labels, blank line, unsourced "Count 401/403".
- U4: Never Do 2 rests on M3 inference; region claim double-tagged M8+I2 → single tag; LOW: per-key URLs, whitepaper quote in never-do.
- U6: Never Do 3 ❌ is medium; enable-security default untagged; mock 500 status double-tagged + directory URL; LOW: LambdaClient-on-classpath claim untagged; "Default choice" wording.
- Cross-skill: enable-security default tag (U2,U3,U6 consistent with family fact); Maven 3.9.16 tag (U1 vs U2).
