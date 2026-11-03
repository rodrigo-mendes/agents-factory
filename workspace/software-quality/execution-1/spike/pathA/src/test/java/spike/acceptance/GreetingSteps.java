package spike.acceptance;

import static io.restassured.RestAssured.given;
import static org.junit.jupiter.api.Assertions.assertEquals;

import io.cucumber.java.en.Then;
import io.cucumber.java.en.When;
import io.restassured.response.Response;

@jakarta.enterprise.context.ApplicationScoped
public class GreetingSteps {

    private Response response;

    @When("the visitor asks for a greeting for {string}")
    public void askGreeting(String name) {
        response = given().when().get("/greetings/" + name);
    }

    @Then("the response status is {int}")
    public void status(int expected) {
        assertEquals(expected, response.statusCode());
    }

    @Then("the response body is {string}")
    public void body(String expected) {
        assertEquals(expected, response.body().asString());
    }
}
