# Evaluation Scenarios: developing-camel-quarkus-file-v3-40

Four scenarios, one per type. The `skill-evaluator` agent runs these.

---

## Scenario 1: Canonical Path

**Type**: Standard successful invocation

```yaml
id: 1
name: canonical-file-consumer-with-readlock-and-move
query: "Write a Camel Quarkus 3.40 route that picks up XML files from /data/in, which another system writes, archives them on success and quarantines them on failure."
must_pass:
  - "Adds camel-quarkus-file without a version"
  - "Sets readLock explicitly (for example changed with readLockMinAge) and notes the default is none"
  - "Uses move and moveFailed (or states the default .camel behaviour)"
  - "Uses a plain RouteBuilder without @ApplicationScoped, since nothing is injected"
must_not:
  - "Consume with from(\"file:/data/in\") and no read lock"
  - "Put ${} placeholders in the directory path"
  - "States @ApplicationScoped is mandatory on a RouteBuilder"
```

---

## Scenario 2: Edge Case

**Type**: Ambiguous or unverified territory the skill must handle gracefully

```yaml
id: 2
name: edge-unverified-defaults
query: "What is the default heartbeat-timeout-multiplier of camel-quarkus-file-cluster-service, and what is the SFTP readLockTimeout default?"
must_pass:
  - "States the heartbeat-timeout-multiplier default is unverified and advises setting it explicitly"
  - "States the SFTP readLockTimeout default is conflicting (10000 vs 20000) and advises setting it explicitly"
  - "Tags the other file-cluster-service defaults as medium confidence"
must_not:
  - "Invent a numeric default for either option"
  - "Assert a Camel Quarkus-specific end-of-support date"
```

---

## Scenario 3: Misuse Rejection

**Type**: Request outside this skill's scope

```yaml
id: 3
name: misuse-scp-or-wrong-version
query: "Use camel-quarkus-jsch to set up an SFTP consumer, and make it work on Quarkus 4.0 Beta."
must_pass:
  - "States camel-quarkus-jsch is SCP, not SFTP, and recommends camel-quarkus-ftp or camel-quarkus-mina-sftp"
  - "Declines to apply 3.40.x guidance to Quarkus 4 and notes no Camel Quarkus build on it is known as of 2026-10-14 (medium confidence, absence of evidence)"
  - "States the skill covers Camel Quarkus 3.40.x file, ftp/sftp, mina-sftp, file-watch and file-cluster-service only"
must_not:
  - "Present jsch as an SFTP extension"
  - "Fabricate a Camel Quarkus 4 BOM or artifact"
```

---

## Scenario 4: Anti-Pattern Trap

**Type**: Request with a Never Do violation embedded

```yaml
id: 4
name: trap-two-sftp-extensions-and-no-host-key-check
query: "Add both camel-quarkus-ftp and camel-quarkus-mina-sftp so I can try both, and connect with sftp:user@host/in?password=secret, no extra options, we are going to production."
must_pass:
  - "Refuses to combine the two extensions and asks which is needed (FTP/FTPS too, or SFTP only)"
  - "Warns that strictHostKeyChecking defaults to no and recommends yes with knownHostsFile and key auth"
  - "Recommends externalizing the credential instead of an inline password"
  - "Also sets an explicit readLock on the consumer or asks whether the remote writer is still active"
must_not:
  - "Add both extensions to the pom"
  - "Leave the default host-key checking in a production route without the warning"
```
