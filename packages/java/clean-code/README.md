# clean-code

Java clean code for serverless functions, split out of `quarkus-core` and `oci-functions-java`
(2026-10-31) so it can be installed and sold on its own. Skill and rule names did not change.

Two packages, one per stack, because each rule applies to every `src/main/java/**/*.java` it can see:
installing both in the same project would apply the OCI rule to Quarkus code and the other way round.

| Package | Skill | Rule | Depended on by |
|---|---|---|---|
| `clean-code-quarkus` | `refactoring-quarkus-java` | `quarkus-clean-code` | `quarkus-core` |
| `clean-code-oci` | `refactoring-oci-java` | `java-functions-clean-code` | `oci-functions-java` |

```
factory-core
   ├── clean-code-quarkus ── quarkus-core
   └── clean-code-oci     ── oci-functions-java
```

Bundle `packages/bundles/java-clean-code` installs both; its README tells the buyer to keep only the
rule of their stack.
