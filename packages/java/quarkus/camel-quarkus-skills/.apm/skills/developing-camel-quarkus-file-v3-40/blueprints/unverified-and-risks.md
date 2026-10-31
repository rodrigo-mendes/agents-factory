# Unverified Register, Risks and Bibliography

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). The research file reports a quality score of 88% and a deep run that used all 3 iterations. This register lists 13 unverified items (U1-U13), 12 medium-confidence items (M1-M12) and 1 coverage limit (L1). There are no irresolvable items (I): the three that earlier looked irresolvable are tagged (unverified) in the text and listed under U.

## Contents

- [Tag to register mapping](#tag-to-register-mapping)
- [Version-lifetime risk](#version-lifetime-risk)
- [Unverified items](#unverified-items)
- [Medium-confidence items](#medium-confidence-items)
- [Coverage limits](#coverage-limits)
- [Source Bibliography](#source-bibliography)

## Tag to register mapping

Untagged claims are High (versioned official page); medium-confidence and unverified items never appear in Always Do or Never Do.

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (unverified) | Camel Quarkus-specific LTS end date; SKILL.md Version-lifetime risk (not resolvable from documentation) | U1 |
| (unverified) | `GenericFile<File>` runtime body type; file-consumer-producer.md | U2 |
| (unverified) | SSH library of `camel-quarkus-ftp` in native; SKILL.md Ask First "FTP library", native-mode.md, remote-ftp-sftp.md | U3 |
| (unverified) | NotifyBuilder on Camel Quarkus; integration-examples.md | U4 |
| (unverified) | XSLT build-time vs runtime properties; integration-examples.md | U5 |
| (unverified) | Splitter streaming wording for 4.22; never-do-patterns.md #9 | U6 |
| (unverified) | `readLockLoggingLevel` default; file-consumer-producer.md | U7 |
| (unverified) | SFTP `readLockTimeout` default (10000 vs 20000); remote-ftp-sftp.md | U8 |
| (unverified) | Maven plugin `create` command form; integration-examples.md | U9 |
| (unverified) | Release that removes the `camel-quarkus-junit5` stub; this register | U10 |
| (log output unverified) | Output of `mvn verify -Dnative`; SKILL.md Quick Reference, native-mode.md | U11 |
| (unverified) | `heartbeat-timeout-multiplier` default and cluster property build/runtime flags; file-watch-and-cluster.md | U12 |
| (unverified) | Camel 4.13 eager max-messages-per-poll option name and default; migration-guide.md, file-consumer-producer.md | U13 |
| (medium confidence, absence of evidence) | No Camel Quarkus build on Quarkus 4 is known; SKILL.md, migration-guide.md, evaluation-scenarios.md, this register | M1 |
| (medium confidence) | Camel 4.10, 4.11 and 4.18 upgrade-guide entries; migration-guide.md | M2 |
| (medium confidence) | Remote path jail (4.21, 4.22.1); SKILL.md Ask First, migration-guide.md, remote-ftp-sftp.md | M3 |
| (medium confidence) | `forceWrites` and boolean `preSort` (4.22); SKILL.md Ask First, migration-guide.md, file-consumer-producer.md, never-do-patterns.md #7 | M4 |
| (medium confidence) | `file-cluster-service` property defaults; SKILL.md Ask First and Quick Reference, file-watch-and-cluster.md | M5 |
| (medium confidence) | Polling vs events trade-off (inferred from the options); SKILL.md Ask First | M6 |
| (medium confidence) | Large-file memory behaviour; SKILL.md Ask First, remote-ftp-sftp.md, never-do-patterns.md #9 | M7 |
| (medium confidence) | Dynamic directory paths, security framing; SKILL.md Ask First, never-do-patterns.md #8 | M8 |
| (medium confidence) | Inference that `readLock=fileLock` on a share risks double processing; never-do-patterns.md #2 | M9 |
| (medium confidence) | Inference that add-all-charsets "just in case" is wrong; never-do-patterns.md #6 ("inferred") | M10 |
| (medium confidence) | Samples taken from the `main` branch; always-do-patterns.md #2, integration-examples.md | M11 |
| (medium confidence) | Multi-node coordination patterns (shared repository, cluster singleton); never-do-patterns.md #2, SKILL.md Ask First "Several instances" | M12 |

## Version-lifetime risk

- Quarkus 4.0.0.Beta1 was published 2026-10-01; the final release is "planned for the end of November"; the highlights list Java 21 as the new base version (High, https://quarkus.io/blog/quarkus-4-0-0-beta1-released/, fetched 2026-10-14). No Camel Quarkus build on Quarkus 4 is known; the Beta1 post does not mention Camel Quarkus (medium confidence, absence of evidence), see M1. Plan a migration with no known date and do not assume Quarkus 4 compatibility.
- Quarkus 3.40 was released 2026-09-30 as an LTS and is community-maintained until 2027-09-30 (High, https://quarkus.io/releases). The Camel Quarkus-specific end date is (unverified), see U1: the "LTS Until" column on https://camel.apache.org/camel-quarkus/latest/ is blank. Applying the Quarkus date to Camel Quarkus is an inference.
- Camel Quarkus 3.40.0 was released 2026-09-28 and is marked LTS (High, https://camel.apache.org/releases/; no LTS-until date given), 16 days before the research date. The docs looked complete, but patch releases are expected.
- `camel-quarkus-junit5` was renamed `camel-quarkus-junit` (since 3.31; High, https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.31.0.html). `camel-quarkus-junit5` 3.40.0 is still published as a deprecated stub ("DEPRECATED: This artifact has moved to org.apache.camel.quarkus:camel-quarkus-junit"; only dependency `camel-quarkus-junit`; no relocation element; High, https://repo1.maven.org/maven2/org/apache/camel/quarkus/camel-quarkus-junit5/3.40.0/camel-quarkus-junit5-3.40.0.pom, fetched 2026-10-14). The release that removes the stub is (unverified), see U10 (the 3.31 guide said "until 3.34.0 is released"); prefer `camel-quarkus-junit`.

## Unverified items

- U1: Camel Quarkus-specific LTS end date for 3.40: not resolvable from documentation ("LTS Until" is blank). Quarkus 3.40 LTS to 2027-09-30 is an inference only.
- U2: Runtime body type `GenericFile<File>` (the page says only "a `File` object").
- U3: SSH library the `camel-quarkus-ftp` extension uses in native mode.
- U4: NotifyBuilder support on Camel Quarkus (not covered by the testing guide).
- U5: XSLT build-time vs runtime property split.
- U6: Splitter streaming wording for Camel 4.22 (Camel EIP, not re-fetched).
- U7: `readLockLoggingLevel` default.
- U8: SFTP `readLockTimeout` default: `10000` per the SFTP summary vs `20000` per the File page, which gives `20000` as the FTP default. The file consumer default of `10000` (SKILL.md Quick Reference) is a separate, sourced value and does not conflict. Set it explicitly.
- U9: Maven plugin `create` command form for this exact invocation.
- U10: Release in which the deprecated `camel-quarkus-junit5` stub will be removed (3.40.0 still publishes it; the 3.31 guide said "until 3.34.0 is released").
- U11: Log output of `mvn verify -Dnative`.
- U12: `quarkus.camel.cluster.file.heartbeat-timeout-multiplier` default, and the build-time vs runtime flag of each cluster property. Set it explicitly; check `file-cluster-service.html` or the extension source.
- U13: Camel 4.13 eager max-messages-per-poll change (option name, old and new default; investigators disagreed). Check the real name in `camel-4x-upgrade-guide-4_13.html`; do not use a guessed name.

The `CamelQuarkusTestSupport` package and the `doBeforeEach`/`adviceRoute` signatures are not unverified: they are stated in the skill `developing-camel-quarkus-junit-v3-40`.

## Medium-confidence items

- M1: No Camel Quarkus build on Quarkus 4 is known (absence of evidence; the Beta1 post does not mention Camel Quarkus).
- M2: Upgrade-guide entries for Camel 4.10, 4.11 and 4.18.
- M3: Remote-consumer path jail (4.21 and 4.22.1 notes; guides partly read, see L1).
- M4: `forceWrites` deprecation and String `preSort` in 4.22 (guide partly read, see L1).
- M5: `quarkus.camel.cluster.file.*` property defaults (read through a tool summary).
- M6: Polling-vs-events trade-off (inferred from the options).
- M7: Large-file memory behaviour (`localWorkDirectory`, `streamDownload`).
- M8: Dynamic directory paths: the security framing is an inference.
- M9: `readLock=fileLock` on a share risks double processing (inference from the page's "should be avoided" wording).
- M10: Enabling add-all-charsets "just in case" is wrong (inference).
- M11: Samples taken from the `main` branch of camel-quarkus, not the 3.40.x tag.
- M12: Multi-node coordination patterns (shared `idempotentRepository`, cluster singleton).

## Coverage limits

- L1: The Camel 4.18, 4.21 and 4.22 upgrade guides were only partly read; entries from them are tagged (medium confidence) (the 4.18 entry in M2, plus M3 and M4).

## Source Bibliography

All fetched 2026-10-14. camel.apache.org pages have no page date and are the current stable 3.40.x / 4.22.x docs. No community sources were used. The tool returns summaries, so confirm exact wording on the live page before quoting.

- https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/file.html
- https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/file-cluster-service.html
- https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/file-watch.html
- https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/ftp.html
- https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/mina-sftp.html
- https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/xslt.html
- https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/jaxb.html
- https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/bean.html
- https://camel.apache.org/camel-quarkus/3.40.x/reference/index.html
- https://camel.apache.org/camel-quarkus/3.40.x/user-guide/native-mode.html
- https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html
- https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html
- https://camel.apache.org/camel-quarkus/latest/
- https://camel.apache.org/components/4.22.x/file-component.html
- https://camel.apache.org/components/4.22.x/languages/file-language.html
- https://camel.apache.org/components/4.22.x/file-watch-component.html
- https://camel.apache.org/components/4.22.x/sftp-component.html
- https://camel.apache.org/manual/camel-4x-upgrade-guide.html and per-version pages `-4_9` to `-4_22` (4_18, 4_21 and 4_22 read only partially)
- https://camel.apache.org/releases/ and https://camel.apache.org/releases/q-3.40.0/
- https://repo1.maven.org/maven2/org/apache/camel/quarkus/camel-quarkus-file/ (3.40.0, 2026-09-24)
- https://repo1.maven.org/maven2/org/apache/camel/quarkus/camel-quarkus-ftp/ (3.40.0, 2026-09-24)
- https://repo1.maven.org/maven2/org/apache/camel/quarkus/camel-quarkus-junit5/3.40.0/camel-quarkus-junit5-3.40.0.pom (fetched 2026-10-14)
- https://quarkus.io/releases ; https://quarkus.io/blog/quarkus-4-0-0-beta1-released/ (2026-10-01) ; https://quarkus.io/blog/mandrel-25-minimum-version/ (2026-05-29)
- Validation (`main` branch, not a 3.40.x tag): https://raw.githubusercontent.com/apache/camel-quarkus/main/integration-tests/file/src/main/java/org/apache/camel/quarkus/component/file/it/FileRoutes.java and `.../FileResource.java`
