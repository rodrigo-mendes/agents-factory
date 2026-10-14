package com.brx.functions.rr.restproxy.client.http;

import java.io.IOException;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.http.HttpTimeoutException;

import static org.junit.Assert.assertEquals;
import org.junit.Before;
import org.junit.Test;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

public class HttpRetryExecutorTest {

    private HttpClient httpClient;
    private HttpRetryExecutor executor;
    private HttpRetryExecutor.ResponseHandler<String> bodyHandler;

    @Before
    public void setUp() {
        httpClient = mock(HttpClient.class);
        executor = new HttpRetryExecutor(httpClient, "TestSvc");
        bodyHandler = new HttpRetryExecutor.ResponseHandler<>() {
            @Override
            public String onSuccess(HttpResponse<String> response) {
                return response.body();
            }

            @Override
            public IOException onFailure(HttpResponse<String> response) {
                return new IOException("TestSvc HTTP error: " + response.statusCode());
            }
        };
    }

    private HttpRequest anyRequest() {
        return HttpRequest.newBuilder().uri(java.net.URI.create("http://example.com")).GET().build();
    }

    @Test
    @SuppressWarnings("unchecked")
    public void testSuccessNoRetry() throws Exception {
        HttpResponse<String> ok = mock(HttpResponse.class);
        when(ok.statusCode()).thenReturn(200);
        when(ok.body()).thenReturn("<ok/>");
        when(httpClient.send(any(HttpRequest.class), any(HttpResponse.BodyHandler.class))).thenReturn(ok);

        assertEquals("<ok/>", executor.execute(anyRequest(), bodyHandler));
        verify(httpClient, times(1)).send(any(HttpRequest.class), any(HttpResponse.BodyHandler.class));
    }

    @Test
    @SuppressWarnings("unchecked")
    public void testRetryOn5xxThenSuccess() throws Exception {
        HttpResponse<String> err = mock(HttpResponse.class);
        when(err.statusCode()).thenReturn(500);
        HttpResponse<String> ok = mock(HttpResponse.class);
        when(ok.statusCode()).thenReturn(200);
        when(ok.body()).thenReturn("<ok/>");
        when(httpClient.send(any(HttpRequest.class), any(HttpResponse.BodyHandler.class)))
                .thenReturn(err, ok);

        assertEquals("<ok/>", executor.execute(anyRequest(), bodyHandler));
        verify(httpClient, times(2)).send(any(HttpRequest.class), any(HttpResponse.BodyHandler.class));
    }

    @Test(expected = IOException.class)
    @SuppressWarnings("unchecked")
    public void test5xxAfterRetriesThrows() throws Exception {
        HttpResponse<String> err = mock(HttpResponse.class);
        when(err.statusCode()).thenReturn(500);
        when(httpClient.send(any(HttpRequest.class), any(HttpResponse.BodyHandler.class))).thenReturn(err);

        executor.execute(anyRequest(), bodyHandler);
    }

    @Test(expected = HttpTimeoutException.class)
    @SuppressWarnings("unchecked")
    public void testTimeoutAfterRetriesThrows() throws Exception {
        when(httpClient.send(any(HttpRequest.class), any(HttpResponse.BodyHandler.class)))
                .thenThrow(new HttpTimeoutException("timeout"));

        executor.execute(anyRequest(), bodyHandler);
    }
}
