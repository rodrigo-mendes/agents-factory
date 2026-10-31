# Reusable workflow `_java-build.yml`

Back to [SKILL.md](../SKILL.md). setup-java v6.1.0, gradle/actions v6.4.1, checkout v7.0.1, upload-artifact v7.0.2. Research date 2026-10-30.

Contents: [Workflow](#workflow) | [Notes](#notes)

## Workflow

A reusable workflow takes typed inputs, declares explicit outputs, receives no secrets, sets its own minimal permissions and a job timeout. Inputs reach shell steps only through `env:`.

```yaml
# ./.github/workflows/_java-build.yml
name: _java-build
on:
  workflow_call:
    inputs:
      tool:              { type: string, required: true,  description: 'maven or gradle' }
      java-version:      { type: string, required: false, default: '25', description: 'JDK major: 17, 21 or 25' }
      package:           { type: string, required: false, default: jar, description: 'jar, zip or image' }
      working-directory: { type: string, required: false, default: '.', description: 'project root' }
    outputs:
      artifact-name:   { description: 'uploaded artifact name', value: '${{ jobs.build.outputs.artifact-name }}' }
      artifact-digest: { description: 'SHA-256 digest of the uploaded artifact', value: '${{ jobs.build.outputs.artifact-digest }}' }
permissions:
  contents: read
jobs:
  build:
    runs-on: ubuntu-latest
    timeout-minutes: 30   # default is 360; a hung build must not burn six hours
    defaults:
      run:
        working-directory: ${{ inputs.working-directory }}
    outputs:
      artifact-name:   ${{ steps.pkg.outputs.name }}
      artifact-digest: ${{ steps.up.outputs.artifact-digest }}
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - name: Validate inputs and derive slug
        id: val
        env: { TOOL: '${{ inputs.tool }}', PACKAGE: '${{ inputs.package }}', WD: '${{ inputs.working-directory }}' }
        run: |
          case "$TOOL" in maven|gradle) ;; *) echo "tool must be maven or gradle" >&2; exit 1;; esac
          case "$PACKAGE" in jar|zip|image) ;; *) echo "package must be jar, zip or image" >&2; exit 1;; esac
          slug=$(printf '%s' "$WD" | sed 's/[^A-Za-z0-9]/-/g; s/^-*//; s/-*$//')
          echo "slug=${slug:-root}" >> "$GITHUB_OUTPUT"
      - uses: ./.github/actions/build/setup-java-build
        with:
          tool: ${{ inputs.tool }}
          java-version: ${{ inputs.java-version }}
      - if: ${{ inputs.tool == 'maven' }}
        run: ./mvnw -B -ntp verify
      - if: ${{ inputs.tool == 'gradle' }}
        env: { PACKAGE: '${{ inputs.package }}' }
        run: |
          if [ "$PACKAGE" = "zip" ]; then ./gradlew build buildZip; else ./gradlew build; fi
      - name: Maven Lambda zip
        if: ${{ inputs.tool == 'maven' && inputs.package == 'zip' }}
        run: |
          mkdir -p dist/stage/lib
          find target -maxdepth 1 -name '*.jar' ! -name 'original-*.jar' -exec cp {} dist/stage/lib/ \;
          (cd dist/stage && zip -r ../function.zip lib)
      - name: Test summary
        if: ${{ always() }}
        env: { JAVA_VERSION: '${{ inputs.java-version }}' }
        run: |
          shopt -s nullglob
          files=(target/surefire-reports/TEST-*.xml target/failsafe-reports/TEST-*.xml build/test-results/test/TEST-*.xml)
          t=0; f=0; e=0; s=0
          for x in "${files[@]}"; do
            line=$(grep -m1 -o '<testsuite [^>]*>' "$x" || true)
            get() { echo "$line" | sed -n "s/.* $1=\"\([0-9]*\)\".*/\1/p"; }
            t=$((t+$(get tests))); f=$((f+$(get failures))); e=$((e+$(get errors))); s=$((s+$(get skipped)))
          done
          { echo "### Tests (JDK $JAVA_VERSION)"; echo "| total | failed | errors | skipped |"
            echo "|---|---|---|---|"; echo "| $t | $f | $e | $s |"; } >> "$GITHUB_STEP_SUMMARY"
      - name: Upload test and coverage reports
        if: ${{ always() }}
        uses: actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9 # v7.0.2
        with:
          name: test-reports-${{ steps.val.outputs.slug }}-${{ inputs.tool }}-jdk${{ inputs.java-version }}-${{ github.run_attempt }}
          path: |
            ${{ inputs.working-directory }}/target/surefire-reports/
            ${{ inputs.working-directory }}/target/failsafe-reports/
            ${{ inputs.working-directory }}/target/site/jacoco/
            ${{ inputs.working-directory }}/build/reports/jacoco/test/html/
            ${{ inputs.working-directory }}/build/test-results/test/
          retention-days: 7
          if-no-files-found: warn
      - name: Select package path
        id: pkg
        env: { TOOL: '${{ inputs.tool }}', PACKAGE: '${{ inputs.package }}', JDK: '${{ inputs.java-version }}', SLUG: '${{ steps.val.outputs.slug }}' }
        run: |
          case "$TOOL-$PACKAGE" in
            maven-zip)  p='dist/function.zip' ;;
            maven-*)    p='target/*.jar' ;;
            gradle-zip) p='build/distributions/*.zip' ;;
            gradle-*)   p='build/libs/*.jar' ;;
          esac
          echo "path=$p" >> "$GITHUB_OUTPUT"
          echo "name=app-${GITHUB_SHA}-${SLUG}-jdk${JDK}" >> "$GITHUB_OUTPUT"
      - id: up
        uses: actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9 # v7.0.2
        with:
          name: ${{ steps.pkg.outputs.name }}
          path: |
            ${{ inputs.working-directory }}/${{ steps.pkg.outputs.path }}
            !${{ inputs.working-directory }}/target/original-*.jar
          retention-days: 14
          if-no-files-found: error
```

## Notes

- `package: image` uploads the JAR; the image itself is built by `publishing-container-images-github-actions` (see [hand-off](./lambda-and-image-handoff.md)). This workflow never pushes an image.
- The composite passes no cache-write input to setup-java: its README documents none for `cache: maven`. PR cache scoping is GitHub's own (see Ask First in [SKILL.md](../SKILL.md#-ask-first)).
- The `!…/original-*.jar` line excludes the pre-shade JAR that the Shade plugin leaves beside the shaded one.
- The artifact name carries a slug of `working-directory` (`root` for `.`), so two callers in one run never collide.
- The summary parser reads the `tests`, `failures`, `errors`, `skipped` attributes of the first `<testsuite` tag (medium confidence). Representative: adapt to your report layout.
- The `if: ${{ always() }}` form keeps report steps running after a failed test step (medium confidence).
- Availability of the `inputs` context in `defaults.run.working-directory` and in a local composite action's `with:` was not confirmed on a page (unverified).
- The Maven zip step uses the `zip` binary, whose presence on `ubuntu-latest` was not checked (unverified).
- One job-level matrix leg should package: pass `package: zip` or `image` only from `cd-<app>.yml`; `ci-<app>.yml` uses `jar`. The artifact name carries the JDK and the slug so matrix legs never collide.
- The `GITHUB_SHA` on `pull_request` is the merge commit of the PR ref, so a CI artifact is not the commit that lands; only the `cd-` build is promoted.
