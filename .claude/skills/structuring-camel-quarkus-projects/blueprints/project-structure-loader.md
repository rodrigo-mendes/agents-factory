# Project Structure Loader Notes

How an agent or instruction should consume the layout conventions of
`structuring-camel-quarkus-projects` before creating any file.

## Purpose

- Keep one source of truth for placement and naming, instead of repeating it in every instruction or prompt.
- Let project-specific values (package, coordinates) override the placeholder defaults.

## Sources and precedence

```
1st  the project itself    existing source tree and pom.xml (real base_package, groupId, artifactId)
2nd  ../assets/project-structure.yml   layout config shipped with the skill
3rd  placeholder defaults  com.company.project (never use for real code without confirmation)
```

- [SKILL.md](../SKILL.md) — directory tree summary, package/location/name table, Always Do / Ask First / Never Do.
- [project-structure.yml](../assets/project-structure.yml) — machine-readable packages, file patterns, locations and naming patterns. Its `project:` values are placeholders.

## Loading procedure

Before creating any file:

1. Read [SKILL.md](../SKILL.md) and [project-structure.yml](../assets/project-structure.yml).
2. Read the real `base_package`, `groupId` and `artifactId` from the project (source tree, `pom.xml`). If none can be found, ask; do not invent them.
3. Substitute them for the placeholders.
4. Compute the target package and directory from the config.

Worked example, with the real package `org.acme.billing`:

```
base_package    = org.acme.billing
route_package   = base_package + ".integration.routes"   -> org.acme.billing.integration.routes
route_directory = src/main/java/org/acme/billing/integration/routes
route_file      = [Functionality]Route.java
```

## Scope

This layout does not define framework behaviour (annotations, CDI scopes, test APIs, extensions, versions). Take those from the version-specific skills, for example `developing-camel-quarkus-core-v3-40`.
