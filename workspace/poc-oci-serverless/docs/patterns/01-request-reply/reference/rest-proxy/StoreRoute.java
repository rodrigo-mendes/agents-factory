package br.com.natal.ia.integration.routes;

import br.com.natal.ia.model.StoreDescModel;
import jakarta.enterprise.context.ApplicationScoped;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.Date;
import org.apache.camel.Exchange;
import org.apache.camel.builder.RouteBuilder;
import org.apache.camel.converter.jaxb.JaxbDataFormat;
import org.apache.camel.http.base.HttpOperationFailedException;
import org.eclipse.microprofile.config.inject.ConfigProperty;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Integration: Store creation and update via Oracle RMS → BrxServices.
 *
 * Flow:
 *   POST /api/store/create?store={id}  → OAuth2 → GET storeDetail → Transform → POST destination (XML)
 *   POST /api/store/update?store={id}  → OAuth2 → GET storeDetail → Transform → PUT  destination (XML)
 *
 * Skills dynamically loaded based on requirements:
 * - camel-quarkus-core-v3.15:          RouteBuilder, CDI integration
 * - camel-quarkus-rest-v3.15:          REST DSL trigger endpoints
 * - camel-quarkus-platform-http-v3.15: HTTP transport
 * - camel-quarkus-http-v3.15:          HTTP client (OAuth2, source API, destination API)
 * - camel-quarkus-jaxb-v3.15:          XML marshalling (StoreDesc)
 * - camel-quarkus-jackson-v3.15:       JSON unmarshalling (StoreResult)
 * - camel-quarkus-log-v3.15:           Structured logging
 *
 * @see .github/skills/camel-quarkus-core-v3.15/SKILL.md
 * @see .github/skills/camel-quarkus-rest-v3.15/SKILL.md
 * @see .github/skills/camel-quarkus-http-v3.15/SKILL.md
 * @see .github/skills/camel-quarkus-jaxb-v3.15/SKILL.md
 */
@ApplicationScoped
public class StoreRoute extends RouteBuilder {

    @ConfigProperty(name = "store.source.base-url")
    String sourceBaseUrl;

    @ConfigProperty(name = "store.destination.base-url")
    String destinationBaseUrl;

    @ConfigProperty(name = "store.oauth2.token-url")
    String tokenUrl;

    @ConfigProperty(name = "store.oauth2.client-id")
    String clientId;

    @ConfigProperty(name = "store.oauth2.client-secret")
    String clientSecret;

    @ConfigProperty(name = "store.oauth2.scope")
    String scope;

    @Override
    public void configure() throws Exception {

        // --- Global error handling ---
        onException(HttpOperationFailedException.class)
                .handled(true)
                .log("ERROR HTTP ao processar store: statusCode=${exception.statusCode}, body=${exception.responseBody}")
                .setHeader(Exchange.HTTP_RESPONSE_CODE, constant(502))
                .setHeader(Exchange.CONTENT_TYPE, constant("application/json"))
                .setBody(simple("{\"erro\": \"Falha na chamada HTTP: ${exception.statusCode}\", \"detalhe\": \"${exception.responseBody}\"}"));

        onException(Exception.class)
                .handled(true)
                .log("ERROR processando store: ${exception.message}")
                .setHeader(Exchange.HTTP_RESPONSE_CODE, constant(500))
                .setHeader(Exchange.CONTENT_TYPE, constant("application/json"))
                .setBody(simple("{\"erro\": \"${exception.message}\"}"));

        // --- JAXB data format for StoreDesc XML marshalling ---
        JaxbDataFormat jaxb = new JaxbDataFormat("br.com.natal.ia.model");
        jaxb.setPrettyPrint(true);
        jaxb.setFragment(true);

        // --- REST DSL trigger endpoints ---
        rest("/store")
                .description("API para integração de lojas RMS → BrxServices")

                .post("/create")
                    .description("Dispara criação de loja: busca do RMS e envia para BrxServices via POST")
                    .produces("application/json")
                    .to("direct:storeCreate")

                .post("/update")
                    .description("Dispara atualização de loja: busca do RMS e envia para BrxServices via PUT")
                    .produces("application/json")
                    .to("direct:storeUpdate");

        // --- Create store flow ---
        from("direct:storeCreate")
                .routeId("rota-store-create")
                .log("===> [STORE-CREATE] Iniciando criação de loja para store=${header.store}")
                .setProperty("httpMethodDestination", constant("POST"))
                .to("direct:storeGetFromSource")
                .to("direct:storeTransformToXml")
                .to("direct:storeSendToDestination")
                .log("===> [STORE-CREATE] Loja criada com sucesso: store=${header.store}")
                .setHeader(Exchange.HTTP_RESPONSE_CODE, constant(200))
                .setHeader(Exchange.CONTENT_TYPE, constant("application/json"))
                .setBody(simple("{\"status\": \"sucesso\", \"operacao\": \"create\", \"store\": \"${exchangeProperty.storeId}\"}"));

        // --- Update store flow ---
        from("direct:storeUpdate")
                .routeId("rota-store-update")
                .log("===> [STORE-UPDATE] Iniciando atualização de loja para store=${header.store}")
                .setProperty("httpMethodDestination", constant("PUT"))
                .to("direct:storeGetFromSource")
                .to("direct:storeTransformToXml")
                .to("direct:storeSendToDestination")
                .log("===> [STORE-UPDATE] Loja atualizada com sucesso: store=${header.store}")
                .setHeader(Exchange.HTTP_RESPONSE_CODE, constant(200))
                .setHeader(Exchange.CONTENT_TYPE, constant("application/json"))
                .setBody(simple("{\"status\": \"sucesso\", \"operacao\": \"update\", \"store\": \"${exchangeProperty.storeId}\"}"));

        // --- OAuth2 token retrieval ---
        from("direct:storeOAuth2Token")
                .routeId("rota-store-oauth2-token")
                .log("===> [OAUTH2] Obtendo access token...")
                .removeHeaders("*", "CamelExchangeId")  // Remove ALL headers including 'store' to avoid sending to OAuth endpoint
                .setHeader(Exchange.HTTP_METHOD, constant("POST"))
                .setHeader(Exchange.CONTENT_TYPE, constant("application/x-www-form-urlencoded"))
                .setBody(simple("grant_type=client_credentials&scope=${properties:store.oauth2.scope}"))
                .toD("${properties:store.oauth2.token-url}"
                        + "?authMethod=Basic"
                        + "&authUsername=${properties:store.oauth2.client-id}"
                        + "&authPassword=${properties:store.oauth2.client-secret}"
                        + "&authenticationPreemptive=true"  // Force sending Basic auth header immediately
                        + "&httpMethod=POST")
                .unmarshal().json()
                .setProperty("accessToken", jsonpath("$.access_token"))
                .log("===> [OAUTH2] Token obtido com sucesso");

        // --- Get store data from source API (RMS) ---
        from("direct:storeGetFromSource")
                .routeId("rota-store-get-from-source")
                .setProperty("storeId", header("store"))
                .log("===> [SOURCE] Buscando dados da loja ${exchangeProperty.storeId} no RMS...")
                .to("direct:storeOAuth2Token")
                .removeHeaders("CamelHttp*")
                .setHeader(Exchange.HTTP_METHOD, constant("GET"))
                .setHeader("Authorization", simple("Bearer ${exchangeProperty.accessToken}"))
                .setHeader("Accept", constant("application/json"))
                .setBody(constant(null))
                .toD("${properties:store.source.base-url}/services/private/Store/storeDetail"
                        + "?store=${exchangeProperty.storeId}"
                        + "&httpMethod=GET")
                .log("===> [SOURCE] Resposta RMS recebida: ${body}")
                .unmarshal().json();

        // --- Transform JSON to StoreDesc XML ---
        from("direct:storeTransformToXml")
                .routeId("rota-store-transform-to-xml")
                .log("===> [TRANSFORM] Transformando JSON → StoreDesc XML...")
                .process(exchange -> {
                    Object body = exchange.getMessage().getBody();
                    Map<String, Object> storeData = extractStoreData(body);

                    StoreDescModel desc = new StoreDescModel();
                    desc.setStore(getInt(storeData, "store"));
                    desc.setStoreType(getStr(storeData, "storeType"));
                    desc.setStoreName(getStr(storeData, "storeName"));
                    desc.setStoreName10(getStr(storeData, "storeName10"));
                    desc.setStoreName3(getStr(storeData, "storeName3"));
                    desc.setStoreAdd1(getStr(storeData, "add1"));
                    desc.setStoreAdd2(getStr(storeData, "add2"));
                    desc.setStoreCity(getStr(storeData, "city"));
                    desc.setState(getStr(storeData, "state"));
                    desc.setCountryId(getStr(storeData, "countryId"));
                    desc.setStorePcode(getStr(storeData, "post"));
                    desc.setStoreClass(getStr(storeData, "storeClass"));
                    desc.setStoreMgrName(getStr(storeData, "store"));
                    desc.setStoreOpenDate(parseDate(getStr(storeData, "storeOpenDate")));
                    desc.setPhoneNumber(getStr(storeData, "contactPhone"));
                    desc.setStockholdingInd(getStr(storeData, "stockholdingInd"));
                    desc.setChannelId(getInt(storeData, "channelId"));
                    desc.setDistrict(getInt(storeData, "district"));
                    desc.setTransferZone(getInt(storeData, "transferZone"));
                    desc.setDefaultWh(getInt(storeData, "defaultWh"));
                    desc.setStartOrderDays(getInt(storeData, "startOrderDays"));
                    desc.setCurrencyCode(getStr(storeData, "currencyCode"));
                    desc.setLang(getInt(storeData, "lang"));
                    desc.setTimezoneName(getStr(storeData, "timezoneName"));
                    // Default values for fields not present in source
                    desc.setOrigCurrencyCode(getStr(storeData, "currencyCode"));

                    exchange.getMessage().setBody(desc);
                })
                .marshal(jaxb)
                .log("===> [TRANSFORM] XML gerado:\n${body}");

        // --- Send XML to destination API (BrxServices) ---
        from("direct:storeSendToDestination")
                .routeId("rota-store-send-to-destination")
                .log("===> [DESTINATION] Enviando XML para BrxServices (método=${exchangeProperty.httpMethodDestination})...")
                .removeHeaders("CamelHttp*")
                .setHeader(Exchange.HTTP_METHOD, exchangeProperty("httpMethodDestination"))
                .setHeader(Exchange.CONTENT_TYPE, constant("application/xml"))
                .toD("${properties:store.destination.base-url}")
                .log("===> [DESTINATION] Resposta BrxServices: ${body}");
    }

    /**
     * Extracts the store data map from the API response.
     * The response may be a single Map or a List containing a Map.
     */
    @SuppressWarnings("unchecked")
    private Map<String, Object> extractStoreData(Object body) {
        if (body instanceof List<?> list && !list.isEmpty()) {
            return (Map<String, Object>) list.get(0);
        }
        if (body instanceof Map) {
            return (Map<String, Object>) body;
        }
        return new LinkedHashMap<>();
    }

    private String getStr(Map<String, Object> map, String key) {
        Object val = map.get(key);
        return val != null ? val.toString() : null;
    }

    private Integer getInt(Map<String, Object> map, String key) {
        Object val = map.get(key);
        if (val instanceof Number num) {
            return num.intValue();
        }
        if (val instanceof String str && !str.isEmpty()) {
            return Integer.parseInt(str);
        }
        return null;
    }

    /**
     * Parses a date string in "yyyy-MM-dd" format to a Date object.
     * 
     * @param dateStr the date string to parse
     * @return the parsed Date, or null if the input is null or empty
     */
    private Date parseDate(String dateStr) {
        if (dateStr == null || dateStr.isEmpty()) {
            return null;
        }
        try {
            SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd");
            return sdf.parse(dateStr);
        } catch (ParseException e) {
            log.warn("Failed to parse date '{}': {}", dateStr, e.getMessage());
            return null;
        }
    }
}
