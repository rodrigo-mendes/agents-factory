# TLS and security, Kafka 4.4.0

Back to [SKILL.md](../SKILL.md). S-ids resolve in the [Source Bibliography](./unverified-and-risks.md#source-bibliography). The security landing page was read as navigation only (register L5).

## Authentication and authorization

- [ ] SASL over TLS on client listeners. Mechanisms: GSSAPI, PLAIN, SCRAM-SHA-256, SCRAM-SHA-512, OAUTHBEARER [S10]. Use TLS under SASL, in particular for PLAIN (medium confidence, M21).
  - Config: `listener.name.sasl_ssl.scram-sha-512.sasl.jaas.config=org.apache.kafka.common.security.scram.ScramLoginModule required ...;` [S10]
  - SCRAM in KRaft stores credentials in the metadata log. That suits production only where controllers are secured and on a private network [S10] (medium confidence, M23).
  - Bootstrap credentials at format time: `kafka-storage.sh format ... --add-scram 'SCRAM-SHA-256=[name="admin",password="..."]'`. Inter-broker credentials must exist before brokers start [S10].
  - Add client credentials at runtime: `kafka-configs.sh --alter --add-config 'SCRAM-SHA-256=[iterations=8192,password=...]' --entity-type users --entity-name alice`. Minimum and default iterations are 4096 [S10].
- [ ] OAUTHBEARER: the default unsecured JWT is non-production. In 4.4 a JWKS URL requires expected audience and issuer, or the broker fails to start [S10][S1].
- [ ] mTLS: `ssl.client.auth=required`; `requested` is discouraged [S11] (medium confidence, M22).
- [ ] ACLs with `StandardAuthorizer` on all nodes, `super.users` semicolon-separated, `allow.everyone.if.no.acl.found` false [S9] (medium confidence, M14).
  - `kafka-acls.sh --bootstrap-server ... --add --allow-principal User:Bob --producer --topic Test-topic`, and `--consumer --topic Test-topic --group Group-1` [S9].
  - Prefixed patterns: `--resource-pattern-type prefixed`. Be careful with `match` combined with `--remove` [S9].
  - `super.users` and `log.cleaner.*` defaults were not captured (unverified), U14.
- [ ] Policy plugins (`CreateTopicPolicy`, `AlterConfigPolicy`) are deployed on controllers [S20].
- [ ] Custom principal builders implement `KafkaPrincipalSerde` [S9][S20].
- [ ] Delegation tokens, if used: `delegation.token.secret.key` must be identical on all brokers and controllers. It is stored in plain text in `server.properties`, so protect the file [S10].

## TLS in transit

- [ ] Client to broker: `listener.security.protocol.map=CLIENT:SASL_SSL`. Defaults: `ssl.protocol=TLSv1.3`, `ssl.enabled.protocols=TLSv1.2,TLSv1.3` [S7][S31]. The SSL page example shows a legacy list (`TLSv1.2,TLSv1.1,TLSv1`); the config page default is used (medium confidence, U15).
- [ ] Broker to broker: map `inter.broker.listener.name` to SSL or SASL_SSL. The fallback `security.inter.broker.protocol` defaults to PLAINTEXT [S31][S11].
- [ ] Controller listener is secured and network-isolated from clients; `controller.listener.names` cannot equal the inter-broker listener [S31] (medium confidence, M20).
- [ ] Keep hostname verification on: `ssl.endpoint.identification.algorithm=https` is the default [S7]. Certificates carry a SAN [S11].
- [ ] PEM keystores are supported: `ssl.keystore.type=PEM`, `ssl.keystore.key`, `ssl.keystore.certificate.chain` [S11].
- [ ] Certificate rotation: hot keystore reload is not described on the 4.4 SSL page (unverified), U7. Plan a rolling restart unless verified.
- [ ] In Compose give each broker its own certificate. The official examples share one set and the README says that is not for production [S3] (medium confidence, M26: one release-branch file).

SSL secrets in the image go in `/etc/kafka/secrets` and are referenced through `KAFKA_SSL_KEYSTORE_FILENAME`, `KAFKA_SSL_KEYSTORE_CREDENTIALS`, `KAFKA_SSL_KEY_CREDENTIALS`, `KAFKA_SSL_TRUSTSTORE_FILENAME`, `KAFKA_SSL_TRUSTSTORE_CREDENTIALS` [S3].

```properties
# Representative — adapt to your environment (one certificate per broker, SAN set)
listener.security.protocol.map=CONTROLLER:SSL,CLIENT:SASL_SSL,BROKER:SSL
inter.broker.listener.name=BROKER
sasl.enabled.mechanisms=SCRAM-SHA-512
ssl.client.auth=required
authorizer.class.name=org.apache.kafka.metadata.authorizer.StandardAuthorizer
super.users=User:admin
```

## Encryption at rest

- [ ] No native at-rest encryption was found in the 4.4 pages read (unverified), U8. Use host or volume encryption for Docker volumes.
- [ ] Encrypt MM2 target clusters and exported data the same way.

## Network policy

- [ ] Publish only client listener ports, bound to `127.0.0.1` or the application network. The official examples publish 29092, 39092 and 49092 on all interfaces [S4] (medium confidence, M28: release-branch example, not a versioned page).
- [ ] Do not publish the controller port (9093) [S31] (medium confidence, M20). The official isolated example does not publish it either [S5].
- [ ] Publish the JMX port only with authentication and TLS [S14] (medium confidence, the monitoring page was partly read, register L2). The exact JMX flags are standard JDK flags (medium confidence), M2.
- [ ] File descriptors at least 100000; check `vm.max_map_count` [S16] (medium confidence, M19).

## Verification

```bash
# Representative — adapt to your environment
openssl s_client -connect kafka-1:9093 -servername kafka-1 </dev/null 2>/dev/null | openssl x509 -noout -subject -ext subjectAltName
# Expected: a SAN containing the broker hostname
kafka-acls.sh --bootstrap-server kafka-1:19092 --command-config admin.properties --list
```
