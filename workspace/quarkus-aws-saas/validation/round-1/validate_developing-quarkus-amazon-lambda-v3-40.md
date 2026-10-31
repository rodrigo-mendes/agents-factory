# Validate — developing-quarkus-amazon-lambda-v3-40 (pilot, round 1)

Worker: quality-validator, 2026-10-28. The worker refused to write this file; the orchestrator wrote it from the inline report.
Score: **90/100** (0 HIGH, 3 MEDIUM, 5 LOW). Orchestrator re-check: all 3 MEDIUM confirmed against the file.

| ID | Sev | Location | Finding | Fix hint | Re-check |
|---|---|---|---|---|---|
| M1 | MEDIUM | SKILL.md:76; never-do-patterns.md:55-57 | Never Do ✅ alternative lists `java25` (unverified for Quarkus 3.40, SKILL.md:22/61) and `provided.al2023` (medium, register M1) | alternative = "a non-deprecated AL2023 runtime from the AWS table"; point to Ask First C2; drop/tag `java25` | confirmed |
| M2 | MEDIUM | SKILL.md:19 | "default builder image `…:jdk-21`" vs family fact: default `mandrel`, the image is in examples | "default `mandrel`; the guide's examples use …:jdk-21" | confirmed |
| M3 | MEDIUM | SKILL.md:93 vs snapstart.md:25 | "(all default `true`)" includes `enabled`, whose default is "page not recorded" | scope `true` to the 4 sub-keys only | confirmed |
| L1 | LOW | always-do (149), evaluation-scenarios (129), never-do (106) | no Contents list on files > 100 lines | add Contents | — |
| L2 | LOW | SKILL.md:75 | SnapStart-on-native ✅ reads like a choice | append "(Ask First C1)" | — |
| L3 | LOW | SKILL.md Quick Navigation | no link to Verification Loop | link packaging-and-artifact-contract#verification-loop | — |
| L4 | LOW | SKILL.md:19 | bare "L1" id | "(coverage limit L1 in the register)" | — |
| L5 | LOW | ask-first-decisions.md:24 | "Nothing recorded" | "page not recorded" | — |
