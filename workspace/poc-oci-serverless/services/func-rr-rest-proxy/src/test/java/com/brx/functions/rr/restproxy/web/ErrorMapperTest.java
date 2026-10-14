package com.brx.functions.rr.restproxy.web;

import java.io.IOException;
import java.net.http.HttpTimeoutException;

import static org.junit.Assert.assertEquals;
import org.junit.Before;
import org.junit.Test;

import com.brx.functions.rr.restproxy.model.StoreResponse;
import com.fnproject.events.output.APIGatewayResponseEvent;

public class ErrorMapperTest {

    private ErrorMapper errorMapper;

    @Before
    public void setUp() {
        errorMapper = new ErrorMapper(new ResponseFactory());
    }

    @Test
    public void testTimeoutMapsTo504() {
        APIGatewayResponseEvent<StoreResponse> r =
                errorMapper.toResponse(new HttpTimeoutException("RMS timeout"));
        assertEquals(Integer.valueOf(504), r.getStatus());
        assertEquals("Gateway Timeout", r.getBody().getErro());
    }

    @Test
    public void testOAuthFailureMapsTo503() {
        APIGatewayResponseEvent<StoreResponse> r =
                errorMapper.toResponse(new IOException("OAuth2 token request failed with status: 401"));
        assertEquals(Integer.valueOf(503), r.getStatus());
        assertEquals("Service Unavailable", r.getBody().getErro());
    }

    @Test
    public void testHttp4xxMapsToBadRequest() {
        APIGatewayResponseEvent<StoreResponse> r = errorMapper.toResponse(
                new IOException("Falha na chamada HTTP: 400 - {\"message\":\"Invalid Store. 1234\"}"));
        assertEquals(Integer.valueOf(400), r.getStatus());
        assertEquals("Bad Request", r.getBody().getErro());
        assertEquals("Falha na chamada HTTP: 400 - {\"message\":\"Invalid Store. 1234\"}", r.getBody().getDetalhe());
    }

    @Test
    public void testHttp5xxMapsToBadGateway() {
        APIGatewayResponseEvent<StoreResponse> r = errorMapper.toResponse(
                new IOException("Falha na chamada HTTP: 500 - {\"message\":\"RMS unavailable\"}"));
        assertEquals(Integer.valueOf(502), r.getStatus());
        assertEquals("Bad Gateway", r.getBody().getErro());
    }

    @Test
    public void testBrxServicesErrorMapsToBadGateway() {
        APIGatewayResponseEvent<StoreResponse> r =
                errorMapper.toResponse(new IOException("BrxServices HTTP error: 500"));
        assertEquals(Integer.valueOf(502), r.getStatus());
        assertEquals("Bad Gateway", r.getBody().getErro());
    }

    @Test
    public void testGenericIoExceptionMapsTo500() {
        APIGatewayResponseEvent<StoreResponse> r =
                errorMapper.toResponse(new IOException("Connection reset"));
        assertEquals(Integer.valueOf(500), r.getStatus());
        assertEquals("Internal server error", r.getBody().getErro());
    }

    @Test
    public void testUnexpectedExceptionMapsTo500() {
        APIGatewayResponseEvent<StoreResponse> r =
                errorMapper.toResponse(new RuntimeException("Unexpected null pointer"));
        assertEquals(Integer.valueOf(500), r.getStatus());
        assertEquals("Internal server error", r.getBody().getErro());
    }
}
