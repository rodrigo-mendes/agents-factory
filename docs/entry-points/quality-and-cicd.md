# Acceptance-test and CI/CD commands

## Acceptance tests from specs

`/building-acceptance-tests` turns an OpenSpec change into Gherkin features and a Cucumber suite on
Quarkus 3.40.

| Argument | Meaning |
|---|---|
| `<change-dir>` or `<spec-root>` | The OpenSpec change or the spec root to read. |
| `<project-dir>` | The Quarkus project to write the tests into. |
| `mode=features-only` | Write only the `.feature` files, traced to the spec. |
| `mode=full` | Write the features, step definitions and the integration test. This is the default. |

```
/building-acceptance-tests openspec/changes/add-greeting ./service mode=features-only
/building-acceptance-tests openspec/changes/add-greeting ./service mode=full
```

Start with `features-only`, review the scenarios against the spec, then run `full`.

The engineer never calls real external services; it uses stubs.

## CI/CD pipelines

`/building-cicd-pipelines` writes or fixes GitHub Actions workflows.

```
/building-cicd-pipelines Java Lambda CI and CD to AWS via OIDC, Pro private repo, dev and prod, monorepo ./
```

It writes and fixes only. It does not push, open pull requests, trigger workflows or create secrets.
For an audit of existing workflows, use the reviewer agent `cicd-pipeline-reviewer` instead; it
does not write anything.

## Related

- Packages: [`acceptance-testing`](../../packages/quality/acceptance-testing/README.md),
  [`quarkus-acceptance-testing`](../../packages/quality/quarkus-acceptance-testing/README.md),
  [`github-actions-cicd`](../../packages/delivery/github/github-actions-cicd/README.md).
- Spec source: [specs-and-github](specs-and-github.md).
