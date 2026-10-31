---
saved-by: building-agent-packages (orchestrator), summary of quality-validator inline report
round: 2
date: 2026-10-29
---
# Round 2 — openspec-github
Scores: bridge skill 92.5 · command 100 · agent 99.5 · instructions 99.5 · README 100. 0 HIGH.
All 25 round-1 findings CLOSED (groupA M1-M3 + LOWs; audit F1, F2, F4-F8, F11-F13).
New: N1 MEDIUM local "App token" refused by preflight (docs say machine-user or App) · N2 MEDIUM publish path filter bypassable via rename (`--name-only` lists only destination) · N3 LOW applyTo `**/openspec-github/**` too broad · N4 LOW F5/F7 residuals undocumented · N5 LOW mapping.md mismatches · N6 LOW preflight order in cli-contract · N7 LOW read-only token valid during npm (unverified) · N8 LOW no test for publish path filter.
Note: register counts in this report predate the R17 downgrade (now 8 unverified / 9 medium).
