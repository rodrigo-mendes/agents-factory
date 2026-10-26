---
name: coordinating-oci-handoffs
description: >-
  Shared handoff protocol for the OCI agent family (oci-functions-java, oci-deployer, oci-debugger,
  oci-terraform, oci-serverless-architect/stack, oci-observability): how agents record work-orders
  and report files under docs/handoff/<capability>/ and hand work off to each other. Use when an
  OCI agent needs to read prior handoff context, write a report, or route work to a sibling agent.
---

# Coordinating OCI Handoffs

The OCI agents cooperate through a file-based **handoff protocol**: each agent reads any existing
records in the target project's `docs/handoff/<capability>/`, does its work, writes a report from a
shared template, and names the single next action (which sibling agent/skill picks it up).

## Quick Navigation

- **[Handoff protocol](./blueprints/handoff-protocol.md)** — the full spec (invocation vocabulary,
  per-tool mechanism, the standard handshake every agent follows).
- **Templates** (in [`./assets/`](./assets/)): `work-order.template.md`, `report.template.md`,
  `deploy-report.template.md`, `diagnosis-report.template.md`.

## How agents use it

| Agent | Reads | Writes |
|---|---|---|
| `oci-functions-java` | work-order / diagnosis-report | `report-java.md` |
| `oci-deployer` | diagnosis-report | `deploy-report.md` |
| `oci-debugger` | deploy-report | `diagnosis-report.md` |
| `oci-terraform` | work-order / report | `report-terraform-infra.md` |

Reports are written into the **target project** (`docs/handoff/<capability>/`), never into this
package. This skill is the single source of truth for the protocol and its templates.
