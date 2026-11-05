# ZooKeeper and broker security, Kafka 3.9.2

Back to [SKILL.md](../SKILL.md). Sources: [ZooKeeper authentication](https://kafka.apache.org/39/security/zookeeper-authentication/), [ZooKeeper encryption](https://kafka.apache.org/39/security/zookeeper-encryption/), [SASL](https://kafka.apache.org/39/security/authentication-using-sasl/), [ACLs](https://kafka.apache.org/39/security/authorization-and-acls/), [SSL](https://kafka.apache.org/39/security/encryption-and-authentication-using-ssl/), [listeners](https://kafka.apache.org/39/security/listener-configuration/), [running cluster](https://kafka.apache.org/39/security/incorporating-security-features-in-a-running-cluster/), [Admin Guide](https://zookeeper.apache.org/doc/r3.8.4/zookeeperAdmin.html). All read in full 2026-11-04. Most items rest on one page each (medium confidence, M13).

## Order for securing an existing ZooKeeper (5 steps)

Changing `zookeeper.set.acl` or removing ports out of order can leave znodes with inconsistent ACLs (paraphrased, single page, medium confidence, M13).

1. Enable SASL or mTLS on ZooKeeper, keeping the non-TLS port.
2. Rolling-restart the brokers with the JAAS or mTLS settings.
3. If mTLS, disable the non-TLS port.
4. Rolling-restart with `zookeeper.set.acl=true`.
5. Run `bin/zookeeper-security-migration.sh --zookeeper.acl=secure --zookeeper.connect=localhost:2181`.

Disabling security is the reverse, also 5 steps. `zookeeper.set.acl` defaults to `false` ([broker configs](https://kafka.apache.org/39/configuration/broker-configs/)). Use of the flag with mTLS only: the authentication page sets it in its mTLS sample, the encryption page says to set it only with SASL (medium confidence, U22). Follow the authentication page for mTLS identities. A leftover `/migration` znode from this tool can stall a later migration (see [zk-to-kraft-migration](./zk-to-kraft-migration.md)).

## SASL to ZooKeeper

- Brokers use the JAAS `Client` section, passed with `-Djava.security.auth.login.config`. In Compose pass it through `KAFKA_OPTS`. Rename the section with `zookeeper.sasl.clientconfig`. Change the service name with `zookeeper.sasl.client.username` (default `zookeeper`).
- ZooKeeper JAAS can only be set through the static file (paraphrased). Brokers need the same principal name.
- SASL between ZooKeeper servers (`quorum.auth.*`) was not captured (unverified, U6).

## mTLS to ZooKeeper (ZooKeeper 3.5.7+, Kafka 2.5+)

- ZooKeeper server: `secureClientPort=2182`, `serverCnxnFactory=org.apache.zookeeper.server.NettyServerCnxnFactory`, `authProvider.x509=org.apache.zookeeper.server.auth.X509AuthenticationProvider`, plus `ssl.keyStore.*` and `ssl.trustStore.*`.
- Broker: `zookeeper.connect=zk1:2182,...`, `zookeeper.ssl.client.enable=true`, `zookeeper.clientCnxnSocket=org.apache.zookeeper.ClientCnxnSocketNetty`, plus `zookeeper.ssl.keystore.*` and `zookeeper.ssl.truststore.*`.
- Set the key password equal to the keystore password: ZooKeeper does not support a different one.
- With mTLS only, brokers and tools share a certificate DN (ACLs key on the DN), with distinct SANs.
- Encryption without client certificates: ZooKeeper `ssl.clientAuth=none` (default `need`). Brokers then need no keystore.
- CLI against TLS ZooKeeper: `--zk-tls-config-file` for `zookeeper-security-migration.sh`, `kafka-acls.sh`, `kafka-configs.sh`. `zookeeper-shell.sh` uses `-zk-tls-config-file`.
- Quorum TLS between ZooKeeper servers: `sslQuorum=true` with `NettyServerCnxnFactory` and `ssl.quorum.keyStore.*`, `ssl.quorum.trustStore.*`, one keystore per instance (Admin Guide). Zero-downtime upgrade: roll with `sslQuorum=false` and `portUnification=true`, then `sslQuorum=true`, then `portUnification=false`. Verify with the log line "Using TLS encrypted quorum communication".

## Authentication and authorization on brokers

- Client listeners: SASL_SSL with SCRAM-SHA-512, or SSL with `ssl.client.auth=required`. Never `requested`.
- SCRAM in ZooKeeper mode stores credentials in ZooKeeper, which is suitable for production only where ZooKeeper is secure and on a private network (medium confidence, M4). Create credentials with `kafka-configs.sh --zookeeper zk-1:2182 --zk-tls-config-file zk_tls_config.properties --alter --add-config 'SCRAM-SHA-512=[password=...]' --entity-type users --entity-name alice`. Inter-broker credentials must exist before brokers start. KRaft SCRAM bootstrap on 3.9 is not on the SASL page (unverified, U9).
- Authorizer: `kafka.security.authorizer.AclAuthorizer` in ZooKeeper mode (ACLs live in ZooKeeper), `org.apache.kafka.metadata.authorizer.StandardAuthorizer` in KRaft, plus `super.users`. `kafka-acls.sh --bootstrap-server` is the modern form. `--authorizer-properties zookeeper.connect=...` is marked deprecated and not supported in KRaft. Default of `allow.everyone.if.no.acl.found`: (unverified, U8).
- Mechanism changes on a live cluster are multi-bounce: add the mechanism, move clients, switch inter-broker, remove the old one.
- Delegation tokens: `delegation.token.secret.key` is identical on all brokers (and controllers in KRaft) and stored in plain text in `server.properties`, so protect the file.

## Hardening checklist

- [ ] Client TLS: keystores have a SAN and use PKCS12. In the image, mount them under `/etc/kafka/secrets` (default `CMD` only, medium confidence, U13).
- [ ] Broker to broker: `security.inter.broker.protocol=SSL` or an SSL-mapped `inter.broker.listener.name`.
- [ ] Broker to ZooKeeper: `zookeeper.ssl.client.enable=true` plus the Netty socket and truststore.
- [ ] Enabling TLS on a running cluster takes 3 bounces (open the secure port, switch inter-broker, close PLAINTEXT), waiting for the ISR between nodes.
- [ ] `ssl.enabled.protocols`: the config page default read `TLSv1.2`, the SSL page example lists `TLSv1.2,TLSv1.1,TLSv1`. Set `TLSv1.2,TLSv1.3` explicitly (medium confidence, U7).
- [ ] Certificate rotation: dynamic keystore update not described (unverified, U14).
- [ ] At rest: encrypt data directories at OS level. No native at-rest encryption in the pages read (medium confidence, M8).
- [ ] Network: publish client ports on `127.0.0.1` only. Do not publish ZooKeeper 2181, 2182, 2888, 3888 or the AdminServer 8080. Do not publish JMX.
