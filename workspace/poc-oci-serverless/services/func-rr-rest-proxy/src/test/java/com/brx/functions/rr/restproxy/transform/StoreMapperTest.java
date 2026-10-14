package com.brx.functions.rr.restproxy.transform;

import java.util.HashMap;
import java.util.Map;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertNull;
import org.junit.Before;
import org.junit.Test;

import com.brx.functions.rr.restproxy.model.StoreDescModel;

public class StoreMapperTest {

    private StoreMapper mapper;

    @Before
    public void setUp() {
        mapper = new StoreMapper();
    }

    @Test
    public void testMapFields() {
        StoreDescModel model = mapper.map(sampleRmsData());

        assertEquals(Integer.valueOf(1234), model.getStore());
        assertEquals("W", model.getStoreType());
        assertEquals("Loja Centro SP", model.getStoreName());
        assertEquals("Centro SP", model.getStoreName10());
        assertEquals("CSP", model.getStoreName3());
        assertEquals("Rua Principal 100", model.getStoreAdd1());
        assertEquals("Andar 2", model.getStoreAdd2());
        assertEquals("Sao Paulo", model.getStoreCity());
        assertEquals("SP", model.getState());
        assertEquals("BR", model.getCountryId());
        assertEquals("01001-000", model.getStorePcode());
        assertEquals("A", model.getStoreClass());
        assertEquals("1234", model.getStoreMgrName());
        assertEquals("11999999999", model.getPhoneNumber());
        assertEquals("Y", model.getStockholdingInd());
        assertEquals(Integer.valueOf(1), model.getChannelId());
        assertEquals(Integer.valueOf(10), model.getDistrict());
        assertEquals(Integer.valueOf(5), model.getTransferZone());
        assertEquals(Integer.valueOf(100), model.getDefaultWh());
        assertEquals(Integer.valueOf(3), model.getStartOrderDays());
        assertEquals("BRL", model.getCurrencyCode());
        assertEquals(Integer.valueOf(12), model.getLang());
        assertEquals("America/Sao_Paulo", model.getTimezoneName());
        assertEquals("BRL", model.getOrigCurrencyCode());
        assertNotNull(model.getStoreOpenDate());
    }

    @Test
    public void testMapNullFields() {
        Map<String, Object> rmsData = new HashMap<>();
        rmsData.put("store", 1234);

        StoreDescModel model = mapper.map(rmsData);

        assertEquals(Integer.valueOf(1234), model.getStore());
        assertNull(model.getStoreType());
        assertNull(model.getStoreName());
        assertNull(model.getStoreCity());
        assertNull(model.getStoreOpenDate());
    }

    @Test
    public void testMapInvalidDate() {
        Map<String, Object> rmsData = sampleRmsData();
        rmsData.put("storeOpenDate", "2023-13-45"); // invalid date

        StoreDescModel model = mapper.map(rmsData);

        // Invalid date is silently ignored (logged as warning)
        assertNull(model.getStoreOpenDate());
    }

    @Test
    public void testMapEmptyDate() {
        Map<String, Object> rmsData = sampleRmsData();
        rmsData.put("storeOpenDate", "");

        StoreDescModel model = mapper.map(rmsData);

        assertNull(model.getStoreOpenDate());
    }

    private Map<String, Object> sampleRmsData() {
        Map<String, Object> data = new HashMap<>();
        data.put("store", 1234);
        data.put("storeType", "W");
        data.put("storeName", "Loja Centro SP");
        data.put("storeName10", "Centro SP");
        data.put("storeName3", "CSP");
        data.put("add1", "Rua Principal 100");
        data.put("add2", "Andar 2");
        data.put("city", "Sao Paulo");
        data.put("state", "SP");
        data.put("countryId", "BR");
        data.put("post", "01001-000");
        data.put("storeClass", "A");
        data.put("storeOpenDate", "2023-06-15");
        data.put("contactPhone", "11999999999");
        data.put("stockholdingInd", "Y");
        data.put("channelId", 1);
        data.put("district", 10);
        data.put("transferZone", 5);
        data.put("defaultWh", 100);
        data.put("startOrderDays", 3);
        data.put("currencyCode", "BRL");
        data.put("lang", 12);
        data.put("timezoneName", "America/Sao_Paulo");
        return data;
    }
}
