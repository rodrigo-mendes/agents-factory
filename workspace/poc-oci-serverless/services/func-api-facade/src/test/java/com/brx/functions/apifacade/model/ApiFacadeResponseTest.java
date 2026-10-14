package com.brx.functions.apifacade.model;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNull;
import org.junit.Test;

public class ApiFacadeResponseTest {

    @Test
    public void testDefaultConstructor() {
        ApiFacadeResponse resp = new ApiFacadeResponse();
        assertEquals(0, resp.getStatusCode());
        assertNull(resp.getMessage());
        assertNull(resp.getData());
    }

    @Test
    public void testParameterizedConstructor() {
        ApiFacadeResponse resp = new ApiFacadeResponse(201, "Created", "result-data");
        assertEquals(201, resp.getStatusCode());
        assertEquals("Created", resp.getMessage());
        assertEquals("result-data", resp.getData());
    }

    @Test
    public void testOkWithMessageOnly() {
        ApiFacadeResponse resp = ApiFacadeResponse.ok("Success");
        assertEquals(200, resp.getStatusCode());
        assertEquals("Success", resp.getMessage());
        assertNull(resp.getData());
    }

    @Test
    public void testOkWithMessageAndData() {
        ApiFacadeResponse resp = ApiFacadeResponse.ok("Done", "secret-value");
        assertEquals(200, resp.getStatusCode());
        assertEquals("Done", resp.getMessage());
        assertEquals("secret-value", resp.getData());
    }

    @Test
    public void testError() {
        ApiFacadeResponse resp = ApiFacadeResponse.error(404, "Not found");
        assertEquals(404, resp.getStatusCode());
        assertEquals("Not found", resp.getMessage());
        assertNull(resp.getData());
    }

    @Test
    public void testSetters() {
        ApiFacadeResponse resp = new ApiFacadeResponse();
        resp.setStatusCode(500);
        resp.setMessage("Error");
        resp.setData("detail");
        resp.setElapsedMs(120);
        resp.setColdStart(true);
        resp.setApiVersion("1.0.0");

        assertEquals(500, resp.getStatusCode());
        assertEquals("Error", resp.getMessage());
        assertEquals("detail", resp.getData());
        assertEquals(120, resp.getElapsedMs());
        assertTrue(resp.isColdStart());
        assertEquals("1.0.0", resp.getApiVersion());
    }

    private void assertTrue(boolean val) {
        org.junit.Assert.assertTrue(val);
    }
}
