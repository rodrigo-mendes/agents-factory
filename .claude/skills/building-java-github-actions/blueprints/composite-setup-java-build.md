# Composite action `setup-java-build`

Back to [SKILL.md](../SKILL.md). setup-java v6.1.0, gradle/actions v6.4.1. Research date 2026-10-30.

## Action

Path: `./.github/actions/build/setup-java-build/action.yml` (composite actions live under `.github/actions/<group>/<name>/`). It must run after `actions/checkout`, because a local action is read from the workspace.

```yaml
name: setup-java-build
description: Install a Temurin JDK and the right dependency cache for Maven or Gradle
inputs:
  tool:
    description: 'maven or gradle'
    required: true
  java-version:
    description: 'JDK major version'
    required: false
    default: '25'
  gradle-cache-provider:
    description: 'basic (default) or enhanced; enhanced needs Terms of Use acceptance'
    required: false
    default: 'basic'
runs:
  using: composite
  steps:
    - if: ${{ inputs.tool == 'maven' }}
      uses: actions/setup-java@b843ebf9b913146b38da2eaa7aeddf76074ae1ad # v6.1.0
      with:
        distribution: temurin
        java-version: ${{ inputs.java-version }}
        cache: maven
    - if: ${{ inputs.tool == 'gradle' }}
      uses: actions/setup-java@b843ebf9b913146b38da2eaa7aeddf76074ae1ad # v6.1.0
      with:
        distribution: temurin
        java-version: ${{ inputs.java-version }}
    - if: ${{ inputs.tool == 'gradle' }}
      uses: gradle/actions/setup-gradle@8da46b539cd8fe6ab27ca75128919a18d757604c # v6.4.1
      with:
        cache-provider: ${{ inputs.gradle-cache-provider }}
```

## Design notes

- Two setup-java steps with `if:` replace one step with `cache: ''`, because the empty-string behaviour of `cache` is not stated in the README (unverified).
- Gradle gets no setup-java `cache`; setup-gradle owns the Gradle User Home (see N7 in [never-do patterns](./never-do-patterns.md)).
- `cache-provider: basic` is the default because the family targets private repositories and `enhanced` requires accepting Terms of Use (Ask First in [SKILL.md](../SKILL.md#-ask-first)).
- setup-gradle validates the wrapper by default; the action sets no `validate-wrappers` input.
- Gradle wrapper and `gradlew` live in the project root; a build root other than the repository root was not checked against setup-gradle inputs (unverified).
- Pass `enhanced` only after the user accepts the terms; keep the choice visible in the caller, not inside the reusable workflow.
