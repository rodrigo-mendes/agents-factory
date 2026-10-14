package com.brx.functions.rr.restproxy.client;

import java.io.IOException;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.http.HttpTimeoutException;
import java.util.Map;

import static org.junit.Assert.assertEquals;
import org.junit.Before;
import org.junit.Test;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.fasterxml.jackson.databind.ObjectMapper;

public class RmsClientTest {

    private HttpClient httpClient;
    private ObjectMapper objectMapper;
    private RmsClient rmsClient;

    @Before
    public void setUp() {
        httpClient = mock(HttpClient.class);
        objectMapper = new ObjectMapper();

        rmsClient = new RmsClient(httpClient, objectMapper,
                "https://rms.example.com",
                "https://idcs.example.com/oauth2/v1/token",
                "test:scope",
                "client-id-value",
                "client-secret-value",
                10000L);
    }

    @Test
    @SuppressWarnings("unchecked")
    public void testOAuthTokenSuccess() throws Exception {
        HttpResponse<String> mockResponse = mock(HttpResponse.class);
        String tokenJson = "{\"access_token\":\"abc123\",\"expires_in\":3600,\"token_type\":\"Bearer\"}";
        when(mockResponse.statusCode()).thenReturn(200);
        when(mockResponse.body()).thenReturn(tokenJson);
        when(httpClient.send(any(HttpRequest.class), any(HttpResponse.BodyHandler.class)))
                .thenReturn(mockResponse);

        String token = rmsClient.getAccessToken();

        assertEquals("abc123", token);
    }

    @Test(expected = IOException.class)
    @SuppressWarnings("unchecked")
    public void testOAuthTokenFailure401() throws Exception {
        HttpResponse<String> mockResponse = mock(HttpResponse.class);
        when(mockResponse.statusCode()).thenReturn(401);
        when(mockResponse.body()).thenReturn("Unauthorized");
        when(httpClient.send(any(HttpRequest.class), any(HttpResponse.BodyHandler.class)))
                .thenReturn(mockResponse);

        rmsClient.getAccessToken();
    }

    @Test
    @SuppressWarnings("unchecked")
    public void testOAuthTokenCacheReuse() throws Exception {
        HttpResponse<String> mockResponse = mock(HttpResponse.class);
        String tokenJson = "{\"access_token\":\"cached-token\",\"expires_in\":3600,\"token_type\":\"Bearer\"}";
        when(mockResponse.statusCode()).thenReturn(200);
        when(mockResponse.body()).thenReturn(tokenJson);
        when(httpClient.send(any(HttpRequest.class), any(HttpResponse.BodyHandler.class)))
                .thenReturn(mockResponse);

        // First call — acquires token
        String token1 = rmsClient.getAccessToken();
        // Second call — should reuse cached token
        String token2 = rmsClient.getAccessToken();

        assertEquals("cached-token", token1);
        assertEquals("cached-token", token2);
        // httpClient.send should be called only once (token acquisition)
        verify(httpClient, times(1)).send(any(HttpRequest.class), any(HttpResponse.BodyHandler.class));
    }

    @Test
    @SuppressWarnings("unchecked")
    public void testOAuthTokenRenewalAfterExpiry() throws Exception {
        HttpResponse<String> mockResponse = mock(HttpResponse.class);
        when(mockResponse.statusCode()).thenReturn(200);
        when(mockResponse.body())
                .thenReturn("{\"access_token\":\"token-1\",\"expires_in\":1,\"token_type\":\"Bearer\"}")
                .thenReturn("{\"access_token\":\"token-2\",\"expires_in\":3600,\"token_type\":\"Bearer\"}");
        when(httpClient.send(any(HttpRequest.class), any(HttpResponse.BodyHandler.class)))
                .thenReturn(mockResponse);

        // First call
        String token1 = rmsClient.getAccessToken();
        assertEquals("token-1", token1);

        // Invalidate token (simulates expiry)
        rmsClient.invalidateToken();

        // Second call should acquire new token
        String token2 = rmsClient.getAccessToken();
        assertEquals("token-2", token2);

        verify(httpClient, times(2)).send(any(HttpRequest.class), any(HttpResponse.BodyHandler.class));
    }

    @Test
    @SuppressWarnings("unchecked")
    public void testGetStoreDetailSuccess() throws Exception {
        // First call: OAuth2 token
        HttpResponse<String> tokenResponse = mock(HttpResponse.class);
        when(tokenResponse.statusCode()).thenReturn(200);
        when(tokenResponse.body()).thenReturn(
                "{\"access_token\":\"test-token\",\"expires_in\":3600,\"token_type\":\"Bearer\"}");

        // Second call: Store detail
        HttpResponse<String> storeResponse = mock(HttpResponse.class);
        when(storeResponse.statusCode()).thenReturn(200);
        when(storeResponse.body()).thenReturn("{\"store\":1234,\"storeName\":\"Test Store\"}");

        when(httpClient.send(any(HttpRequest.class), any(HttpResponse.BodyHandler.class)))
                .thenReturn(tokenResponse, storeResponse);

        Map<String, Object> result = rmsClient.getStoreDetail("1234");

        assertEquals(1234, result.get("store"));
        assertEquals("Test Store", result.get("storeName"));
    }

    @Test(expected = HttpTimeoutException.class)
    @SuppressWarnings("unchecked")
    public void testGetStoreDetailTimeout() throws Exception {
        // Token call succeeds
        HttpResponse<String> tokenResponse = mock(HttpResponse.class);
        when(tokenResponse.statusCode()).thenReturn(200);
        when(tokenResponse.body()).thenReturn(
                "{\"access_token\":\"test-token\",\"expires_in\":3600,\"token_type\":\"Bearer\"}");

        when(httpClient.send(any(HttpRequest.class), any(HttpResponse.BodyHandler.class)))
                .thenReturn(tokenResponse)
                .thenThrow(new HttpTimeoutException("timeout"))
                .thenThrow(new HttpTimeoutException("timeout"))
                .thenThrow(new HttpTimeoutException("timeout"));

        rmsClient.getStoreDetail("1234");
    }

    @Test
    @SuppressWarnings("unchecked")
    public void testGetStoreDetailRetryOn5xx() throws Exception {
        // Token call succeeds
        HttpResponse<String> tokenResponse = mock(HttpResponse.class);
        when(tokenResponse.statusCode()).thenReturn(200);
        when(tokenResponse.body()).thenReturn(
                "{\"access_token\":\"test-token\",\"expires_in\":3600,\"token_type\":\"Bearer\"}");

        // First store call: 500, second: 200
        HttpResponse<String> errorResponse = mock(HttpResponse.class);
        when(errorResponse.statusCode()).thenReturn(500);
        when(errorResponse.body()).thenReturn("Internal Server Error");

        HttpResponse<String> successResponse = mock(HttpResponse.class);
        when(successResponse.statusCode()).thenReturn(200);
        when(successResponse.body()).thenReturn("{\"store\":1234}");

        when(httpClient.send(any(HttpRequest.class), any(HttpResponse.BodyHandler.class)))
                .thenReturn(tokenResponse, errorResponse, successResponse);

        Map<String, Object> result = rmsClient.getStoreDetail("1234");

        assertEquals(1234, result.get("store"));
        verify(httpClient, times(3)).send(any(HttpRequest.class), any(HttpResponse.BodyHandler.class));
    }

    @Test(expected = IOException.class)
    @SuppressWarnings("unchecked")
    public void testOAuthTokenNetworkUnreachable() throws Exception {
        when(httpClient.send(any(HttpRequest.class), any(HttpResponse.BodyHandler.class)))
                .thenThrow(new IOException("Network is unreachable"));

        rmsClient.getAccessToken();
    }

    @Test
    @SuppressWarnings("unchecked")
    public void testOAuthTokenResponseMissingFields() throws Exception {
        HttpResponse<String> mockResponse = mock(HttpResponse.class);
        // Response missing expires_in — should still extract access_token
        String tokenJson = "{\"access_token\":\"token-no-expiry\",\"token_type\":\"Bearer\"}";
        when(mockResponse.statusCode()).thenReturn(200);
        when(mockResponse.body()).thenReturn(tokenJson);
        when(httpClient.send(any(HttpRequest.class), any(HttpResponse.BodyHandler.class)))
                .thenReturn(mockResponse);

        String token = rmsClient.getAccessToken();

        assertEquals("token-no-expiry", token);
    }
}
