# Shared files touched by this run

Written only by `scripts/state_event.py <slug> touch <path>`, right after this run changes a file
that other runs also own (root `apm.yml`, `apm.lock.yaml`, `CLAUDE.md`, `docs/`, another package).
Hashes: HEAD blob vs working copy at the time of the call. `check_state.py` requires every touched
path in `plan/commit-plan.json`, so G3 shows it.

| Timestamp | Path | HEAD | Now | Actor | Note |
|---|---|---|---|---|---|
