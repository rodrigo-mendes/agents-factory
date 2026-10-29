# Unused-Bean Removal: Quarkus ArC 3.40.x

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md).

## Contents

- [Default and roots](#default-and-roots)
- [Removal modes](#removal-modes)
- [Identifier-only beans](#identifier-only-beans)
- [Inspecting removals](#inspecting-removals)

## Default and roots

ArC resolves injection points at build time and removes unused beans. The default is `quarkus.arc.remove-unused-beans=all`. These beans count as unremovable:

- beans annotated `@io.quarkus.arc.Unremovable`;
- types listed in `quarkus.arc.unremovable-types`;
- beans covered by an `UnremovableBeanBuildItem`;
- beans named with `@Named`;
- beans that declare an observer method.

ArC cannot detect lookups through `CDI.current()`, so a bean used only that way may be removed by mistake.

```java
@ApplicationScoped
@Unremovable
public class OrderMapper { }
```

The value format of `quarkus.arc.unremovable-types` was not recorded; read its property description in the CDI reference before use.

Sources: https://quarkus.io/version/3.40/guides/cdi-reference ; https://quarkus.io/version/3.40/guides/cdi-integration

## Removal modes

Values: `all` (default), `none`/`false`, `fwk`/`framework` (keeps every application bean, still optimizes framework beans).

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| `all` | boot time, memory | name and programmatic lookups need `@Unremovable` | default |
| `fwk` | safety for application beans looked up dynamically | slightly larger application | heavy name lookup of `@Identifier` beans from Camel |
| `none` | closest to the spec | gives up dead-bean elimination | debugging only |

Source: https://quarkus.io/version/3.40/guides/cdi-reference

## Identifier-only beans

The removal rules in the CDI reference name `@Named`, not `@Identifier`, as a reason a bean is unremovable.

- (unverified, U1) Whether ArC removes an `@Identifier`-only bean that nothing injects. No official page states it; not resolvable from documentation.
- (unverified, U2) Whether Camel Quarkus 3.40 produces an `UnremovableBeanBuildItem` for beans referenced by name in routes. The camel-quarkus-bean extension page does not cover it.

Do not assert either outcome. Workaround: add `@Unremovable` (or use `quarkus.arc.unremovable-types`, or `remove-unused-beans=fwk`).

```java
@ApplicationScoped @Identifier("orderMapper") @Unremovable
class OrderMapper { }
```

Impact if the bean is removed: a Camel lookup by name fails at runtime. Follow-ups: the ArC processor source on the 3.40 branch, the camel-quarkus core/bean deployment processors, or a test that reads `/q/arc/removed-beans`.

Sources: https://quarkus.io/version/3.40/guides/cdi-reference ; https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/bean.html

## Inspecting removals

Representative, adapt to your environment (dev mode only; the endpoint list is unverified, U9):

```bash
./mvnw quarkus:dev -Dquarkus.log.category."io.quarkus.arc.processor".level=DEBUG
curl -s localhost:8080/q/arc/removed-beans
# Expected: beans looked up only by name are NOT listed
```

Documentation note (medium confidence, M7): the cdi-reference removal list and the config-property description of "unused" differ slightly (the property text says "does not have a name" and omits `@All`). Treat the cdi-reference list as authoritative.
