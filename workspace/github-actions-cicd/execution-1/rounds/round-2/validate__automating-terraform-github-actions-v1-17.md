# Validate r2: automating-terraform-github-actions-v1-17 (2026-10-30). Score 99.5

H1 FIXED: SKILL.md:3,63 default gate is PR review on protected main; plan-variants.md:8 `<env>` branch policy `main`.
M1 FIXED: merge plan runs under `<env>` deploy role so it can take the lock (workflow-tf-plan.md:19); PR plan `-lock=false` (M4 tagged).
M2 FIXED: `<env>-pr` and `<env>` only (SKILL.md:66,103; plan-variants.md:8-9); no `<env>-plan`.
M3 FIXED: workflow-callers.md:24,60,72 job-level detection plus `ci-gate`.
L1 not rechecked.
Known: F-001 FIXED (Verification Loop SKILL.md:121); F-008 FIXED (run_attempt in name, always-do:26, plan.md:97); F-009 FIXED (no `<repo-workflows-dir>`); F-007 FIXED (concurrency in workflow-drift.md:12). F-003 (Contents lines) not confirmed by grep: treat as open LOW.

NEW: none.
