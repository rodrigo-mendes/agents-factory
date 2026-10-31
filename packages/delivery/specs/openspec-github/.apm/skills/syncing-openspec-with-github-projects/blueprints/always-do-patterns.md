# Always-do patterns

Code and commands behind the Always Do list. Back to [SKILL.md](../SKILL.md). Sources: family facts
F2-F8 (read 2026-10-29), family rules 4-12, and the script contract.

## Contents

- [Dry-run, then apply with a relayed approval](#dry-run-then-apply-with-a-relayed-approval)
- [Read divergence with status](#read-divergence-with-status)
- [Event text through env](#event-text-through-env)
- [App token with narrow permissions](#app-token-with-narrow-permissions)
- [Verify vendored scripts first](#verify-vendored-scripts-first)
- [Trust by exact bot login](#trust-by-exact-bot-login)
- [Tracker file](#tracker-file)

## Dry-run, then apply with a relayed approval

```bash
python scripts/gh_projects_sync.py push . --change list-tenant-items --profile handoff-profile.yaml
# PLAN gh api -X POST repos/acme/shop/issues --input - < stdin(812 chars)
# planned 9 write(s); stage E3
python scripts/gh_projects_sync.py push . --change list-tenant-items --profile handoff-profile.yaml --apply
```

The second command runs only when the brief carries the orchestrator's relayed approval line for
tracker writes. A relay is not a new approval: quote it in the report.

## Read divergence with status

```bash
python scripts/gh_projects_sync.py status . --change list-tenant-items --profile handoff-profile.yaml
# DIVERGE task:T2: field Status='Todo', want 'In progress'     (exit 2)
```

Report each `DIVERGE` line. Exit 2 is a finding, not a failure; the fix is `push` (git wins), never an edit on GitHub.

## Event text through env

```yaml
- name: Evaluate the command
  env:
    COMMENT_BODY: ${{ github.event.comment.body }}
    COMMENT_AUTHOR: ${{ github.event.comment.user.login }}
  run: python "$VENDOR/gate_command.py" evaluate . --profile "$PROFILE" --apply
```

`VENDOR` stands for the vendored scripts folder (the `.github` directory's `openspec-github` subfolder).
The script reads the variables itself; nothing from the comment is spliced into the shell text.

## App token with narrow permissions

```yaml
- uses: actions/create-github-app-token@64ab729a6294000f5aa4a4bc0b73d1f32bc45510  # v3.3.0
  with:
    client-id: ${{ vars.OPENSPEC_APP_CLIENT_ID }}
    private-key: ${{ secrets.OPENSPEC_APP_PRIVATE_KEY }}
    permission-issues: write
    permission-organization-projects: write
```

`client-id` is the recommended input; `permission-*` narrows the default of all installation permissions (F8).

## Verify vendored scripts first

```bash
python "$VENDOR/_vendor.py" verify "$VENDOR"   # exit 1 when a file differs from MANIFEST.sha256
```

## Trust by exact bot login

```python
if (conf.get("user") or {}).get("login") != tracker.get("bot_login"):
    return None          # not written by the gate identity: ignored by pull
```

## Tracker file

```yaml
kind: github-projects
owner: acme
owner_type: organization
project_number: 7
repo: acme/shop
approval_source: chat            # github or both is an Ask First decision
approvers: [alice, bob]
bot_login: "openspec-bot[bot]"   # quote: contains [ ]
```
