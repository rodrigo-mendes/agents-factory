package com.brx.functions.rr.restproxy.transform;

import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.Map;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.brx.functions.rr.restproxy.model.StoreDescModel;

/**
 * Maps a raw RMS store-detail JSON map to the {@link StoreDescModel} XML model, applying the
 * field-name translation and lenient date parsing rules of the integration contract.
 */
public class StoreMapper {

    private static final Logger log = LoggerFactory.getLogger(StoreMapper.class);
    private static final String DATE_PATTERN = "yyyy-MM-dd";

    public StoreDescModel map(Map<String, Object> rmsData) {
        StoreDescModel model = new StoreDescModel();

        model.setStore(getInteger(rmsData, "store"));
        model.setStoreType(getString(rmsData, "storeType"));
        model.setStoreName(getString(rmsData, "storeName"));
        model.setStoreName10(getString(rmsData, "storeName10"));
        model.setStoreName3(getString(rmsData, "storeName3"));
        model.setStoreAdd1(getString(rmsData, "add1"));
        model.setStoreAdd2(getString(rmsData, "add2"));
        model.setStoreCity(getString(rmsData, "city"));
        model.setState(getString(rmsData, "state"));
        model.setCountryId(getString(rmsData, "countryId"));
        model.setStorePcode(getString(rmsData, "post"));
        model.setStoreClass(getString(rmsData, "storeClass"));
        model.setStoreMgrName(String.valueOf(getInteger(rmsData, "store")));
        model.setPhoneNumber(getString(rmsData, "contactPhone"));
        model.setStockholdingInd(getString(rmsData, "stockholdingInd"));
        model.setChannelId(getInteger(rmsData, "channelId"));
        model.setDistrict(getInteger(rmsData, "district"));
        model.setTransferZone(getInteger(rmsData, "transferZone"));
        model.setDefaultWh(getInteger(rmsData, "defaultWh"));
        model.setStartOrderDays(getInteger(rmsData, "startOrderDays"));
        model.setCurrencyCode(getString(rmsData, "currencyCode"));
        model.setLang(getInteger(rmsData, "lang"));
        model.setTimezoneName(getString(rmsData, "timezoneName"));
        model.setOrigCurrencyCode(getString(rmsData, "currencyCode"));

        String dateStr = getString(rmsData, "storeOpenDate");
        if (dateStr != null && !dateStr.isEmpty()) {
            try {
                SimpleDateFormat sdf = new SimpleDateFormat(DATE_PATTERN);
                sdf.setLenient(false);
                model.setStoreOpenDate(sdf.parse(dateStr));
            } catch (ParseException e) {
                log.warn("Failed to parse storeOpenDate: {}", dateStr);
            }
        }

        return model;
    }

    private String getString(Map<String, Object> map, String key) {
        Object value = map.get(key);
        return value != null ? String.valueOf(value) : null;
    }

    private Integer getInteger(Map<String, Object> map, String key) {
        Object value = map.get(key);
        if (value == null) return null;
        if (value instanceof Number) return ((Number) value).intValue();
        try {
            return Integer.parseInt(String.valueOf(value));
        } catch (NumberFormatException e) {
            return null;
        }
    }
}
