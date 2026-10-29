# CDI Lite Limitations: Quarkus ArC 3.40.x

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). Source for every line unless stated: https://quarkus.io/version/3.40/guides/cdi-reference

## What ArC implements

- Jakarta CDI 4.1, **CDI Lite**, with some improvements; ArC passes the CDI Lite TCK and does **not** implement CDI Full.
- Most work happens at build time. Bean discovery uses a single bean archive in annotated mode, built from a Jandex index.

## What is not available

| Feature | Status in 3.40 | Use instead |
|---|---|---|
| CDI portable extensions | not supported | Quarkus extension build items |
| `@ConversationScoped` | not available | no alternative recorded |
| `InterceptionFactory` | replaced by `InterceptionProxy` | `InterceptionProxy` |
| Decorating built-in beans such as `Event` | unsupported | no alternative recorded |

Build items that replace extension hooks: `AdditionalBeanBuildItem`, `UnremovableBeanBuildItem`, `SyntheticBeanBuildItem`, `BeanDefiningAnnotationBuildItem`, `AnnotationsTransformerBuildItem` (https://quarkus.io/version/3.40/guides/cdi-integration).

CDI Full features beyond a subset are only partly supported. Decorators, a subset of `BeanManager` and `@SessionScoped` (with Undertow) are the supported remainder (medium confidence, M9); confirm details on the page before relying on them.

## Name of the build-item factory (medium confidence)

The research read that `AdditionalBeanBuildItem` has a `setUnremovable()` method but did not read the page for a static factory such as `unremovableOf`. This skill does not use that name (register M3).
