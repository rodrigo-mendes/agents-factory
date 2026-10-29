# P9 Commit

Back to [SKILL.md](../../SKILL.md).

1. Every `touch`ed shared file goes into a group. Propose groups (e.g. skills / agent+rules / package+root apm.yml+lock / .claude regenerated / docs / workspace research) as `execution-<N>/plan/commit-plan.json` for `scripts/commit_groups.py`.
2. `scripts/check_state.py workspace/<slug>` must pass. **G3**: show groups, messages, files per group and the leftover decision list; wait for an explicit yes; record it with `state_event.py ... gate G3 --scope ... --words ...`.
3. `scripts/commit_groups.py execution-<N>/plan/commit-plan.json` (dry run), then `--apply`. It stages explicit paths only and refuses stray files.
4. Commit messages follow the repo history style plus the attribution lines in the session reminder.
5. `retro add` at least one lesson; `known-failure` rows are shown to the user as proposed additions to `blueprints/known-failures.md` (a separate change). `state_event.py ... phase P9 done`, then `shared-unlock` and `unlock`. **G4**: never push. Tell the user the commits are local and the push is theirs.

If the harness blocks `git push`, report it; do not look for a workaround.
