# Scores (one row per review report)

Written only by `scripts/state_event.py <slug> score ...`, one row per validate/test/audit report of
the pilot (`--round pilot`) or a P6 round. The latest row of (round, target, kind) wins. The
dashboard and each round's `scoreboard.md` are generated from this file; never write a scoreboard
by hand. Skill and package scores use 0-100 (`100 - 6/HIGH - 2.5/MEDIUM - 0.5/LOW`); the audit uses 0-10.

| Timestamp | Round | Target | Kind | Score | HIGH | MEDIUM | LOW | Pass | Total | Actor | Note |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-10-30T12:47:17 | round-2 | composing-github-actions-pipelines | validate | 97.5 | 0 |  |  |  |  | orchestrator |  |
| 2026-10-30T12:47:17 | round-2 | automating-terraform-github-actions-v1-17 | validate | 99.5 | 0 |  |  |  |  | orchestrator |  |
| 2026-10-30T12:47:18 | round-2 | federating-github-actions-aws-oidc | validate | 97.5 | 0 |  |  |  |  | orchestrator |  |
| 2026-10-30T12:47:18 | round-2 | federating-github-actions-oci | validate | 99 | 0 |  |  |  |  | orchestrator |  |
| 2026-10-30T12:47:19 | round-2 | building-java-github-actions | validate | 99 | 0 |  |  |  |  | orchestrator |  |
| 2026-10-30T12:47:56 | round-2 | package | audit | 9.7 | 0 | 1 | 2 |  |  | orchestrator |  |
| 2026-10-30T12:50:30 | round-2 | publishing-container-images-github-actions | validate | 99.5 | 0 |  |  |  |  | orchestrator |  |
| 2026-10-30T12:50:30 | round-2 | building-nextjs-github-actions-v16-4 | validate | 99.5 | 0 |  |  |  |  | orchestrator |  |
| 2026-10-30T12:50:31 | round-2 | limiting-blast-radius-github-actions-deploys | validate | 99 | 0 |  |  |  |  | orchestrator |  |
| 2026-10-30T12:50:31 | round-2 | securing-supply-chain-github-actions | validate | 97 | 0 |  |  |  |  | orchestrator |  |
| 2026-10-30T12:50:32 | round-2 | package | validate | 91 | 0 |  |  |  |  | orchestrator |  |
| 2026-10-30T12:50:32 | round-2 | automating-terraform-github-actions-v1-17 | test | 97 |  |  |  |  |  | orchestrator | all listed scenarios PASS |
| 2026-10-30T12:50:33 | round-2 | securing-supply-chain-github-actions | test | 97 |  |  |  |  |  | orchestrator | all listed scenarios PASS |
| 2026-10-30T12:50:33 | round-2 | federating-github-actions-oci | test | 97 |  |  |  |  |  | orchestrator | all listed scenarios PASS |
| 2026-10-30T12:50:34 | round-2 | building-cicd-pipelines | test | 97 |  |  |  |  |  | orchestrator | all listed scenarios PASS |
| 2026-10-30T12:50:34 | round-2 | composing-github-actions-pipelines | test | 97 |  |  |  |  |  | orchestrator | all listed scenarios PASS |
| 2026-10-30T12:50:35 | round-2 | limiting-blast-radius-github-actions-deploys | test | 97 |  |  |  |  |  | orchestrator | all listed scenarios PASS |
| 2026-10-30T12:54:42 | pilot | automating-terraform-github-actions-v1-17 | validate | 91 | 0 | 2 | 8 |  |  | orchestrator | round-0 pilot |
| 2026-10-30T12:54:43 | round-1 | composing-github-actions-pipelines | validate | 90 | 1 | 1 | 3 |  |  | orchestrator |  |
| 2026-10-30T12:54:43 | round-1 | composing-github-actions-pipelines | test | 100 |  |  |  | 5 | 5 | orchestrator |  |
| 2026-10-30T12:54:44 | round-1 | automating-terraform-github-actions-v1-17 | validate | 86 | 1 | 3 | 1 |  |  | orchestrator |  |
| 2026-10-30T12:54:45 | round-1 | automating-terraform-github-actions-v1-17 | test | 100 |  |  |  | 5 | 5 | orchestrator |  |
| 2026-10-30T12:54:46 | round-1 | federating-github-actions-aws-oidc | validate | 90 | 1 | 1 | 3 |  |  | orchestrator |  |
| 2026-10-30T12:54:46 | round-1 | federating-github-actions-aws-oidc | test | 100 |  |  |  | 5 | 5 | orchestrator |  |
| 2026-10-30T12:54:47 | round-1 | federating-github-actions-oci | validate | 90 | 1 | 1 | 3 |  |  | orchestrator |  |
| 2026-10-30T12:54:48 | round-1 | federating-github-actions-oci | test | 100 |  |  |  | 5 | 5 | orchestrator |  |
| 2026-10-30T12:54:49 | round-1 | building-java-github-actions | validate | 92.5 | 0 | 2 | 5 |  |  | orchestrator |  |
| 2026-10-30T12:54:49 | round-1 | building-java-github-actions | test | 100 |  |  |  | 4 | 4 | orchestrator |  |
| 2026-10-30T12:54:50 | round-1 | publishing-container-images-github-actions | validate | 90 | 1 | 1 | 3 |  |  | orchestrator |  |
| 2026-10-30T12:54:51 | round-1 | publishing-container-images-github-actions | test | 100 |  |  |  | 5 | 5 | orchestrator |  |
| 2026-10-30T12:54:52 | round-1 | building-nextjs-github-actions-v16-4 | validate | 90.5 | 0 | 3 | 4 |  |  | orchestrator |  |
| 2026-10-30T12:54:52 | round-1 | building-nextjs-github-actions-v16-4 | test | 100 |  |  |  | 5 | 5 | orchestrator |  |
| 2026-10-30T12:54:53 | round-1 | limiting-blast-radius-github-actions-deploys | validate | 88.5 | 0 | 4 | 3 |  |  | orchestrator |  |
| 2026-10-30T12:54:54 | round-1 | limiting-blast-radius-github-actions-deploys | test | 100 |  |  |  | 5 | 5 | orchestrator |  |
| 2026-10-30T12:54:55 | round-1 | securing-supply-chain-github-actions | validate | 93 | 0 | 2 | 4 |  |  | orchestrator |  |
| 2026-10-30T12:54:55 | round-1 | securing-supply-chain-github-actions | test | 100 |  |  |  | 5 | 5 | orchestrator |  |
| 2026-10-30T12:54:56 | round-1 | package | validate | 86 | 1 | 2 | 6 |  |  | orchestrator |  |
| 2026-10-30T12:54:57 | round-1 | building-cicd-pipelines | test | 67 |  |  |  | 2 | 3 | orchestrator | scenario 3 PARTIAL |
| 2026-10-30T12:54:58 | round-1 | audit | audit | 7.8 | 0 | 4 | 3 |  |  | orchestrator |  |
