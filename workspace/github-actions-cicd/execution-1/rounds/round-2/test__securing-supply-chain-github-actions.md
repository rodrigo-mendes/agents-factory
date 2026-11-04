# Test P6 r2 - securing-supply-chain-github-actions (S1, S2)

Own-context simulation, 2026-10-30. S1 PASS, S2 PASS. Score 100.

| r1 finding | Status | Evidence |
|---|---|---|
| S-1 MEDIUM write scopes on default PR job | FIXED | workflow-callers.md:20-22 `security` job `permissions: { contents: read }`; :26-35 separate `code-security` job (`if: vars.CODE_SECURITY_ENABLED == 'true'`) is the only one with `security-events`/`pull-requests: write`; scenario S1:11 and S2:26 updated; workflow-licensed-jobs.md:21 `_code-security.yml` |
| S-2 MEDIUM image hand-off names | FIXED | workflow-callers.md:65 `_image-publish.yml`, :74 `image-ref: ${{ needs.publish.outputs.image-ref }}`; matches images skill outputs `digest`, `image-ref` |
| S-3 LOW pull credential scope | FIXED | workflow-security-scan.md:15-16 `environment` input, secrets read in the scan job; workflow-callers.md:76,82 environment secret per rule 10, Free exception warned |

New findings: none in this skill. Cross-skill: the composing catalog still misdescribes this skill's blocks (see test__composing-github-actions-pipelines.md N-1).
