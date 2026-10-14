package com.brx.functions.apifacade.service;

import java.io.ByteArrayInputStream;
import java.nio.charset.StandardCharsets;
import java.util.Base64;
import java.util.logging.Logger;

import com.oracle.bmc.ClientConfiguration;
import com.oracle.bmc.auth.AbstractAuthenticationDetailsProvider;
import com.oracle.bmc.auth.ResourcePrincipalAuthenticationDetailsProvider;
import com.oracle.bmc.objectstorage.ObjectStorageClient;
import com.oracle.bmc.objectstorage.requests.GetNamespaceRequest;
import com.oracle.bmc.objectstorage.requests.PutObjectRequest;
import com.oracle.bmc.retrier.RetryConfiguration;
import com.oracle.bmc.secrets.SecretsClient;
import com.oracle.bmc.secrets.model.Base64SecretBundleContentDetails;
import com.oracle.bmc.secrets.requests.GetSecretBundleRequest;
import com.oracle.bmc.secrets.responses.GetSecretBundleResponse;
import com.oracle.bmc.waiter.ExponentialBackoffDelayStrategyWithJitter;
import com.oracle.bmc.waiter.MaxAttemptsTerminationStrategy;

public class OciServiceClient implements OciService {

    private static final Logger LOG = Logger.getLogger(OciServiceClient.class.getName());

    private final ObjectStorageClient objectStorageClient;
    private final SecretsClient secretsClient;
    private String namespace;

    public OciServiceClient() {
        AbstractAuthenticationDetailsProvider provider =
                ResourcePrincipalAuthenticationDetailsProvider.builder().build();

        RetryConfiguration retryConfig = RetryConfiguration.builder()
                .terminationStrategy(new MaxAttemptsTerminationStrategy(3))
                .delayStrategy(new ExponentialBackoffDelayStrategyWithJitter(5000))
                .build();

        ClientConfiguration clientConfig = ClientConfiguration.builder()
                .connectionTimeoutMillis(5000)
                .readTimeoutMillis(15000)
                .retryConfiguration(retryConfig)
                .build();

        this.objectStorageClient = ObjectStorageClient.builder()
                .configuration(clientConfig)
                .build(provider);
        this.secretsClient = SecretsClient.builder()
                .configuration(clientConfig)
                .build(provider);

        try {
            this.namespace = objectStorageClient.getNamespace(
                    GetNamespaceRequest.builder().build()
            ).getValue();
            LOG.info("{\"event\":\"init_complete\",\"namespace\":\"" + namespace + "\"}");
        } catch (Exception e) {
            LOG.warning("{\"event\":\"namespace_unavailable\",\"error\":\"" + e.getMessage() + "\"}");
            this.namespace = null;
        }
    }

    @Override
    public String getSecret(String secretId) {
        LOG.info("{\"event\":\"get_secret\",\"secretId\":\"" + secretId + "\"}");

        GetSecretBundleResponse response = secretsClient.getSecretBundle(
                GetSecretBundleRequest.builder()
                        .secretId(secretId)
                        .build()
        );

        Base64SecretBundleContentDetails content =
                (Base64SecretBundleContentDetails) response.getSecretBundle().getSecretBundleContent();

        return new String(
                Base64.getDecoder().decode(content.getContent()),
                StandardCharsets.UTF_8
        );
    }

    @Override
    public void putObject(String bucketName, String objectName, String data) {
        LOG.info("{\"event\":\"put_object\",\"bucket\":\"" + bucketName
                + "\",\"object\":\"" + objectName + "\"}");

        byte[] bytes = data.getBytes(StandardCharsets.UTF_8);

        objectStorageClient.putObject(
                PutObjectRequest.builder()
                        .namespaceName(namespace)
                        .bucketName(bucketName)
                        .objectName(objectName)
                        .contentLength((long) bytes.length)
                        .putObjectBody(new ByteArrayInputStream(bytes))
                        .build()
        );
    }
}
