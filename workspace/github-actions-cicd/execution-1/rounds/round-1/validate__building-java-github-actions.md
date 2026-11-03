# Validate: building-java-github-actions (P6 r1, 2026-10-30)

Score: 92.5 (0 HIGH, 2 MEDIUM, 5 LOW). SKILL.md 140 lines. SHAs match F4, F5, F10, F23, F24; versions match F11-F13. Rule 16 table in workflow-callers.md:64-71 matches. Verification Loop, 4 scenarios, register counts (8/0/8/6) correct. Contract (`tool`, `java-version`, `package`, `working-directory`; `artifact-name`, `artifact-digest`) is internally consistent but not what composing's catalog or monorepo example uses (see composing H1).

## MEDIUM
- M1 (composing Always Do, blueprints/workflow-java-build.md:27-28): the `build` job has no `timeout-minutes` (0 occurrences in the whole skill; also gradle-build.md:75 `submit` job). Default is 360. Fix: add e.g. 30 and justify.
- M2 (A4/B3, composite-setup-java-build.md:37; workflow-java-build.md:46): passes `cache-read-only` to `actions/setup-java` with no cited source. The register M3 tags only the PR read-only recommendation, not the input name; composing treats the comparable setup-node input names as unverified. An unknown input only warns, so the PR read-only intent may silently not apply. Fix: confirm against the v6.1.0 README or tag (unverified) and register it.

## LOW
- L1 (composing Always Do): `ci-orders.yml` (workflow-callers.md:7-29) has no PR concurrency group; it also uses `paths` while only noting the gate in prose.
- L2: `actions/checkout` without `persist-credentials: false` (workflow-java-build.md:36, gradle-build.md:79).
- L3 (rule 6/7, gradle-build.md:73-74): `contents: write` at workflow level; move to the job.
- L4 (A4): 17 dangling "F<n>" / "family rule" references across 8 blueprint files.
- L5 (rule 3, SKILL.md:56): "Pin Maven 3.10.0 with the wrapper, because runners ship 3.9.x" mixes a rule and a fact; fine if kept as rationale, flag for consistency.
