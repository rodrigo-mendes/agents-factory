package com.brx.functions.apifacade;

import java.net.SocketTimeoutException;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Optional;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;
import org.junit.Before;
import org.junit.Rule;
import org.junit.Test;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.doThrow;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.brx.functions.apifacade.model.ApiFacadeRequest;
import com.brx.functions.apifacade.model.ApiFacadeResponse;
import com.brx.functions.apifacade.service.OciService;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fnproject.events.input.APIGatewayRequestEvent;
import com.fnproject.events.testing.APIGatewayTestFeature;
import com.fnproject.fn.api.Headers;
import com.fnproject.fn.api.QueryParameters;
import com.fnproject.fn.testing.FnResult;
import com.fnproject.fn.testing.FnTestingRule;
import com.oracle.bmc.model.BmcException;

public class ApiFacadeFunctionTest {

    @Rule
    public final FnTestingRule testing = FnTestingRule.createDefault();

    private final ObjectMapper mapper = new ObjectMapper();
    private OciService mockOciService;

    @Before
    public void setUp() {
        testing.setConfig("ENVIRONMENT", "test");
        testing.addSharedClass(MockOciServiceHolder.class);
        testing.addSharedClassPrefix("com.brx.functions.apifacade.service.");
        testing.addSharedClassPrefix("com.oracle.bmc.");
        
        // Share slf4j, logback and xml classes to prevent ClassLoader constraint linkage errors
        testing.addSharedClassPrefix("org.slf4j.");
        testing.addSharedClassPrefix("ch.qos.logback.");
        testing.addSharedClassPrefix("org.xml.sax.");
        testing.addSharedClassPrefix("javax.xml.parsers.");
        testing.addSharedClassPrefix("com.sun.org.apache.xerces.");

        mockOciService = mock(OciService.class);
        MockOciServiceHolder.ociService = mockOciService;
    }

    private static final QueryParameters EMPTY_PARAMS = new QueryParameters() {
        @Override public Optional<String> get(String key) { return Optional.empty(); }
        @Override public List<String> getValues(String key) { return Collections.emptyList(); }
        @Override public Map<String, List<String>> getAll() { return Collections.emptyMap(); }
    };

    private APIGatewayRequestEvent<String> buildRequest(String method, String path, ApiFacadeRequest body) throws Exception {
        String jsonBody = body != null ? mapper.writeValueAsString(body) : null;
        return new APIGatewayRequestEvent<>(
                EMPTY_PARAMS,
                jsonBody,
                method,
                path,
                Headers.emptyHeaders()
        );
    }

    private ApiFacadeResponse executeAndParse(String method, String path, ApiFacadeRequest body) throws Exception {
        APIGatewayTestFeature apigw = APIGatewayTestFeature.createDefault(testing);
        apigw.givenEvent(buildRequest(method, path, body)).enqueue();
        testing.thenRun(ApiFacadeFunction.class, "handler");
        FnResult result = testing.getOnlyResult();
        return mapper.readValue(result.getBodyAsString(), ApiFacadeResponse.class);
    }

    // ===== /hello route =====

    @Test
    public void testHelloRoute() throws Exception {
        ApiFacadeResponse response = executeAndParse("GET", "/hello", null);
        assertEquals(200, response.getStatusCode());
        assertTrue(response.getMessage().contains("Hello from API Facade"));
        assertTrue(response.getMessage().contains("test"));
    }

    @Test
    public void testHelloRoutePost() throws Exception {
        ApiFacadeResponse response = executeAndParse("POST", "/hello", null);
        assertEquals(200, response.getStatusCode());
        assertTrue(response.getMessage().contains("Hello from API Facade"));
    }

    // ===== Unknown route =====

    @Test
    public void testUnknownRoute() throws Exception {
        ApiFacadeResponse response = executeAndParse("GET", "/unknown", null);
        assertEquals(404, response.getStatusCode());
        assertTrue(response.getMessage().contains("Route not found"));
        assertTrue(response.getMessage().contains("/unknown"));
    }

    // ===== /secret route — validation =====

    @Test
    public void testSecretRouteWrongMethod() throws Exception {
        ApiFacadeResponse response = executeAndParse("GET", "/secret", null);
        assertEquals(405, response.getStatusCode());
        assertTrue(response.getMessage().contains("Method not allowed"));
    }

    @Test
    public void testSecretRouteNullBody() throws Exception {
        ApiFacadeResponse response = executeAndParse("POST", "/secret", null);
        assertEquals(400, response.getStatusCode());
        assertTrue(response.getMessage().contains("resource_id"));
    }

    @Test
    public void testSecretRouteMissingResourceId() throws Exception {
        ApiFacadeResponse response = executeAndParse("POST", "/secret", new ApiFacadeRequest());
        assertEquals(400, response.getStatusCode());
        assertTrue(response.getMessage().contains("resource_id"));
    }

    @Test
    public void testSecretRouteEmptyResourceId() throws Exception {
        ApiFacadeRequest req = new ApiFacadeRequest();
        req.setResourceId("");
        ApiFacadeResponse response = executeAndParse("POST", "/secret", req);
        assertEquals(400, response.getStatusCode());
        assertTrue(response.getMessage().contains("resource_id"));
    }

    // ===== /secret route — happy path =====

    @Test
    public void testSecretRouteSuccess() throws Exception {
        when(mockOciService.getSecret("ocid1.secret.oc1..test"))
                .thenReturn("my-secret-value");

        ApiFacadeRequest req = new ApiFacadeRequest();
        req.setResourceId("ocid1.secret.oc1..test");

        ApiFacadeResponse response = executeAndParse("POST", "/secret", req);
        assertEquals(200, response.getStatusCode());
        assertTrue(response.getMessage().contains("Secret retrieved successfully"));
        assertEquals("my-secret-value", response.getData());
    }

    // ===== /secret route — OCI unavailable =====

    @Test
    public void testSecretRouteOciUnavailable() throws Exception {
        MockOciServiceHolder.ociService = null;

        ApiFacadeRequest req = new ApiFacadeRequest();
        req.setResourceId("ocid1.secret.oc1..test");

        ApiFacadeResponse response = executeAndParse("POST", "/secret", req);
        assertEquals(503, response.getStatusCode());
        assertTrue(response.getMessage().contains("OCI services unavailable"));
    }

    // ===== /store route — validation =====

    @Test
    public void testStoreRouteWrongMethod() throws Exception {
        ApiFacadeResponse response = executeAndParse("GET", "/store", null);
        assertEquals(405, response.getStatusCode());
        assertTrue(response.getMessage().contains("Method not allowed"));
    }

    @Test
    public void testStoreRouteNullBody() throws Exception {
        ApiFacadeResponse response = executeAndParse("POST", "/store", null);
        assertEquals(400, response.getStatusCode());
        assertTrue(response.getMessage().contains("bucket_name"));
    }

    @Test
    public void testStoreRouteMissingFields() throws Exception {
        ApiFacadeResponse response = executeAndParse("POST", "/store", new ApiFacadeRequest());
        assertEquals(400, response.getStatusCode());
        assertTrue(response.getMessage().contains("bucket_name"));
    }

    @Test
    public void testStoreRouteMissingObjectName() throws Exception {
        ApiFacadeRequest req = new ApiFacadeRequest();
        req.setBucketName("my-bucket");
        ApiFacadeResponse response = executeAndParse("POST", "/store", req);
        assertEquals(400, response.getStatusCode());
        assertTrue(response.getMessage().contains("object_name"));
    }

    @Test
    public void testStoreRouteEmptyBucketName() throws Exception {
        ApiFacadeRequest req = new ApiFacadeRequest();
        req.setBucketName("");
        req.setObjectName("file.txt");
        ApiFacadeResponse response = executeAndParse("POST", "/store", req);
        assertEquals(400, response.getStatusCode());
        assertTrue(response.getMessage().contains("bucket_name"));
    }

    @Test
    public void testStoreRouteEmptyObjectName() throws Exception {
        ApiFacadeRequest req = new ApiFacadeRequest();
        req.setBucketName("my-bucket");
        req.setObjectName("");
        ApiFacadeResponse response = executeAndParse("POST", "/store", req);
        assertEquals(400, response.getStatusCode());
        assertTrue(response.getMessage().contains("object_name"));
    }

    // ===== /store route — happy path =====

    @Test
    public void testStoreRouteSuccess() throws Exception {
        ApiFacadeRequest req = new ApiFacadeRequest();
        req.setBucketName("my-bucket");
        req.setObjectName("file.txt");
        req.setData("file content");

        ApiFacadeResponse response = executeAndParse("POST", "/store", req);
        assertEquals(200, response.getStatusCode());
        assertTrue(response.getMessage().contains("Object stored successfully"));
        verify(mockOciService).putObject("my-bucket", "file.txt", "file content");
    }

    @Test
    public void testStoreRouteSuccessNullData() throws Exception {
        ApiFacadeRequest req = new ApiFacadeRequest();
        req.setBucketName("my-bucket");
        req.setObjectName("file.txt");
        // data is null — exercises the ternary operator

        ApiFacadeResponse response = executeAndParse("POST", "/store", req);
        assertEquals(200, response.getStatusCode());
        assertTrue(response.getMessage().contains("Object stored successfully"));
        verify(mockOciService).putObject("my-bucket", "file.txt", "");
    }

    // ===== /store route — OCI unavailable =====

    @Test
    public void testStoreRouteOciUnavailable() throws Exception {
        MockOciServiceHolder.ociService = null;

        ApiFacadeRequest req = new ApiFacadeRequest();
        req.setBucketName("my-bucket");
        req.setObjectName("file.txt");
        req.setData("data");

        ApiFacadeResponse response = executeAndParse("POST", "/store", req);
        assertEquals(503, response.getStatusCode());
        assertTrue(response.getMessage().contains("OCI services unavailable"));
    }

    // ===== BmcException handling =====

    @Test
    public void testBmcExceptionTimeout() throws Exception {
        when(mockOciService.getSecret(anyString()))
                .thenThrow(new BmcException(true, "Timeout", new SocketTimeoutException("connect timed out"), "opc-1"));

        ApiFacadeRequest req = new ApiFacadeRequest();
        req.setResourceId("ocid1.secret.oc1..test");

        ApiFacadeResponse response = executeAndParse("POST", "/secret", req);
        assertEquals(503, response.getStatusCode());
        assertTrue(response.getMessage().contains("Service temporarily unavailable"));
    }

    @Test
    public void testBmcExceptionServerError500() throws Exception {
        when(mockOciService.getSecret(anyString()))
                .thenThrow(new BmcException(500, "InternalServerError", "Server error", "opc-2"));

        ApiFacadeRequest req = new ApiFacadeRequest();
        req.setResourceId("ocid1.secret.oc1..test");

        ApiFacadeResponse response = executeAndParse("POST", "/secret", req);
        assertEquals(503, response.getStatusCode());
        assertTrue(response.getMessage().contains("Service temporarily unavailable"));
    }

    @Test
    public void testBmcExceptionServerError502() throws Exception {
        when(mockOciService.getSecret(anyString()))
                .thenThrow(new BmcException(502, "BadGateway", "Bad gateway", "opc-3"));

        ApiFacadeRequest req = new ApiFacadeRequest();
        req.setResourceId("ocid1.secret.oc1..test");

        ApiFacadeResponse response = executeAndParse("POST", "/secret", req);
        assertEquals(503, response.getStatusCode());
        assertTrue(response.getMessage().contains("Service temporarily unavailable"));
    }

    @Test
    public void testBmcExceptionTooManyRequests() throws Exception {
        when(mockOciService.getSecret(anyString()))
                .thenThrow(new BmcException(429, "TooManyRequests", "Rate limited", "opc-4"));

        ApiFacadeRequest req = new ApiFacadeRequest();
        req.setResourceId("ocid1.secret.oc1..test");

        ApiFacadeResponse response = executeAndParse("POST", "/secret", req);
        assertEquals(503, response.getStatusCode());
        assertTrue(response.getMessage().contains("Service temporarily unavailable"));
    }

    @Test
    public void testBmcExceptionClientError404() throws Exception {
        when(mockOciService.getSecret(anyString()))
                .thenThrow(new BmcException(404, "NotFound", "Secret not found", "opc-5"));

        ApiFacadeRequest req = new ApiFacadeRequest();
        req.setResourceId("ocid1.secret.oc1..test");

        ApiFacadeResponse response = executeAndParse("POST", "/secret", req);
        assertEquals(404, response.getStatusCode());
        assertTrue(response.getMessage().contains("Secret not found"));
    }

    @Test
    public void testBmcExceptionClientError403() throws Exception {
        when(mockOciService.getSecret(anyString()))
                .thenThrow(new BmcException(403, "NotAuthorized", "Access denied", "opc-6"));

        ApiFacadeRequest req = new ApiFacadeRequest();
        req.setResourceId("ocid1.secret.oc1..test");

        ApiFacadeResponse response = executeAndParse("POST", "/secret", req);
        assertEquals(403, response.getStatusCode());
        assertTrue(response.getMessage().contains("Access denied"));
    }

    @Test
    public void testBmcExceptionClientError401() throws Exception {
        when(mockOciService.getSecret(anyString()))
                .thenThrow(new BmcException(401, "NotAuthenticated", "Not authenticated", "opc-8"));

        ApiFacadeRequest req = new ApiFacadeRequest();
        req.setResourceId("ocid1.secret.oc1..test");

        ApiFacadeResponse response = executeAndParse("POST", "/secret", req);
        assertEquals(401, response.getStatusCode());
        assertTrue(response.getMessage().contains("Not authenticated"));
    }

    // ===== BmcException on /store route =====

    @Test
    public void testStoreRouteBmcExceptionTimeout() throws Exception {
        doThrow(new BmcException(true, "Timeout", new SocketTimeoutException("read timed out"), "opc-7"))
                .when(mockOciService).putObject(anyString(), anyString(), anyString());

        ApiFacadeRequest req = new ApiFacadeRequest();
        req.setBucketName("my-bucket");
        req.setObjectName("file.txt");
        req.setData("data");

        ApiFacadeResponse response = executeAndParse("POST", "/store", req);
        assertEquals(503, response.getStatusCode());
        assertTrue(response.getMessage().contains("Service temporarily unavailable"));
    }

    // ===== General exception handling =====

    @Test
    public void testUnhandledExceptionReturns500() throws Exception {
        when(mockOciService.getSecret(anyString()))
                .thenThrow(new RuntimeException("Unexpected error"));

        ApiFacadeRequest req = new ApiFacadeRequest();
        req.setResourceId("ocid1.secret.oc1..test");

        ApiFacadeResponse response = executeAndParse("POST", "/secret", req);
        assertEquals(500, response.getStatusCode());
        assertTrue(response.getMessage().contains("Internal server error"));
    }

    @Test
    public void testUnhandledExceptionOnStoreReturns500() throws Exception {
        doThrow(new RuntimeException("Disk full"))
                .when(mockOciService).putObject(anyString(), anyString(), anyString());

        ApiFacadeRequest req = new ApiFacadeRequest();
        req.setBucketName("my-bucket");
        req.setObjectName("file.txt");
        req.setData("data");

        ApiFacadeResponse response = executeAndParse("POST", "/store", req);
        assertEquals(500, response.getStatusCode());
        assertTrue(response.getMessage().contains("Internal server error"));
    }

    // ===== IllegalArgumentException handling =====

    @Test
    public void testIllegalArgumentExceptionReturns400() throws Exception {
        when(mockOciService.getSecret(anyString()))
                .thenThrow(new IllegalArgumentException("Invalid OCID format"));

        ApiFacadeRequest req = new ApiFacadeRequest();
        req.setResourceId("bad-id");

        ApiFacadeResponse response = executeAndParse("POST", "/secret", req);
        assertEquals(400, response.getStatusCode());
        assertTrue(response.getMessage().contains("Invalid OCID format"));
    }

    // ===== Additional edge cases =====

    @Test
    public void testSecretRouteReturnsNullSecret() throws Exception {
        when(mockOciService.getSecret(anyString())).thenReturn(null);

        ApiFacadeRequest req = new ApiFacadeRequest();
        req.setResourceId("ocid1.secret.oc1..test");

        ApiFacadeResponse response = executeAndParse("POST", "/secret", req);
        assertEquals(200, response.getStatusCode());
        assertEquals(null, response.getData());
    }

    @Test
    public void testCaseSensitiveRouting() throws Exception {
        ApiFacadeResponse response = executeAndParse("GET", "/Hello", null);
        assertEquals(404, response.getStatusCode());
    }

    @Test
    public void testSecretRouteDeleteMethod() throws Exception {
        ApiFacadeResponse response = executeAndParse("DELETE", "/secret", null);
        assertEquals(405, response.getStatusCode());
    }

    @Test
    public void testStoreRouteDeleteMethod() throws Exception {
        ApiFacadeResponse response = executeAndParse("DELETE", "/store", null);
        assertEquals(405, response.getStatusCode());
    }

    @Test
    public void testStoreRouteWithSpecialCharactersInData() throws Exception {
        ApiFacadeRequest req = new ApiFacadeRequest();
        req.setBucketName("my-bucket");
        req.setObjectName("special.json");
        req.setData("{\"key\": \"value with 'quotes' and \\\"escapes\\\"\", \"unicode\": \"ação\"}");

        ApiFacadeResponse response = executeAndParse("POST", "/store", req);
        assertEquals(200, response.getStatusCode());
        verify(mockOciService).putObject(eq("my-bucket"), eq("special.json"), eq(req.getData()));
    }

    @Test
    public void testStoreRouteWithEmptyStringData() throws Exception {
        ApiFacadeRequest req = new ApiFacadeRequest();
        req.setBucketName("my-bucket");
        req.setObjectName("empty.txt");
        req.setData("");

        ApiFacadeResponse response = executeAndParse("POST", "/store", req);
        assertEquals(200, response.getStatusCode());
        verify(mockOciService).putObject("my-bucket", "empty.txt", "");
    }
}
