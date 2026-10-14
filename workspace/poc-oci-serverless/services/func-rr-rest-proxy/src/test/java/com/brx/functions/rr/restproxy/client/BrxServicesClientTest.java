package com.brx.functions.rr.restproxy.client;

import java.io.IOException;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.http.HttpTimeoutException;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNull;
import org.junit.Before;
import org.junit.Test;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

public class BrxServicesClientTest {

    private HttpClient httpClient;
    private BrxServicesClient client;

    @Before
    public void setUp() {
        httpClient = mock(HttpClient.class);
        client = new BrxServicesClient(httpClient,
                "http://brxservices.example.com/ords/brxoper/BrxServices/Store",
                10000L);
    }

    @Test
    @SuppressWarnings("unchecked")
    public void testSendPostSuccess() throws Exception {
        HttpResponse<String> mockResponse = mock(HttpResponse.class);
        when(mockResponse.statusCode()).thenReturn(200);
        when(mockResponse.body()).thenReturn("<response>ok</response>");
        when(httpClient.send(any(HttpRequest.class), any(HttpResponse.BodyHandler.class)))
                .thenReturn(mockResponse);

        String result = client.send("<StoreDesc/>", "POST");

        assertEquals("<response>ok</response>", result);
        verify(httpClient, times(1)).send(any(HttpRequest.class), any(HttpResponse.BodyHandler.class));
    }

    @Test
    @SuppressWarnings("unchecked")
    public void testSendPutSuccess() throws Exception {
        HttpResponse<String> mockResponse = mock(HttpResponse.class);
        when(mockResponse.statusCode()).thenReturn(200);
        when(mockResponse.body()).thenReturn("<response>updated</response>");
        when(httpClient.send(any(HttpRequest.class), any(HttpResponse.BodyHandler.class)))
                .thenReturn(mockResponse);

        String result = client.send("<StoreDesc/>", "PUT");

        assertEquals("<response>updated</response>", result);
    }

    @Test(expected = HttpTimeoutException.class)
    @SuppressWarnings("unchecked")
    public void testSendTimeout() throws Exception {
        when(httpClient.send(any(HttpRequest.class), any(HttpResponse.BodyHandler.class)))
                .thenThrow(new HttpTimeoutException("timeout"))
                .thenThrow(new HttpTimeoutException("timeout"))
                .thenThrow(new HttpTimeoutException("timeout"));

        client.send("<StoreDesc/>", "POST");
    }

    @Test(expected = IOException.class)
    @SuppressWarnings("unchecked")
    public void testSend5xxAfterRetries() throws Exception {
        HttpResponse<String> mockResponse = mock(HttpResponse.class);
        when(mockResponse.statusCode()).thenReturn(500);
        when(mockResponse.body()).thenReturn("Internal Server Error");
        when(httpClient.send(any(HttpRequest.class), any(HttpResponse.BodyHandler.class)))
                .thenReturn(mockResponse);

        client.send("<StoreDesc/>", "POST");
    }

    @Test
    @SuppressWarnings("unchecked")
    public void testSendRetryOn5xxThenSuccess() throws Exception {
        HttpResponse<String> errorResponse = mock(HttpResponse.class);
        when(errorResponse.statusCode()).thenReturn(500);
        when(errorResponse.body()).thenReturn("Error");

        HttpResponse<String> successResponse = mock(HttpResponse.class);
        when(successResponse.statusCode()).thenReturn(200);
        when(successResponse.body()).thenReturn("<ok/>");

        when(httpClient.send(any(HttpRequest.class), any(HttpResponse.BodyHandler.class)))
                .thenReturn(errorResponse, successResponse);

        String result = client.send("<StoreDesc/>", "POST");

        assertEquals("<ok/>", result);
        verify(httpClient, times(2)).send(any(HttpRequest.class), any(HttpResponse.BodyHandler.class));
    }

    @Test
    @SuppressWarnings("unchecked")
    public void testSendEmptyResponseBody() throws Exception {
        HttpResponse<String> mockResponse = mock(HttpResponse.class);
        when(mockResponse.statusCode()).thenReturn(200);
        when(mockResponse.body()).thenReturn("");
        when(httpClient.send(any(HttpRequest.class), any(HttpResponse.BodyHandler.class)))
                .thenReturn(mockResponse);

        String result = client.send("<StoreDesc/>", "POST");

        assertEquals("", result);
    }

    @Test
    @SuppressWarnings("unchecked")
    public void testSendNullResponseBody() throws Exception {
        HttpResponse<String> mockResponse = mock(HttpResponse.class);
        when(mockResponse.statusCode()).thenReturn(200);
        when(mockResponse.body()).thenReturn(null);
        when(httpClient.send(any(HttpRequest.class), any(HttpResponse.BodyHandler.class)))
                .thenReturn(mockResponse);

        String result = client.send("<StoreDesc/>", "POST");

        assertNull(result);
    }
}
