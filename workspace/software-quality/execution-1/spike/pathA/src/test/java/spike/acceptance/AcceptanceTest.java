package spike.acceptance;

import io.quarkiverse.cucumber.CucumberOptions;
import io.quarkiverse.cucumber.CucumberQuarkusTest;

@CucumberOptions(features = "classpath:features", glue = "spike.acceptance")
public class AcceptanceTest extends CucumberQuarkusTest {
}
