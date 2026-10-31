# File Processing Blueprint

Back to [SKILL.md](../SKILL.md). Shared workflow, structure skill and boundaries live there; this file holds only the file-handling specialty.

## Specializations

1. **Local files**: consume from a directory, write output files, watch a directory for changes.
2. **Remote files**: FTP, FTPS and SFTP download and upload.
3. **Hand-off of content**: this specialty reads and writes files; parsing and format conversion belong to the data transformation blueprint (see Cross-references in SKILL.md).

Coverage note: no installed skill documents CSV or Excel parsing. If the user needs it, say it is not documented, ask whether to proceed with raw file handling only, and offer `/researching-technical-frameworks`.

## Required Skills

| Need | Skill |
|---|---|
| Always | `developing-camel-quarkus-file-v3-40`, `developing-camel-quarkus-core-v3-40`, `structuring-camel-quarkus-projects` |
| Convert file content (XML) | `developing-camel-quarkus-jaxb-v3-40` or `developing-camel-quarkus-xslt-v3-40` via the data transformation blueprint |
| Log processed files | `developing-camel-quarkus-log-v3-40` |
| Tests that wait for file output | `developing-camel-quarkus-junit-v3-40` via the testing blueprint |

## What to Ask

- Directory or remote path, file name pattern, and whether other processes write into the folder.
- What happens to a file after success and after failure (keep, move, delete).
- Remote server type (FTP, FTPS or SFTP only), authentication method, host key policy.
- Typical and maximum file size; one instance or several replicas.

## Ask First Decisions

| Decision | Options | Source |
|---|---|---|
| Post-processing | `.camel` default vs move vs delete vs noop | Ask First in the file skill |
| Several instances | Single vs file-cluster-service vs shared idempotent repository | Ask First in the file skill |
| FTP library | `camel-quarkus-ftp` vs `camel-quarkus-mina-sftp`; one per application | Ask First and Always Do in the file skill |
| Polling vs events (medium confidence) | `file:` vs `file-watch:` | Ask First in the file skill |
| Large remote files (medium confidence) | Local work directory or streaming vs in-memory | Ask First in the file skill |
| Dynamic paths (medium confidence) | Fixed root plus a validated file name vs a directory built from input | Ask First in the file skill |
| Credentials storage | Secrets management is not covered; see [Out of Scope](../SKILL.md#out-of-scope) | User |

## Quality Standards

### ✅ Always Do

- **Set `readLock` explicitly** on consumers of folders other processes write to (file skill, Always Do).
- **Make post-processing explicit** (move, delete or noop) (file skill, Always Do).
- **Read paths and patterns from configuration** (team convention).
- **Use `strictHostKeyChecking=yes` with a known-hosts file for SFTP** (file skill, Always Do).

### ⚠️ Ask First

- **Validating any dynamic file name** (medium confidence; file skill, Ask First "Dynamic paths").
- **Idempotency** across restarts or nodes.
- **Atomic writes** (temp name or done-file) if downstream polls the output folder.
- **Charset** when native builds read a non-UTF-8 file.

### 🚫 Never Do

- **Never hardcode paths or patterns.** Instead: configuration properties (team convention).
- **Never put `camel-quarkus-ftp` and `camel-quarkus-mina-sftp` in one build.** Instead: pick one.
- **Never use `camel-quarkus-jsch` for SFTP.** Instead: `camel-quarkus-ftp` or `camel-quarkus-mina-sftp` (it is SCP).
- **Never use unencrypted FTP for sensitive data.** Instead: SFTP or FTPS.
