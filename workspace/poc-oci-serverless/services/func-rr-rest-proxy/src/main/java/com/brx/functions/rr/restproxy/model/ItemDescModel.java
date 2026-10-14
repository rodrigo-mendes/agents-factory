package com.brx.functions.rr.restproxy.model;

import jakarta.xml.bind.annotation.XmlAccessType;
import jakarta.xml.bind.annotation.XmlAccessorType;
import jakarta.xml.bind.annotation.XmlElement;
import jakarta.xml.bind.annotation.XmlRootElement;

@XmlRootElement(name = "ItemDesc")
@XmlAccessorType(XmlAccessType.FIELD)
public class ItemDescModel {

    @XmlElement
    private String item;

    @XmlElement
    private String itemDescription;

    @XmlElement
    private String status;

    @XmlElement
    private String action;

    public ItemDescModel() {
    }

    public ItemDescModel(String item, String itemDescription, String status, String action) {
        this.item = item;
        this.itemDescription = itemDescription;
        this.status = status;
        this.action = action;
    }

    public String getItem() {
        return item;
    }

    public void setItem(String item) {
        this.item = item;
    }

    public String getItemDescription() {
        return itemDescription;
    }

    public void setItemDescription(String itemDescription) {
        this.itemDescription = itemDescription;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public String getAction() {
        return action;
    }

    public void setAction(String action) {
        this.action = action;
    }
}