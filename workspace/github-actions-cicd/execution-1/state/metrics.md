# Metrics (cost estimated vs actual)

Written only by `scripts/state_event.py <slug> metric ...`. The P3 pilot writes the estimate per
unit and for the whole run; every stage writes its actual. `check_state.py` compares the actual sum
with `token_budget` of `PACKAGE_BRIEF.md`.

| Timestamp | Scope | Kind | Tokens | Minutes | Actor | Note |
|---|---|---|---|---|---|---|
| 2026-10-30T10:28:18 | research | actual | 171659 | 9 | orchestrator | pilot terraform research |
| 2026-10-30T10:35:04 | author | actual | 163511 | 6 | orchestrator | pilot terraform author |
| 2026-10-30T10:38:43 | validate | actual | 156739 | 3 | orchestrator | pilot validate |
| 2026-10-30T10:38:45 | run | estimate | 6500000 |  | orchestrator | remaining: 8 units x ~493k (research+author+validate) = ~3.9M; P5 package ~0.4M; P6 3 rounds incl test/audit/fix ~2.2M |
| 2026-10-30T11:39:17 | author | actual | 88245 |  | orchestrator | P5 rules |
| 2026-10-30T11:39:39 | author | actual | 100908 |  | orchestrator | P5 executor agent + command |
| 2026-10-30T11:40:59 | author | actual | 102859 |  | orchestrator | P5 reviewer agent |
| 2026-10-30T11:41:15 | author | actual | 94412 |  | orchestrator | P5 README + apm.yml |
| 2026-10-30T12:30:09 | run | actual | 6100000 |  | orchestrator | approx cumulative through round-1 (research 1.6M, author 1.7M, P5 0.4M, round-1 1.3M, orchestrator overhead) |
| 2026-10-30T12:31:49 | fix | actual | 105930 |  | orchestrator | r1 fix aws-oidc |
| 2026-10-30T12:34:18 | fix | actual | 260381 |  | orchestrator | r1 fix oci + composing |
| 2026-10-30T12:35:04 | fix | actual | 111779 |  | orchestrator | r1 fix images |
| 2026-10-30T12:35:55 | fix | actual | 152298 |  | orchestrator | r1 fix terraform |
| 2026-10-30T12:37:51 | fix | actual | 224547 |  | orchestrator | r1 fix blast + nextjs |
| 2026-10-30T12:39:15 | fix | actual | 238937 |  | orchestrator | r1 fix supply + java |
| 2026-10-30T12:42:45 | fix | actual | 127100 |  | orchestrator | r1 fix package |
| 2026-10-30T12:50:48 | round | actual | 548564 |  | orchestrator | round-2 4 reviewers |
