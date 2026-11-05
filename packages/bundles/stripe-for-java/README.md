# stripe-for-java

Stripe for Java: stripe-java 34.x payments, subscriptions and webhooks, with the stripe-advisor and stripe-integrator agents.

**Who it is for:** Java teams that add Stripe payments, subscriptions and webhooks with stripe-java 34.x.

## Contents

<!-- BEGIN GENERATED:contents -->
**Packages included:** [`stripe-java`](../../java/libs/stripe-java/README.md)
**Also installed as dependencies:** [`factory-core`](../../factory/factory-core/README.md)

| Type | Entry point or agent | Package |
|---|---|---|
| command | [`/integrate-stripe-java`](../../java/libs/stripe-java/README.md#integrate-stripe-java) | `stripe-java` |
| command | [`/review-stripe-integration`](../../java/libs/stripe-java/README.md#review-stripe-integration) | `stripe-java` |
| agent | [`stripe-advisor`](../../java/libs/stripe-java/.apm/agents/stripe-advisor.agent.md) | `stripe-java` |
| agent | [`stripe-integrator`](../../java/libs/stripe-java/.apm/agents/stripe-integrator.agent.md) | `stripe-java` |

Plus 4 knowledge skills that Claude loads by description. Each package manual lists them.
<!-- END GENERATED:contents -->

## Installation

From the folder of the project that should receive the bundle:

```bash
apm install <path-to-agents-factory>/packages/bundles/stripe-for-java --target claude
```

Add `--dry-run` to preview. APM installs the packages listed above and their dependencies into `.claude/`.

To produce the folder and zip that are sold or shared, export the bundle from this repository:

```bash
python scripts/export-bundle.py stripe-for-java           # dry run
python scripts/export-bundle.py stripe-for-java --apply   # writes dist/stripe-for-java/ and the zip
```

The export holds the `.claude/` folder and a `docs/` folder with the usage manuals of the packages it
includes.

## Quick Start

```text
/integrate-stripe-java implement PaymentIntent create with idempotency key ./payments-service
/review-stripe-integration review webhook handler for signature verification order ./payments-service
```

## Documentation

The usage manuals cover installation, quick start, usage scenarios, a command or skill reference,
agents and limits:

- [`stripe-java`](../../java/libs/stripe-java/README.md): usage manual.

See also the [package catalog](../../../docs/packages/README.md) and the
[entry points](../../../docs/entry-points/README.md).
