# Questions and traceability table

Back to [SKILL.md](../SKILL.md). Policy: factory rules 5 and 6 (a precondition that cannot be read from the spec becomes a numbered question; traceability is checked by script).

## Numbered questions

When a scenario needs a precondition the spec does not write (identity, existing data, configuration):

1. Do not write a `Given`. Add `# QUESTION Q<n>: <question> (not stated in the spec)` under the scenario.
2. Number questions across the whole run, Q1, Q2, ...
3. Hand them to the caller as a list: `Q<n> | requirement | scenario | question | impact if guessed`.
4. When the answer arrives, the spec owner updates `spec.md` first; only then write the `Given`. A `Given` added without a spec change breaks the one-way derivation.

| Q | Requirement | Scenario | Question | Impact if guessed |
|---|---|---|---|---|
| Q1 | R1 | empty tenant | Does R1 require an authenticated caller? | the feature would assert behaviour nobody approved |

## Traceability table

One row per spec scenario, produced from the script output (`--json`), never from memory:

| Requirement | Scenario | Feature file:line | Status |
|---|---|---|---|
| R1 | named visitor | src/test/resources/features/greeting.feature:9 | covered |
| R1 | blank name | not found | missing |

Status values: `covered` (matching tag and name found), `missing` (spec scenario without a feature scenario), `orphan` (a feature scenario with no requirement tag or an unknown one; list these in a second table with the feature file:line and the reason).

## Reading the script output

- `covered` entries carry `feature` and `line`; `missing` entries carry the spec file and line.
- `summary.per_requirement` gives covered over total scenarios per requirement.
- Matching is by requirement tag plus scenario name (case-insensitive, whitespace-normalized). A renamed scenario therefore shows as `missing`: keep names verbatim.
- Exit 1 means gaps: fix the feature, not the script. Exit 2 means no spec requirements or no `.feature` files were found: check the paths.
