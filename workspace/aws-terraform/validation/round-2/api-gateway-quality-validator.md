# Quality validation round 2 — provisioning-aws-api-gateway-v6

Written by the orchestrator from the validator's returned report. Counts: HIGH 1 · MEDIUM 2 · LOW 9. 54 claims sampled, no wrong factual claim. Round 1: 11 of 19 FIXED, remaining partial.

Structural: Never rows 14 = 14 (4 provider-migration + 4 REST + 6 HTTP/WebSocket), all anchors resolve; Always Do 21 bullets High-only; Security Hub APIGateway.1-5 and 8-11 only; 6.0 removals correct; REST vs v2 not mixed (cosmetic L-8).

HIGH N-H1: false read date on the Terraform 1.17.0 claim (SKILL.md:26 no URL/date; unverified-and-risks.md:9-10 and bibliography item 42 dated 2026-10-14, before the release). Fix: add the v1.17 CHANGELOG (2026-10-22), re-date releases page 2026-10-23, cite on SKILL.md:26.
MEDIUM N-M1: stale reference patch "1.16.6" (SKILL.md:19, unverified-and-risks.md:9,:104) → 1.16.7 (2026-10-22) or "1.16.x". N-M2: internal wording "Unit research date" (unverified-and-risks.md:3), "Pages not re-read" (:39).
LOW L-1 bullet SKILL.md:57 two claims; evaluation-scenarios.md:20 requires "a destination separate from the execution-log group" (no source). L-2 bibliography header lists items 1,39,40,41 as individually dated but not 42. L-3 U2 tagged nowhere ("not used" acceptable). L-4 evaluation-scenarios.md:91 (medium confidence) tag not in mapping. L-5 row SKILL.md:85 cites only Security Hub for provider-page claims → add integration page. L-6 upgrade path omits the F17 steps. L-7 never-do-provider-migration.md:87 no constraints-page source for ~> 6.69. L-8 always-do-http-domain-access.md:57-64 REST execution_arn fragment in the v2 file → comment. L-9 APIGateway.11 names abbreviated.
