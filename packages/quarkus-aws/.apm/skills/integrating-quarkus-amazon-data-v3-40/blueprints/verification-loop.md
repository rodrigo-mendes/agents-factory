# Verification Loop

Back to [SKILL.md](../SKILL.md). Representative commands; adapt to your environment. Run after every change to the data-client setup and stop at the first unexpected output.

```bash
# 1. BOM line is 3.23.0 and no Quarkus 4 line leaked in
grep -n "quarkus-amazon-services-bom" -A1 pom.xml | grep -E "3\.23\.0"     # Expected: one match
grep -nE "4\.0\.0\.Beta" pom.xml                                            # Expected: no output

# 2. The HTTP client artifact matches the configured type (A2)
mvn -q dependency:tree -Dincludes=software.amazon.awssdk:url-connection-client,software.amazon.awssdk:aws-crt-client,software.amazon.awssdk:netty-nio-client,software.amazon.awssdk:apache-client
grep -nE "quarkus\.(s3|dynamodb)\.(sync|async)-client\.type" src/main/resources/application.properties

# 3. No static keys, no global endpoint-override (F1, F7)
grep -nE "credentials\.(type=static|static-provider)" src/main/resources/application.properties   # Expected: no output
grep -nE "^quarkus\.(s3|dynamodb)\.endpoint-override" src/main/resources/application.properties   # Expected: no output

# 4. Streams closed and queries paginated (F3, F4): heuristic, review each hit
grep -rn "getObject(" src/main/java | grep -v "try ("
grep -rnE "\.query\(|\.scan\(" src/main/java

# 5. Build the Lambda artifact (family rule 4: function.zip)
./mvnw clean package        # Expected: target/function.zip
```

Checks 1, 3 and the `grep` parts of 2 and 4 are pure text checks; the heuristic ones in check 4 can miss a closed stream held elsewhere, so read the hits. Tenant isolation, region resolution and `@Inject S3Presigner` cannot be verified by these commands: confirm them in a deployed function or a test ([C3](./ask-first-decisions.md#c3-region), [C4](./ask-first-data-decisions.md#c4-tenant-isolation-model), [C5](./ask-first-data-decisions.md#c5-s3presigner)).
