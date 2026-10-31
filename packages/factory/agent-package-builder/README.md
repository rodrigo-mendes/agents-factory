# agent-package-builder

One inline orchestrator skill, `building-agent-packages`, that drives the factory's existing workers
(`framework-researcher`, `artifact-author`, `quality-validator`, `skill-evaluator`,
`architecture-auditor`) from a brief to a committed APM package (skills + agent + rules).

## Use

```
/building-agent-packages <brief | research_dir=<dir> | resume=<dir>>
```

Three entry modes, one pipeline: `new` (list of frameworks and/or needs), `from-research` (a folder of
finished research), `resume` (continue an interrupted run; works with or without `PIPELINE_STATE.md`).
Quality loop: `rounds=N` (default 3) of validate, test, audit, fix, with early exit.

Human gates: **G1** scope/version/units · **G2** pilot review · **G3** commit plan · **G4** push (always manual).

## Design notes

- Inline skill, not a forked agent: workers are `context: fork` + `disable-model-invocation`, so the
  orchestrator launches their subagents directly with the worker `SKILL.md` as spec; subagents cannot nest.
- No new subagent. Runtime dependency on the worker packages is documented, not declared (as in `evaluating`).
- Scripts (stdlib Python, read-only except `commit_groups.py --apply`): `verify_skill.py`,
  `verify_package.py`, `normalize_tags.py`, `inspect_workspace.py`, `check_counts.py`, `commit_groups.py`.
- Origin: distilled from building the Camel Quarkus package (see `blueprints/known-failures.md`).
- Step 2 (not built): a "pipeline mode" in the workers (no P3 gate, fixed output path, write straight to `packages/`).
