package com.brx.functions.apifacade.model;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNull;
import org.junit.Test;

public class ApiFacadeRequestTest {

    @Test
    public void testDefaultConstructor() {
        ApiFacadeRequest req = new ApiFacadeRequest();
        assertNull(req.getResourceId());
        assertNull(req.getBucketName());
        assertNull(req.getObjectName());
        assertNull(req.getData());
    }

    @Test
    public void testResourceIdGetterSetter() {
        ApiFacadeRequest req = new ApiFacadeRequest();
        req.setResourceId("ocid1.secret.oc1..abc");
        assertEquals("ocid1.secret.oc1..abc", req.getResourceId());
    }

    @Test
    public void testBucketNameGetterSetter() {
        ApiFacadeRequest req = new ApiFacadeRequest();
        req.setBucketName("my-bucket");
        assertEquals("my-bucket", req.getBucketName());
    }

    @Test
    public void testObjectNameGetterSetter() {
        ApiFacadeRequest req = new ApiFacadeRequest();
        req.setObjectName("data.json");
        assertEquals("data.json", req.getObjectName());
    }

    @Test
    public void testDataGetterSetter() {
        ApiFacadeRequest req = new ApiFacadeRequest();
        req.setData("payload content");
        assertEquals("payload content", req.getData());
    }
}
