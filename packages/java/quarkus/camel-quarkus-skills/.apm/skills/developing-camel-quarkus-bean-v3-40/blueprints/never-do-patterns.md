# Never-Do Patterns: Camel Quarkus Bean 3.40.x

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). Each anti-pattern and its alternative rest on versioned 3.40.x / 4.22.x pages or the 3.40.0 source tag. Medium-confidence pitfalls (no scope on a named bean, overloads, `Exchange` return type) are in [bean binding](./bean-binding.md#medium-confidence-pitfalls) and [CDI and native](./cdi-and-native.md#scope-and-discovery).

## 1. Name-referenced bean without reflection registration in native mode

The native guide says classes needing reflective access must be registered at compile time. The 3.40.0 `BeanProcessor` registers only classes with `@Handler` methods, not classes referenced by name from `bean:` URIs. Reflective access to such a class is therefore not registered automatically; in native mode that can fail where JVM mode works.

```java
// 🚫 WRONG
@ApplicationScoped @Named("calc") public class Calc { public int add(int a){ return a+1; } }

// ✅ CORRECT
@ApplicationScoped @Named("calc") @RegisterForReflection public class Calc { public int add(int a){ return a+1; } }
```

Sources: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/native-mode.html ; https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html ; https://raw.githubusercontent.com/apache/camel-quarkus/3.40.0/extensions/bean/deployment/src/main/java/org/apache/camel/quarkus/component/bean/deployment/BeanProcessor.java

## 2. bean: as a route input

The Bean component is producer-only.

```java
// 🚫 WRONG
from("bean:myBean").to("log:x");

// ✅ CORRECT: call the bean from another endpoint, or consume on a bean method
from("direct:start").to("bean:myBean");
// @Consume("direct:start") on a method of the bean creates the route
```

Sources: https://camel.apache.org/components/4.22.x/bean-component.html ; https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html

## 3. Mutable state in a Singleton bean

The default `scope=Singleton` bean is one shared instance.

```java
// 🚫 WRONG
@ApplicationScoped @Named("acc") @RegisterForReflection
public class Acc { private java.util.List<String> items = new java.util.ArrayList<>(); public void add(String s){ items.add(s); } }
// from("direct:r").to("bean:acc?method=add")

// ✅ CORRECT: no mutable field; per-call state lives on the Exchange
@ApplicationScoped @Named("acc") @RegisterForReflection
public class Acc { public void add(org.apache.camel.Exchange ex){ ex.setProperty("last", ex.getMessage().getBody(String.class)); } }
// from("direct:r").to("bean:acc?method=add")
```

Source: https://camel.apache.org/components/4.22.x/bean-component.html (the default `scope` is `Singleton`: calls share one instance). Using `scope=Request` instead is an Ask First option: whether it gives one instance per exchange for a CDI-managed named bean is not stated on the page (medium confidence, see SKILL.md Ask First).
