# P9 Commit

Back to [SKILL.md](../../SKILL.md).

1. Propose groups (e.g. skills / agent+rules / package+root apm.yml+lock / .claude regenerated / docs / workspace research) as a `plan.json` for `scripts/commit_groups.py`.
2. **G3**: show groups, messages, files per group and the leftover decision list; wait for an explicit yes.
3. `scripts/commit_groups.py plan.json` (dry run), then `--apply`. It stages explicit paths only and refuses stray files.
4. Commit messages follow the repo history style plus the attribution lines in the session reminder.
5. **G4**: never push. Tell the user the commits are local and the push is theirs.

If the harness blocks `git push`, report it; do not look for a workaround.
