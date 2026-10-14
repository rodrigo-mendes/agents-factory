---
name: camel-quarkus-integrator-project-config
description: "Camel Quarkus 3.40 project configuration: BOMs, dependencies, test artifact, native, application properties. Use when editing pom.xml, application.properties or application.yml."
paths:
  - "**/{pom.xml,src/main/resources/application.properties,src/main/resources/application.yml}"
---

# Camel Quarkus project configuration (3.40)

Targets Camel Quarkus 3.40.x LTS (Camel 4.22, Quarkus 3.40). Exact versions, property names and
values are in the skills (`.claude/skills/`); refer there instead of restating them. Tags
`(unverified)` / `(medium confidence)` in a skill apply here too.

Version lock: only the 3.40 skills apply. Quarkus 4 artifacts are not covered; no Camel Quarkus
build on Quarkus 4 is known (medium confidence, absence of evidence).

Path-scoped rules load only when a matching file is read: this rule helps on existing projects
(`pom.xml` matches in any Maven project). The new-project flow lives in the package README and the
`camel-quarkus-integrator` agent.

## Always

- Import `quarkus-bom` and `quarkus-camel-bom` with the same `quarkus.platform.version`
  (`developing-camel-quarkus-core-v3-40`).
- Add one extension per capability from the skill that covers it (`-rest-`, `-platform-http-`,
  `-http-`, `-file-`, `-jaxb-`, `-xslt-`, `-bean-`, `-log-`; all `developing-camel-quarkus-*-v3-40`).
- Test dependency: `camel-quarkus-junit` at `test` scope
  (`developing-camel-quarkus-junit-v3-40`); Mockito support only if needed
  (`developing-quarkus-junit-v3-40`).
- Keep project layout, package and file locations per `structuring-camel-quarkus-projects`.
- Native mode: list reflection classes and resources explicitly; builder requirements are in
  `developing-camel-quarkus-core-v3-40` (native mode blueprint).
- Verify with `./mvnw` (or `mvn` when the project has no wrapper): `clean compile` and `test`;
  native with `verify -Dnative` (representative, unverified) only when requested (needs a
  Mandrel/GraalVM builder).

## Ask first

- BOM choice: platform BOM vs the standalone `camel-quarkus-bom`, which fits only if a newer Camel
  Quarkus than the platform is needed (`developing-camel-quarkus-core-v3-40`).
- Settings the core skill flags as Ask First (`serialization-enabled`, runtime catalog).
- TLS scope: prefer a named TLS configuration (`developing-camel-quarkus-http-v3-40`) over a global
  `quarkus.tls.*` change; the core skill flags the TLS scope as Ask First.
- Mixing Quarkus 4 artifacts (version lock above) or 3.15-era versions.
- New dependencies beyond the requirement.

## Never

- Use `camel-quarkus-resilience4j` or `camel-quarkus-junit5`: not available in 3.40.x; the skills
  name the replacements.
- Set `serialization-enabled=false` together with the extensions the core skill lists: they need it.
- Put secrets in committed `application.properties` (team convention): use environment variables
  or a secret store.
- Configure messaging, database, Quarkus security or e-mail from memory: no skill covers them, so
  any config would be unguided.
