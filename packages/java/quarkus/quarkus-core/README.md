# quarkus-core

Base Quarkus **3.40 LTS** knowledge skills, shared by the Quarkus packages of this factory.

| Skill | Covers |
|---|---|
| `developing-quarkus-arc-v3-40` | ArC (Quarkus CDI): scopes, qualifiers, unused-bean removal, Jandex, mocking |
| `developing-quarkus-rest-v3-40` | `quarkus-rest`, `quarkus-rest-jackson`, `quarkus-rest-client` |
| `developing-quarkus-junit-v3-40` | `quarkus-junit`: `@QuarkusTest`, profiles, test resources, `@InjectMock` |

Layering:

`refactoring-quarkus-java` and the `quarkus-clean-code` rule live in the `java/clean-code/clean-code-quarkus` package
(a dependency of this one), so they still install with it.

```
factory-core
   └── quarkus-core
         ├── camel-quarkus-skills  (Quarkus + Camel) ── camel-quarkus-integrator
         └── quarkus-aws           (Quarkus + AWS)    ── quarkus-aws-saas
```

The three skills were moved here unchanged from `camel-quarkus-skills` (2026-10-28); their names, and
therefore their installed paths under `.claude/skills/`, did not change. Provenance (research files)
stays in `workspace/research_Quarkus_{ArC,REST,JUnit}_v3.40.md`.
