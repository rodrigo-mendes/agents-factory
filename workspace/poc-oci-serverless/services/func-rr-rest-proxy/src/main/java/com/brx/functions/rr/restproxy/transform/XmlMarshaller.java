package com.brx.functions.rr.restproxy.transform;

import java.io.StringWriter;

import jakarta.xml.bind.JAXBContext;
import jakarta.xml.bind.Marshaller;

/**
 * Marshals JAXB-annotated domain models to formatted XML using a shared {@link JAXBContext}.
 */
public class XmlMarshaller {

    private final JAXBContext jaxbContext;

    public XmlMarshaller(JAXBContext jaxbContext) {
        this.jaxbContext = jaxbContext;
    }

    public String marshal(Object model) throws Exception {
        Marshaller marshaller = jaxbContext.createMarshaller();
        marshaller.setProperty(Marshaller.JAXB_FORMATTED_OUTPUT, Boolean.TRUE);
        StringWriter writer = new StringWriter();
        marshaller.marshal(model, writer);
        return writer.toString();
    }
}
