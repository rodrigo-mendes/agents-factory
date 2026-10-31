---
name: java-environment-validation
description: "Pre-build environment validation rules for OCI Functions Java (Java version, Maven version, Docker, OCIR credentials). Use when running mvn compile/test or before any build command."
paths:
  - "**/pom.xml"
  - "**/func.yaml"
  - "**/Dockerfile"
  - "**/*.java"
---
You are an OCI Functions Build Environment specialist.
Before executing ANY Maven command (compile, test, package), validate that the Java environment is consistent and matches the project target.

## Mandatory Pre-Build Validation

Before running `mvn compile`, `mvn test`, or any Maven lifecycle command, ALWAYS execute:

```bash
java -version 2>&1 && mvn -version 2>&1 | grep -i "java version"
```

If the reported Java versions **differ** (e.g., `java` shows 21 but Maven shows 25):
1. STOP — do NOT proceed with compilation or test debugging
2. Alert the user: "⚠️ JVM mismatch detected: `java` reports vX but Maven uses vY"
3. Suggest fix: `export JAVA_HOME=$(/usr/libexec/java_home -v 21)` (macOS)
4. Re-run Maven with explicit JAVA_HOME if user cannot change system default

## Target JVM Version

- **Project target**: Java 17 (source/target in pom.xml)
- **Tested runtime**: Java 21 (Amazon Corretto)
- **Container runtime**: JRE 17 (fnproject/fn-java-fdk:jre17-latest)
- **NOT supported for testing**: Java 25+ (sealed classes break Mockito mocking of HttpClient, HttpResponse)

## Common JVM Mismatch Scenarios

### macOS with Multiple JDKs
```
Symptom: java -version → Corretto 21, but mvn -version → Homebrew OpenJDK 25
Cause: Maven resolves JAVA_HOME differently from shell PATH
Fix: export JAVA_HOME=$(/usr/libexec/java_home -v 21)
```

### Mockito "Cannot Mock" Errors
```
Symptom: "Mockito cannot mock this class: class java.net.http.HttpClient"
        "Java: 25, JVM vendor: Homebrew"
Cause: Java 25 sealed classes prevent ByteBuddy subclassing
Fix: Switch to Java 21 — do NOT create wrapper interfaces as workaround
```

### JaCoCo "Unsupported Class File Major Version"
```
Symptom: "Unsupported class file major version 69" during test execution
Cause: JaCoCo version incompatible with JVM bytecode version
Fix: Either (a) downgrade JVM to 21, or (b) upgrade JaCoCo to 0.8.13+
```

## .mvn/jvm.config Template

Every Java function project SHOULD include `.mvn/jvm.config`:
```
# Intentionally empty — ensures Maven uses JAVA_HOME consistently
# If specific JVM args needed, add them here (one per line)
```

## Diagnostic Decision Tree

When tests fail with infrastructure errors (not assertion failures):

```
1. Check JVM version match
   → java -version vs mvn -version | grep Java
   → If mismatch → Fix JAVA_HOME → Retry

2. Check for Mockito errors mentioning Java version
   → If "Java: 25" in error → JVM problem, not code problem
   → Do NOT refactor code; fix JVM instead

3. Check for "major version" errors
   → version 65 = Java 21, version 69 = Java 25
   → Upgrade JaCoCo or downgrade JVM

4. Only if JVM is correct, debug actual test logic
```

## ✅ Always Do
- Validate JVM version consistency BEFORE any Maven command
- Use Java 21 (Corretto) for local development and testing
- Report JVM mismatch to user immediately — do not attempt workarounds
- Check `mvn -version` output (not just `java -version`) — Maven may use different JDK

## 🚫 Never Do
- Debug test failures without first validating JVM version
- Create interface wrappers (e.g., HttpSender) to work around JVM incompatibility — fix the JVM instead
- Override ByteBuddy version to fix Mockito issues on wrong JVM — the override IS the problem
- Assume `java -version` reflects what Maven uses — always verify both
- Attempt to make tests pass on Java 25+ when project targets Java 17/21
