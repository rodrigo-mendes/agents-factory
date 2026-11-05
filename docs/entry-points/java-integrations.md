# Java integration commands

These commands help you build integrations in Java: Stripe payments and Camel Quarkus routes.

## Stripe Java

| Job | Command | Routes to | Argument hint |
|---|---|---|---|
| Implement a Stripe flow | [`/integrate-stripe-java`](../../packages/java/libs/stripe-java/README.md#integrate-stripe-java) | `stripe-integrator` | `<requirement> <project-path>` |
| Review an existing Stripe integration | [`/review-stripe-integration`](../../packages/java/libs/stripe-java/README.md#review-stripe-integration) | `stripe-advisor` | `<scope or question> <project-path>` |

```
/integrate-stripe-java implement PaymentIntent create with idempotency key ./payments-service
/review-stripe-integration review webhook handler for signature verification order ./payments-service
```

The review checks signature verification before side effects, idempotency on every POST, the
Stripe-Version header, and the patterns that changed in version 33.x. Use it before you merge.

## Camel Quarkus

`/integrating-camel-quarkus` is an **inline orchestrator**. It interviews you about the integration,
then loads only the Camel Quarkus skills it needs. It targets Camel Quarkus 3.40 LTS (Camel 4.22).

```
/integrating-camel-quarkus
```

It does not cover Quarkus 4, other Camel versions, Kafka or JMS, JDBC, or Quarkus security.

## Libraries without a command

LangChain4j and Quarkus LangChain4j have no command. Their agents are started by other agents or by
an orchestrator. Ask in plain language, and Claude loads the matching skill.

## Related

- Packages: [`stripe-java`](../../packages/java/libs/stripe-java/README.md),
  [`camel-quarkus-integrator`](../../packages/java/quarkus/camel-quarkus-integrator/README.md),
  [`camel-quarkus-skills`](../../packages/java/quarkus/camel-quarkus-skills/README.md),
  [`langchain4j`](../../packages/java/libs/langchain4j/README.md),
  [`quarkus-langchain4j`](../../packages/java/quarkus/quarkus-langchain4j/README.md).
