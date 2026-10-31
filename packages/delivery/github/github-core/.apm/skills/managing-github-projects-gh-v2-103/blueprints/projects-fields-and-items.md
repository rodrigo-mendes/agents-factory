# Projects, fields and items (gh 2.103.x)

Back to [SKILL.md](../SKILL.md). Sources fetched 2026-10-29.

## Resolve IDs once and cache them

```bash
gh api graphql -F number=7 -f owner=my-org -f query='
  query($owner:String!,$number:Int!){ organization(login:$owner){ projectV2(number:$number){ id
    fields(first:50){ nodes{
      ... on ProjectV2FieldCommon { id name dataType }
      ... on ProjectV2SingleSelectField { options { id name } }
      ... on ProjectV2IterationField { configuration { iterations { id startDate } } } } } } } }'
```

- Cache the project node ID, field IDs and single-select option IDs; 50 is the documented maximum of fields per project.
- Requesting `dataType` on `ProjectV2FieldCommon` is (medium confidence): the official guide example requests only `id name`.
- For a user-owned project replace `organization(login:)` with `user(login:)`.
- Source: https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects

## gh project commands

```bash
gh project field-list 7 --owner my-org -L 100 --format json
gh project item-list 7 --owner my-org -L 1000 --format json
gh project item-add 7 --owner my-org --url "https://github.com/my-org/repo/issues/42" --format json
gh project item-archive 7 --owner my-org --id "$ITEM_ID"          # --undo restores
```

- Defaults: `-L 30` for `item-list`, `field-list`, `project list`. Source: https://cli.github.com/manual/gh_project_item-list
- `item-add` takes the issue `--url` and returns the project item; "Adding an existing item returns the existing item's ID". Source: https://cli.github.com/manual/gh_project_item-add
- The `--format json` key paths (`.id` of `item-add`, `.items[].content.url`, `.fields[].options`) are (medium confidence): the manual does not document the shape and the only evidence is a test file on trunk (https://raw.githubusercontent.com/cli/cli/trunk/pkg/cmd/project/shared/queries/export_data_test.go). Verify with one live call, or use the GraphQL selection set above.
- 2.98.0 fixed `item-add` output for non-TTY; parse it only with `--format json` (medium confidence). Source: https://github.com/cli/cli/releases

## Field types and creation

| Type | `item-edit` flag | GraphQL value | Created by gh? |
|---|---|---|---|
| Text | `--text` | `text` | yes |
| Number | `--number` | `number` (Float) | yes |
| Date | `--date YYYY-MM-DD` | `date` (Date) | yes |
| Single select | `--single-select-option-id` | `singleSelectOptionId` | yes, with `--single-select-options` |
| Iteration | `--iteration-id` | `iterationId` | no |
| Multi select | none in gh | `multiSelectOptionIds` | no |

- `gh project field-create --data-type` accepts only TEXT, SINGLE_SELECT, DATE and NUMBER. Source: https://cli.github.com/manual/gh_project_field-create
- ITERATION and MULTI_SELECT exist in the GraphQL `ProjectV2FieldType` enum; how to create them through the API is (unverified). Create them once in the UI and let scripts read the IDs. Source: https://docs.github.com/en/graphql/reference/projects
- Clear a value with `--clear`; one field per `item-edit` call for non-draft items. Source: https://cli.github.com/manual/gh_project_item-edit

## Name-based edit (gh 2.97.0 or newer)

`gh project item-edit` also accepts `--field` and `--value` (names resolved at runtime), and `item-list --field` returns named columns. Scripts should prefer ID flags: names can be renamed and add a lookup per call. Source: https://github.com/cli/cli/releases/tag/v2.97.0

## GraphQL mutations for projects

| Need | Mutation |
|---|---|
| Add an issue or PR | `addProjectV2ItemById(projectId, contentId)` returns `item { id }` |
| Set a value | `updateProjectV2ItemFieldValue(projectId, itemId, fieldId, value)` |
| Clear a value | `clearProjectV2ItemFieldValue` |
| Archive | `archiveProjectV2Item` |
| Draft item | `addProjectV2DraftIssue` (CLI: `gh project item-create --title --body`) |

Source: https://docs.github.com/en/graphql/reference/projects (partly read: targeted types only).

Do not use `updateProjectV2ItemFieldValue` for Labels, Assignees, Milestone or Repository; use the issue commands in [issues, sub-issues and comments](./issues-sub-issues-and-comments.md).

## Draft items vs real issues

Draft items have no repository issue, no comments and no sub-issues. Real issues need a repository and support all three. Ask the user which one an escalation needs before choosing. Sources: https://cli.github.com/manual/gh_project_item-create , https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects

## Size limits

- Up to 50 fields per project; "a maximum of 50,000 items across both active views and the archive page". Sources: https://docs.github.com/en/issues/planning-and-tracking-with-projects/learning-about-projects/about-projects , https://docs.github.com/en/issues/planning-and-tracking-with-projects/managing-items-in-your-project/adding-items-to-your-project
- The 50,000 cap counts archived items too, so archiving does not free capacity.
