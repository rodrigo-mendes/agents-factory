package spike.acceptance;

import static org.junit.jupiter.api.Assertions.assertEquals;

import io.quarkus.test.junit.QuarkusIntegrationTest;
import org.junit.jupiter.api.Test;

/**
 * Variant B1: Quarkus starts the packaged jar (black-box) and configures RestAssured's port;
 * Cucumber runs in the same JVM through its public CLI entry point.
 */
@QuarkusIntegrationTest
class AcceptanceIT {

    @Test
    void features() {
        byte status = io.cucumber.core.cli.Main.run(
                new String[] {
                    "--glue", "spike.acceptance",
                    "--plugin", "pretty",
                    "--tags", "not @wip",
                    "classpath:features"
                },
                Thread.currentThread().getContextClassLoader());
        assertEquals(0, status, "Cucumber scenarios failed");
    }
}
