package com.brx.functions.rr.restproxy.model;

import java.util.Date;

import jakarta.xml.bind.annotation.XmlAccessType;
import jakarta.xml.bind.annotation.XmlAccessorType;
import jakarta.xml.bind.annotation.XmlElement;
import jakarta.xml.bind.annotation.XmlRootElement;

@XmlRootElement(name = "StoreDesc")
@XmlAccessorType(XmlAccessType.FIELD)
public class StoreDescModel {

    @XmlElement
    private Integer store;

    @XmlElement
    private String storeType;

    @XmlElement
    private String storeName;

    @XmlElement
    private String storeName10;

    @XmlElement
    private String storeName3;

    @XmlElement
    private String storeAdd1;

    @XmlElement
    private String storeAdd2;

    @XmlElement
    private String storeCity;

    @XmlElement
    private String state;

    @XmlElement
    private String countryId;

    @XmlElement
    private String storePcode;

    @XmlElement
    private String storeClass;

    @XmlElement
    private String storeMgrName;

    @XmlElement
    private Date storeOpenDate;

    @XmlElement
    private String phoneNumber;

    @XmlElement
    private String stockholdingInd;

    @XmlElement
    private Integer channelId;

    @XmlElement
    private Integer district;

    @XmlElement
    private Integer transferZone;

    @XmlElement
    private Integer defaultWh;

    @XmlElement
    private Integer startOrderDays;

    @XmlElement
    private String currencyCode;

    @XmlElement
    private Integer lang;

    @XmlElement
    private String timezoneName;

    @XmlElement
    private String origCurrencyCode;

    public Integer getStore() {
        return store;
    }

    public void setStore(Integer store) {
        this.store = store;
    }

    public String getStoreType() {
        return storeType;
    }

    public void setStoreType(String storeType) {
        this.storeType = storeType;
    }

    public String getStoreName() {
        return storeName;
    }

    public void setStoreName(String storeName) {
        this.storeName = storeName;
    }

    public String getStoreName10() {
        return storeName10;
    }

    public void setStoreName10(String storeName10) {
        this.storeName10 = storeName10;
    }

    public String getStoreName3() {
        return storeName3;
    }

    public void setStoreName3(String storeName3) {
        this.storeName3 = storeName3;
    }

    public String getStoreAdd1() {
        return storeAdd1;
    }

    public void setStoreAdd1(String storeAdd1) {
        this.storeAdd1 = storeAdd1;
    }

    public String getStoreAdd2() {
        return storeAdd2;
    }

    public void setStoreAdd2(String storeAdd2) {
        this.storeAdd2 = storeAdd2;
    }

    public String getStoreCity() {
        return storeCity;
    }

    public void setStoreCity(String storeCity) {
        this.storeCity = storeCity;
    }

    public String getState() {
        return state;
    }

    public void setState(String state) {
        this.state = state;
    }

    public String getCountryId() {
        return countryId;
    }

    public void setCountryId(String countryId) {
        this.countryId = countryId;
    }

    public String getStorePcode() {
        return storePcode;
    }

    public void setStorePcode(String storePcode) {
        this.storePcode = storePcode;
    }

    public String getStoreClass() {
        return storeClass;
    }

    public void setStoreClass(String storeClass) {
        this.storeClass = storeClass;
    }

    public String getStoreMgrName() {
        return storeMgrName;
    }

    public void setStoreMgrName(String storeMgrName) {
        this.storeMgrName = storeMgrName;
    }

    public Date getStoreOpenDate() {
        return storeOpenDate;
    }

    public void setStoreOpenDate(Date storeOpenDate) {
        this.storeOpenDate = storeOpenDate;
    }

    public String getPhoneNumber() {
        return phoneNumber;
    }

    public void setPhoneNumber(String phoneNumber) {
        this.phoneNumber = phoneNumber;
    }

    public String getStockholdingInd() {
        return stockholdingInd;
    }

    public void setStockholdingInd(String stockholdingInd) {
        this.stockholdingInd = stockholdingInd;
    }

    public Integer getChannelId() {
        return channelId;
    }

    public void setChannelId(Integer channelId) {
        this.channelId = channelId;
    }

    public Integer getDistrict() {
        return district;
    }

    public void setDistrict(Integer district) {
        this.district = district;
    }

    public Integer getTransferZone() {
        return transferZone;
    }

    public void setTransferZone(Integer transferZone) {
        this.transferZone = transferZone;
    }

    public Integer getDefaultWh() {
        return defaultWh;
    }

    public void setDefaultWh(Integer defaultWh) {
        this.defaultWh = defaultWh;
    }

    public Integer getStartOrderDays() {
        return startOrderDays;
    }

    public void setStartOrderDays(Integer startOrderDays) {
        this.startOrderDays = startOrderDays;
    }

    public String getCurrencyCode() {
        return currencyCode;
    }

    public void setCurrencyCode(String currencyCode) {
        this.currencyCode = currencyCode;
    }

    public Integer getLang() {
        return lang;
    }

    public void setLang(Integer lang) {
        this.lang = lang;
    }

    public String getTimezoneName() {
        return timezoneName;
    }

    public void setTimezoneName(String timezoneName) {
        this.timezoneName = timezoneName;
    }

    public String getOrigCurrencyCode() {
        return origCurrencyCode;
    }

    public void setOrigCurrencyCode(String origCurrencyCode) {
        this.origCurrencyCode = origCurrencyCode;
    }
}
