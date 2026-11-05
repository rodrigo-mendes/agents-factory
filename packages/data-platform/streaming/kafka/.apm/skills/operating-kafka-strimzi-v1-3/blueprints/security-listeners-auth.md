# Security, listeners, authentication, Strimzi 1.3.x

Back to [SKILL.md](../SKILL.md). High claims carry two or more official pages; single-source items are tagged (medium confidence); assembled YAML is tagged (unverified). Doc base for AsciiDoc pages: `https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/`.

## Listener authentication

Sources: [listener authentication](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/security/con-securing-kafka-authentication.adoc), [client authentication](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/security/con-securing-client-authentication.adoc), [KafkaUser procedure](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/operators/proc-configuring-kafka-user.adoc).

- With no `authentication` property the listener accepts all connections.
- "Authentication must be configured when using the User Operator to manage `KafkaUsers`".
- The `KafkaUser` authentication type must match the listener. The KafkaUser procedure needs a listener with mTLS and TLS encryption.
- Port 9404 is reserved for Prometheus metrics.
- The listener authentication page looked cut in the SCRAM section, so SCRAM details are cross-checked with the client authentication page (register L5).

```yaml
# Shape of documented fields, assembled (unverified, U3)
listeners:
  - name: scram
    port: 9092
    type: internal
    tls: true
    authentication:
      type: scram-sha-512
  - name: tls
    port: 9093
    type: internal
    tls: true
    authentication:
      type: tls
```

## KafkaUser: authentication and ACLs

Sources: [client authentication](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/security/con-securing-client-authentication.adoc), [client ACLs](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/security/con-securing-client-acls.adoc), [authorization](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/security/con-securing-kafka-authorization.adoc), [KafkaUser procedure](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/operators/proc-configuring-kafka-user.adoc).

- Without `spec.kafka.authorization` "no authorization is enabled and clients have no restrictions".
- With `simple`, access is denied unless the `KafkaUser` lists explicit ACL rules. A user stays not ready until the Kafka resource enables `simple`.
- `tls-external` users get no secret; ACLs and quotas work with `CN=<username>`.

```yaml
# KafkaUser with mTLS and simple ACLs, assembled from documented fields (unverified, U3)
apiVersion: kafka.strimzi.io/v1
kind: KafkaUser
metadata:
  name: my-user
  labels:
    strimzi.io/cluster: my-cluster
spec:
  authentication:
    type: tls
  authorization:
    type: simple
    acls:
      - resource: { type: topic, name: my-topic, patternType: literal }
        operations: [Describe, Read]
      - resource: { type: group, name: my-group, patternType: literal }
        operations: [Read]
```

ACL `host` defaults to `*` and ACL `type` to `allow` ([API reference](https://strimzi.io/docs/operators/1.3.0/configuring.html), medium confidence: one page). User secrets and renewal details: [connect-topics-users](./connect-topics-users.md#user-secrets-medium-confidence).

## OAuth 2.0 with custom

Sources: [OAuth migration](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/oauth/con-oauth-migration.adoc), [OAuth server config](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/oauth/con-oauth-server-config.adoc).

- The `oauth` and `keycloak` types are deprecated for removal. Use `type: custom` with `sasl: true`, `sasl.enabled.mechanisms: OAUTHBEARER` and an OAuth principal builder.
- Secrets must come from a Kubernetes `Secret` through a configuration provider, not clear text.

```yaml
# Skeleton, assembled (unverified, U5): the placeholder syntax and the JAAS string are not confirmed
listeners:
  - name: oauth
    port: 9094
    type: internal
    tls: true
    authentication:
      type: custom
      sasl: true
      listenerConfig:
        oauthbearer.sasl.jaas.config: "... oauth.client.secret=\"${secrets:<ns>/<secret>:<key>}\" ..."
```

## Certificate authorities and renewal

Sources: [certificate renewal](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/security/con-certificate-renewal.adoc), [API reference](https://strimzi.io/docs/operators/1.3.0/configuring.html), [1.3.0 notes](https://github.com/strimzi/strimzi-kafka-operator/releases/tag/1.3.0).

- Default CA validity is 365 days, renewal 30 days before expiry. `maintenanceTimeWindows` can schedule renewals (medium confidence, M9).
- Clients must refresh truststores from `<cluster>-cluster-ca-cert` after CA renewal.
- Internal cluster security and cert-manager integration are Early Access and not recommended for production.

## Network policies and exposure

- Strimzi creates a NetworkPolicy per listener that allows all namespaces; restrict with `networkPolicyPeers` (medium confidence, M10; [network policies](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/security/proc-restricting-access-to-listeners-using-network-policies.adoc)).
- Listener types and the `ingress` deprecation: [ask-first-decisions](./ask-first-decisions.md#c5-external-exposure).

## Hardening checklist

1. Authenticate every listener (always-do item 13).
2. `authorization.type: simple` with least-privilege ACLs and a minimal `superUsers` list (always-do item 14).
3. OAuth through `custom` with secrets from config providers (item 15).
4. Plan CA validity, renewal and maintenance windows.
5. Keep Early Access features out of production.
