# Never-Do Patterns: Quarkus ArC 3.40.x

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). Each anti-pattern and its alternative rest on versioned 3.40 pages and are tagged High in the research. Two research "forbidden" items are not here: the `@Identifier`-only bean (open question, see [bean removal](./bean-removal.md)) and `@Named` as a general qualifier (a recommendation, see SKILL.md Ask First).

## Contents

1. [Direct field access on a normal-scoped bean](#1-direct-field-access-on-a-normal-scoped-bean)
2. [CDI portable extensions or CDI Full features](#2-cdi-portable-extensions-or-cdi-full-features)
3. [InjectMock on Singleton or Dependent beans](#3-injectmock-on-singleton-or-dependent-beans)
4. [Build-profile annotations expecting runtime config](#4-build-profile-annotations-expecting-runtime-config)

## 1. Direct field access on a normal-scoped bean

The client proxy delegates only method calls, so reading a field of an `@ApplicationScoped` bean through the proxy does not reach the contextual instance.

```java
// 🚫 WRONG
int n = counterBean.count;      // counterBean is @ApplicationScoped

// ✅ CORRECT
int n = counterBean.getCount();
```

Source: https://quarkus.io/version/3.40/guides/cdi

## 2. CDI portable extensions or CDI Full features

For application code: `InterceptionFactory` is replaced by `InterceptionProxy`, and `@ConversationScoped` is not available. Portable extensions are not supported; only authors of Quarkus extensions have an alternative, the build items (`AdditionalBeanBuildItem`, `UnremovableBeanBuildItem`, `SyntheticBeanBuildItem`, `BeanDefiningAnnotationBuildItem`, `AnnotationsTransformerBuildItem`). More in [CDI Lite limitations](./cdi-lite-limitations.md).

```java
// 🚫 WRONG (application code)
@Inject InterceptionFactory<Foo> factory;

// ✅ CORRECT
// use InterceptionProxy in its place (see the CDI reference)
```

For extension authors (not application code): a portable `Extension` class is not supported; a Quarkus extension build step contributes beans through a build item such as `AdditionalBeanBuildItem` (see the CDI integration guide).

Sources: https://quarkus.io/version/3.40/guides/cdi-reference ; https://quarkus.io/version/3.40/guides/cdi-integration

## 3. InjectMock on Singleton or Dependent beans

Only normal-scoped beans can be mocked ("basically every scope except @Singleton and @Dependent").

```java
// 🚫 WRONG
@Singleton class Clock { }          // test: @InjectMock Clock clock;

// ✅ CORRECT
@ApplicationScoped class Clock { }  // test: @InjectMock Clock clock;

// ✅ CORRECT (bean stays @Singleton)
// test: @InjectMock @MockitoConfig(convertScopes = true) Clock clock;
```

Without `@MockitoConfig(convertScopes = true)`, do not mock a `@Singleton` or `@Dependent` bean; see [testing](./testing.md).

Source: https://quarkus.io/version/3.40/guides/getting-started-testing

## 4. Build-profile annotations expecting runtime config

`@IfBuildProfile`, `@UnlessBuildProfile`, `@IfBuildProperty` and `@UnlessBuildProperty` are evaluated at build time, so runtime profiles and runtime properties have no effect on them.

```text
# 🚫 WRONG: expecting a dev-only @IfBuildProfile("dev") bean to disappear without a rebuild
java -Dquarkus.profile=prod -jar app.jar

# ✅ CORRECT: rebuild for the profile, or switch at runtime with @LookupIfProperty and Instance<>
```

Source: https://quarkus.io/version/3.40/guides/cdi-reference
