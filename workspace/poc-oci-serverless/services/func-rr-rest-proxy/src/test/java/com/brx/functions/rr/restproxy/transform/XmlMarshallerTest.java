package com.brx.functions.rr.restproxy.transform;

import static org.junit.Assert.assertTrue;
import org.junit.Before;
import org.junit.Test;

import com.brx.functions.rr.restproxy.model.ItemDescModel;
import com.brx.functions.rr.restproxy.model.StoreDescModel;

import jakarta.xml.bind.JAXBContext;

public class XmlMarshallerTest {

    private XmlMarshaller marshaller;

    @Before
    public void setUp() throws Exception {
        JAXBContext jaxbContext = JAXBContext.newInstance(StoreDescModel.class, ItemDescModel.class);
        marshaller = new XmlMarshaller(jaxbContext);
    }

    @Test
    public void testMarshalStore() throws Exception {
        StoreDescModel model = new StoreDescModel();
        model.setStore(1234);
        model.setStoreName("Loja Centro SP");

        String xml = marshaller.marshal(model);

        assertTrue(xml.contains("<StoreDesc>"));
        assertTrue(xml.contains("Loja Centro SP"));
    }

    @Test
    public void testMarshalItem() throws Exception {
        ItemDescModel model = new ItemDescModel("itemA", "Test Item A", "A", "insert");

        String xml = marshaller.marshal(model);

        assertTrue(xml.contains("<ItemDesc>"));
        assertTrue(xml.contains("itemA"));
    }
}
