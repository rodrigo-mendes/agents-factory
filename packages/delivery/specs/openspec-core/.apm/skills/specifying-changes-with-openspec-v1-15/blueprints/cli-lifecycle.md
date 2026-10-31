# CLI Lifecycle, Layout and Inventory (OpenSpec 1.15.0)

Research date 2026-10-28. Back to [SKILL.md](../SKILL.md). No command below was executed during research or authoring; all are representative.

## Contents

- [Layout](#layout)
- [Lifecycle driven by our agents](#lifecycle-driven-by-our-agents)
- [CLI inventory relevant to automation](#cli-inventory-relevant-to-automation)
- [Verification Loop](#verification-loop)

## Layout

Sources: [concepts.md](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/concepts.md), [getting-started.md](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/getting-started.md), [cli-archive spec](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/openspec/specs/cli-archive/spec.md).

```text
openspec/
  config.yaml                      # optional project config: schema, context, rules, operations
  specs/<capability>/spec.md       # live source of truth
  changes/<change-name>/
    proposal.md
    design.md
    tasks.md
    .openspec.yaml                 # optional: schema, created, skip_specs, retire_capabilities, x-* keys
    specs/<capability>/spec.md     # delta specs
  changes/archive/YYYY-MM-DD-<change-name>/   # archived change, all artifacts kept
  schemas/<name>/schema.yaml       # optional custom schemas
```

- Change names are lowercase kebab-case; a leading number is allowed ([cli.md](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/cli.md)).
- The built-in schema `spec-driven` has artifacts proposal, specs (requires proposal), design (requires proposal), tasks (requires specs and design); apply tracks `tasks.md` ([schema.yaml](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/schemas/spec-driven/schema.yaml)).
- Schema resolution order: `--schema`, then `.openspec.yaml`, then `openspec/config.yaml`, then `spec-driven` ([customization.md](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/customization.md)).
- `config.yaml` `context` is capped at 50KB ([migration-guide](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/migration-guide.md)).

## Lifecycle driven by our agents

CLI only, no `/opsx:*` (decision G1). Flags come from [cli.md](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/cli.md).

```bash
# Representative; adapt to your environment (OpenSpec 1.15.0)
# 0. one-time, by a human (init is listed as human-only):
openspec init --tools none
# 1. scaffold a change (or write the folder directly)
openspec new change add-2fa --description "Admin 2FA" --json
# 2. agents write proposal.md, specs/<cap>/spec.md deltas, design.md, tasks.md
#    optional per-artifact guidance:
openspec instructions specs --change add-2fa --json
openspec status --change add-2fa --json     # first artifact with status "ready" = next to write
# 3. gate
openspec validate add-2fa --type change --strict --json --no-interactive
# 4. inspect parsed deltas
openspec show add-2fa --type change --deltas-only --json --no-interactive
# 5. after implementation and with tasks checked: merge deltas and move the folder
openspec archive add-2fa --yes
# 6. confirm live specs and the archive
openspec validate --specs --strict --json --no-interactive
openspec list --archived --json             # archived changes visible since v1.14.0
```

- `instructions archive` is read-only and does not archive. `openspec instructions apply --change <id> --json` returns `state` (`blocked`, `all_done`, `ready`), `progress`, `tasks` and `missingArtifacts` ([agent-contract.md](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/agent-contract.md)).
- There is no `diff` command in the v1.15.0 CLI reference; that no `openspec diff` exists is (medium confidence, absence of evidence).
- Stores and worksets are beta: "Command names, flags, and JSON shapes may change between releases". Out of scope.

## CLI inventory relevant to automation

| Command | Flags |
|---|---|
| `init [path]` | `--tools all\|none\|<ids>`, `--language`, `--force`, `--profile core\|custom`, `--no-animation`, `--copilot-cloud/--no-copilot-cloud` |
| `update [path]` | `--force`, `--dry-run`, `--json` (with `--dry-run`) |
| `list` | `--specs` / `--changes` (default), `--sort recent\|name`, `--json`; plus `--archived` and `--all` since v1.14.0 (not shown in the cli.md list) |
| `view` | interactive dashboard, human-only |
| `show [item]` | `--type change\|spec`, `--json`, `--no-interactive`, `--deltas-only` (change), `--requirements`, `--no-scenarios`, `-r/--requirement <n>` (spec) |
| `validate [item]` | `--all`, `--changes`, `--specs`, `--archived`, `--type`, `--strict`, `--json`, `--concurrency <n>` (default 6, env `OPENSPEC_CONCURRENCY`), `--no-interactive` |
| `archive [change]` | `-y/--yes`, `--skip-specs`, `--no-validate` (requires confirmation; also disables capability retirement) |
| `new change <name>` | `--description`, `--goal`, `--schema`, `--store`, `--json` |
| `status` | `--change <id>`, `--schema`, `--json` |
| `instructions [artifact]` | `--change <id>` (required non-interactively), `--schema`, `--json` |
| `templates` / `schemas` | `--schema`, `--json` / `--json`, `--store` |
| `schema init\|fork\|validate\|which` | see cli.md |
| `config` | `path`, `list`, `get`, `set [--string]`, `unset`, `reset --all --yes`, `edit`, `profile [preset]` |
| `completion generate\|install\|uninstall [shell]` | `bash`, `zsh`, `fish`, `powershell` |
| `feedback <message>` | `--body`; needs authenticated `gh` |

Source: [cli.md](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/cli.md) and [releases](https://github.com/Fission-AI/OpenSpec/releases) for the `list` additions.

## Verification Loop

```bash
# Representative; adapt to your environment (OpenSpec 1.15.0); not executed in this research
openspec --version
# expected: 1.15.0
openspec validate --all --strict --json --no-interactive
# expected: one JSON document on stdout; exit 0 if every item is valid, 1 otherwise (medium confidence, L1 and L2)
openspec validate --archived --no-interactive
# expected: exit 1 if an archived change has unchecked tasks
openspec show <change> --type change --deltas-only --json --no-interactive
# expected: the parsed deltas of the change
```

The standalone binary prints `OpenSpec <version> (standalone)` for `openspec version` ([installation.md](https://raw.githubusercontent.com/Fission-AI/OpenSpec/v1.15.0/docs/installation.md)).

Fixture check of a known-bad delta (a recommendation of the research, not an OpenSpec claim): run `openspec validate bad-change --type change --strict --json --no-interactive` against a fixture folder in a temp directory and assert exit 1 and the JSON; do not assert on the CLI's text output.
