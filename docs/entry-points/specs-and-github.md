# Specs and GitHub commands

These commands keep OpenSpec specs in step with the code and with a GitHub Project. They also draft
specs from an existing proof of concept.

Git is the source of truth. The GitHub Project is a mirror, plus an optional channel for approvals.

## Commands

| Job | Command | Routes to | Argument hint |
|---|---|---|---|
| Propose a spec change after the code drifted | [`/syncing-spec-from-code`](../../packages/delivery/protocol/handoff-core/README.md#syncing-spec-from-code) | `spec-synchronizer` | `<change-id or handoff dir> [--repo] [--profile]` |
| Mirror a change to its GitHub Project | [`/syncing-openspec-to-github`](../../packages/delivery/specs/openspec-github/README.md#syncing-openspec-to-github) | `openspec-github-syncer` | `<change-id> --profile <yaml> [--stage E<n>] [--apply]` |
| Draft specs from a POC (inline) | [`/bootstrapping-spec-from-poc`](../../packages/delivery/specs/openspec-poc/README.md#bootstrapping-spec-from-poc) | inline | `back=<dir> front=<dir> [id=] [repo=] [hint=] [promote=]` |

## Examples

Check whether the code drifted from the spec, and propose a change:

```
/syncing-spec-from-code list-tenant-items
```

Preview the GitHub Project update (dry run; nothing is changed):

```
/syncing-openspec-to-github list-tenant-items --profile <your-profile.yaml>
```

Apply it after you check the preview:

```
/syncing-openspec-to-github list-tenant-items --profile <your-profile.yaml> --apply
```

Draft specs from a POC with a back end and a front end:

```
/bootstrapping-spec-from-poc back=poc/api front=poc/web id=orders-poc
```

## Safety

- The GitHub sync is a dry run unless you pass `--apply`.
- The syncer pushes and reports status. It does not read approvals; the orchestrator does.
- A POC is only a source of questions. Shortcuts in the POC (hard-coded secrets, open CORS, mock
  data) become open questions, never requirements.
- `/bootstrapping-spec-from-poc` produces a draft. Promoting it to a change needs your yes
  (`promote=<change-id>`).

## Related

- Packages: [`handoff-core`](../../packages/delivery/protocol/handoff-core/README.md),
  [`openspec-core`](../../packages/delivery/specs/openspec-core/README.md),
  [`openspec-github`](../../packages/delivery/specs/openspec-github/README.md),
  [`openspec-poc`](../../packages/delivery/specs/openspec-poc/README.md),
  [`github-core`](../../packages/delivery/github/github-core/README.md).
- Next: the SaaS orchestrator uses these specs: [saas-quarkus-aws](saas-quarkus-aws.md).
