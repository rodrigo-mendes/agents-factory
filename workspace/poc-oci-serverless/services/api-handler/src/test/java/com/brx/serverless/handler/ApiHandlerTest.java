package com.brx.serverless.handler;

import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Optional;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;
import org.junit.Before;
import org.junit.Rule;
import org.junit.Test;

import com.brx.serverless.model.ApiRequest;
import com.brx.serverless.model.ApiResponse;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fnproject.events.input.APIGatewayRequestEvent;
import com.fnproject.events.testing.APIGatewayTestFeature;
import com.fnproject.fn.api.Headers;
import com.fnproject.fn.api.QueryParameters;
import com.fnproject.fn.testing.FnResult;
import com.fnproject.fn.testing.FnTestingRule;

public class ApiHandlerTest {

    @Rule
    public final FnTestingRule testing = FnTestingRule.createDefault();

    private final ObjectMapper mapper = new ObjectMapper();

    @Before
    public void setUp() {
        testing.setConfig("LOG_LEVEL", "INFO");

        // Share slf4j, logback and xml classes to prevent ClassLoader constraint linkage errors
        testing.addSharedClassPrefix("org.slf4j.");
        testing.addSharedClassPrefix("ch.qos.logback.");
        testing.addSharedClassPrefix("org.xml.sax.");
        testing.addSharedClassPrefix("javax.xml.parsers.");
        testing.addSharedClassPrefix("com.sun.org.apache.xerces.");
    }

    private static final QueryParameters EMPTY_PARAMS = new QueryParameters() {
        @Override public Optional<String> get(String key) { return Optional.empty(); }
        @Override public List<String> getValues(String key) { return Collections.emptyList(); }
        @Override public Map<String, List<String>> getAll() { return Collections.emptyMap(); }
    };

    private APIGatewayRequestEvent<String> buildRequest(String method, String path, String body) {
        return new APIGatewayRequestEvent<>(
                EMPTY_PARAMS,
                body,
                method,
                path,
                Headers.emptyHeaders()
        );
    }

    private ApiResponse executeAndParse(String method, String path, String body) throws Exception {
        APIGatewayTestFeature apigw = APIGatewayTestFeature.createDefault(testing);
        apigw.givenEvent(buildRequest(method, path, body)).enqueue();
        testing.thenRun(ApiHandler.class, "handler");
        FnResult result = testing.getOnlyResult();
        return mapper.readValue(result.getBodyAsString(), ApiResponse.class);
    }

    // --- Happy path ---

    @Test
    public void testHelloRoute() throws Exception {
        ApiResponse response = executeAndParse("GET", "/hello", null);
        assertEquals(200, response.getStatusCode());
        assertTrue(response.getMessage().contains("Hello from OCI Functions"));
    }

    @Test
    public void testHelloRouteContainsEnvironment() throws Exception {
        testing.setConfig("ENVIRONMENT", "test");
        ApiResponse response = executeAndParse("GET", "/hello", null);
        assertTrue(response.getMessage().contains("test"));
    }

    @Test
    public void testHelloRouteAcceptsPostMethod() throws Exception {
        ApiResponse response = executeAndParse("POST", "/hello", null);
        assertEquals(200, response.getStatusCode());
        assertTrue(response.getMessage().contains("Hello from OCI Functions"));
    }

    // --- Routing edge cases ---

    @Test
    public void testUnknownRoute() throws Exception {
        ApiResponse response = executeAndParse("GET", "/unknown", null);
        assertEquals(404, response.getStatusCode());
        assertTrue(response.getMessage().contains("Route not found"));
    }

    @Test
    public void testEmptyPathReturns404() throws Exception {
        ApiResponse response = executeAndParse("GET", "", null);
        assertEquals(404, response.getStatusCode());
        assertTrue(response.getMessage().contains("Route not found"));
    }

    @Test
    public void testTrailingSlashReturns404() throws Exception {
        ApiResponse response = executeAndParse("GET", "/hello/", null);
        assertEquals(404, response.getStatusCode());
        assertTrue(response.getMessage().contains("Route not found"));
    }

    @Test
    public void testRootPathReturns404() throws Exception {
        ApiResponse response = executeAndParse("GET", "/", null);
        assertEquals(404, response.getStatusCode());
    }

    // --- Request body edge cases ---

    @Test
    public void testHelloRouteWithNullBody() throws Exception {
        ApiResponse response = executeAndParse("GET", "/hello", null);
        assertEquals(200, response.getStatusCode());
    }

    @Test
    public void testHelloRouteWithBody() throws Exception {
        ApiRequest body = new ApiRequest();
        ApiResponse response = executeAndParse("GET", "/hello", mapper.writeValueAsString(body));
        assertEquals(200, response.getStatusCode());
    }

    // --- Configuration ---

    @Test
    public void testDefaultEnvironmentFallback() throws Exception {
        testing.setConfig("ENVIRONMENT", null);
        ApiResponse response = executeAndParse("GET", "/hello", null);
        assertTrue(response.getMessage().contains("dev"));
    }

    // --- Response structure ---

    @Test
    public void testResponseJsonStatusCodeField() throws Exception {
        APIGatewayTestFeature apigw = APIGatewayTestFeature.createDefault(testing);
        apigw.givenEvent(buildRequest("GET", "/hello", null)).enqueue();
        testing.thenRun(ApiHandler.class, "handler");
        FnResult result = testing.getOnlyResult();
        String json = result.getBodyAsString();
        assertTrue("JSON must contain status_code field", json.contains("\"status_code\""));
    }

    @Test
    public void testErrorResponseHasNullData() throws Exception {
        ApiResponse response = executeAndParse("GET", "/unknown", null);
        assertEquals(404, response.getStatusCode());
        assertEquals(null, response.getData());
    }
}
