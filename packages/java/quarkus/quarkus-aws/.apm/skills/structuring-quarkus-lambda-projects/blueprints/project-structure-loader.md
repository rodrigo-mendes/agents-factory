# Project Structure Loader Notes

Back to [SKILL.md](../SKILL.md). How an agent consumes the layout conventions of `structuring-quarkus-lambda-projects` before creating any module, package or file. Shape modelled on the loader notes of `structuring-camel-quarkus-projects`.

## Purpose

- One source of truth for placement and naming, instead of repeating it in each instruction.
- Let project-specific values (package, coordinates, existing module names) override the placeholder defaults.

## Sources and precedence

```
1st  the project itself    root pom.xml (<modules>), existing source trees, real base_package, groupId
2nd  ../assets/project-structure.yml   layout config shipped with the skill
3rd  placeholder defaults  com.company.project (never use for real code without confirmation)
```

When the project already follows a different layout, ask whether to adopt this layout or keep the existing one; do not migrate files unprompted.

## Loading procedure

Before creating a module, package or file:

1. Read [SKILL.md](../SKILL.md) and [project-structure.yml](../assets/project-structure.yml).
2. Read the real `groupId`, base package and `<modules>` from the project. If none can be found, ask; do not invent them.
3. Substitute them for the placeholders.
4. If the task is "one Lambda or many", stop and run the [ask-first decision](./ask-first-decisions.md#1-one-function-per-module-or-one-http-lambda-with-many-routes) before creating any module.
5. Compute the target module, package and directory from the config.

Worked example with the real group `org.acme.saas`, function `orders`:

```
module path     = functions/orders
base package    = org.acme.saas.orders
handler class   = functions/orders/src/main/java/org/acme/saas/orders/OrdersLambda.java        (package root)
flow class      = functions/orders/src/main/java/org/acme/saas/orders/handler/CreateOrderFlow.java
test class      = functions/orders/src/test/java/org/acme/saas/orders/OrdersLambdaTest.java
artifact        = functions/orders/target/function.zip
```

## Scope

This layout does not define framework behaviour (handlers, CDI scopes, test APIs, SnapStart, native) or Terraform resources. Take those from the version-specific skills named in [SKILL.md](../SKILL.md#neighbours-names-and-links).
