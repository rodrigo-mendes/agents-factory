# Always-do patterns

The rules in the skill's ✅ list, each with a right and a wrong example. Back to [SKILL.md](../SKILL.md).

## Contents

- [Check before writing](#check-before-writing)
- [Give each writer its own files](#give-each-writer-its-own-files)
- [Run the generator last, once](#run-the-generator-last-once)
- [Keep command headings exact](#keep-command-headings-exact)
- [Report source defects, do not fix them](#report-source-defects-do-not-fix-them)
- [Show the commit split and stop](#show-the-commit-split-and-stop)

## Check before writing

Run D1 and show the gaps first, so the user approves real work.

```text
✅  /documenting-agent-packages mode=check
    -> 2 of 44 manuals have gaps: terraform (platform missing), oci-terraform (connector-hub missing)
❌  /documenting-agent-packages mode=all      (starts 44 rewrites without looking)
```

## Give each writer its own files

```text
✅  Writer 1 may write: packages/java/libs/stripe-java/README.md, packages/java/libs/langchain4j/README.md
    Writer 2 may write: packages/cloud/terraform/terraform/README.md
❌  Writer 1: "document the Java packages"        (no file list; two writers may touch the same README)
```

## Run the generator last, once

```text
✅  start writers -> wait for all to return -> python docs_catalog.py --root . -> run the checks
❌  python docs_catalog.py --root .   while two writers are still writing
```

## Keep command headings exact

```text
✅  ### `/provision-aws-terraform`            anchor: #provision-aws-terraform
❌  ### `/provision-aws-terraform` - Terraform for AWS      anchor: #provision-aws-terraform---terraform-for-aws
```

## Report source defects, do not fix them

```text
✅  known-issues: "debug-oci-function SKILL.md says code fixes go to /deploy-oci-function; the agent says
                   /develop-java-function. The manual follows the agent. (reported)"
❌  edit the SKILL.md so the manual and the skill agree
```

## Show the commit split and stop

```text
✅  Proposed commits: 1 scripts, 2 docs pages, 3 package manuals, 4 bundle READMEs. Nothing committed.
❌  git commit -am "docs"
```
