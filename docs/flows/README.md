# Flows

A flow chains several entry points into one pipeline. Each page has a diagram that shows what starts
what, the commands in order, and where you decide.

| Flow | Use it when you want to |
|---|---|
| [Research to a validated skill](knowledge-base.md) | Turn a technology or method into a checked skill or rule. |
| [The quality loop](quality-loop.md) | Check an artifact before you commit it. |
| [A complete agent package](full-agent-package.md) | Go from a brief to a committed package, with a quality loop and a commit plan. |
| [A SaaS change, end to end](saas-spec-driven.md) | Build or change a SaaS on Quarkus, AWS Lambda and Next.js. |
| [An OCI serverless capability](oci-serverless-delivery.md) | Build a function, its infrastructure and its API route on OCI. |
| [Specs from a proof of concept](spec-from-poc.md) | Draft a spec from existing prototype code. |

## How to read the diagrams

Arrows between you and a command mean you type it. Arrows into a subagent show what starts it:
`/command (fork)` for a command, `Agent tool` for an orchestrator, and records on disk for handoffs.
The mechanisms are explained in [Agent architecture](../agents/architecture.md).

## Related

- [Entry points](../entry-points/README.md).
- [Overview](../overview.md).
