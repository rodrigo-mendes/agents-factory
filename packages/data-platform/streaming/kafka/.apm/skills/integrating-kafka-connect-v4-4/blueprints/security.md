# Security, Kafka Connect 4.4.0

Back to [SKILL.md](../SKILL.md). Sources: [security model](https://kafka.apache.org/44/security/security-model-connect/), [user guide](https://kafka.apache.org/44/kafka-connect/user-guide/), [configs](https://kafka.apache.org/44/configuration/kafka-connect-configs/), [configuration providers](https://kafka.apache.org/44/configuration/configuration-providers/). All read 2026-11-04. Representative code; adapt to your environment.

## Threat model in one paragraph

The REST API is unsecured by default and lets anyone who reaches it start and stop connectors. Plugins run arbitrary code in the worker JVM, and installing a plugin is equivalent to granting arbitrary code execution. Class-loading client overrides are by design a code-execution vector. So REST access equals cluster-administrator trust. Guardrails that carry two sources are in SKILL.md; the items below add the single-page and unresolved ones.

## Hardening checklist

| Item | Evidence |
|---|---|
| REST on a trusted network, HTTPS | Always Do, Never Do (two pages) |
| Authentication in front of REST (proxy or extension) | Ask First, security model only (medium confidence, M9) |
| `connector.client.config.override.policy=Allowlist` | Always Do (four pages) |
| ConfigProvider placeholders for secrets | Always Do (two pages) |
| Worker to broker over `SASL_SSL` or `SSL`, like any client | security model only (medium confidence) |
| Separate or disable admin endpoints | one page (medium confidence), see below |
| ACLs on the config, offset and status topics | one page (medium confidence), see below |
| Only trusted plugins | security model only (medium confidence) |
| `access.control.allow.origin` empty unless needed (`*` allows any domain) | configs only (medium confidence) |

## Admin endpoints

`admin.listeners` separates the `/admin` endpoints, and an empty value disables them. If unset, `/admin` endpoints are on the regular listeners (medium confidence; the disable-with-empty rule is on the security model page only).

```properties
# disable the admin endpoints
admin.listeners=
```

## ACLs

- Protect the config, offset and status topics with ACLs as with any sensitive topic (medium confidence, security model only).
- Partition the shared worker principal's ACLs by topic prefix per connector (medium confidence, security model only).
- Use separate Connect clusters for teams that do not trust each other (medium confidence, security model only).
- The worker principal needs these ACLs ([user guide](https://kafka.apache.org/44/kafka-connect/user-guide/)): Read on Group `group.id`; Read, Write and Create on the three internal topics (Create only if they do not exist); for sources, Write on target topics (and Create if `topic.creation.enable=true`); for sinks, Read on Group `connect-${connector}` and on sink topics, plus Write on the DLQ topic if set. IdempotentWrite is needed only against pre-2.8 brokers. Exactly-once ACLs are in [ask-first-decisions](./ask-first-decisions.md).

## Secrets

Placeholders resolve at runtime from a provider, so the stored config holds the template, not the value. Anyone who can call REST and knows a valid template can usually read the resolved value.

File provider paths: when `allowed.paths` is unset, a file provider allows every path. Setting it limits reads (medium confidence, configuration providers page only).

```properties
config.providers.file.param.allowed.paths=/mnt/secrets   # (medium confidence, M11)
```

The providers page also mentions `allowlist.pattern` for providers (medium confidence). Whether the system property `org.apache.kafka.automatic.config.providers`, applied in 4.4.0 to dynamic broker config validation, also limits Connect workers is (unverified).

## REST authentication

Options and the production caveat for `PropertyFileLoginModule` are in [ask-first-decisions](./ask-first-decisions.md). Authentication identifies the caller; there is no per-connector authorization (medium confidence).

## Verify

```bash
# From a host that must NOT reach REST
curl -m 5 http://connect-host:8083/
# Expected: connection refused or timeout
```
