package com.brx.functions.rr.restproxy.service;

import java.util.Base64;
import java.util.logging.Logger;

import com.oracle.bmc.ClientConfiguration;
import com.oracle.bmc.auth.ResourcePrincipalAuthenticationDetailsProvider;
import com.oracle.bmc.retrier.RetryConfiguration;
import com.oracle.bmc.secrets.SecretsClient;
import com.oracle.bmc.secrets.model.Base64SecretBundleContentDetails;
import com.oracle.bmc.secrets.requests.GetSecretBundleRequest;
import com.oracle.bmc.secrets.responses.GetSecretBundleResponse;
import com.oracle.bmc.waiter.ExponentialBackoffDelayStrategyWithJitter;
import com.oracle.bmc.waiter.MaxAttemptsTerminationStrategy;

public class OciSecretService {

    private static final Logger LOG = Logger.getLogger(OciSecretService.class.getName());

    private final SecretsClient secretsClient;

    public OciSecretService() {
        ResourcePrincipalAuthenticationDetailsProvider provider =
                ResourcePrincipalAuthenticationDetailsProvider.builder().build();

        RetryConfiguration retryConfig = RetryConfiguration.builder()
                .terminationStrategy(new MaxAttemptsTerminationStrategy(2))
                .delayStrategy(new ExponentialBackoffDelayStrategyWithJitter(1000))
                .build();

        ClientConfiguration clientConfig = ClientConfiguration.builder()
                .connectionTimeoutMillis(3000)
                .readTimeoutMillis(5000)
                .retryConfiguration(retryConfig)
                .build();

        this.secretsClient = SecretsClient.builder()
                .configuration(clientConfig)
                .build(provider);
    }

    OciSecretService(SecretsClient secretsClient) {
        this.secretsClient = secretsClient;
    }

    public String getSecret(String secretOcid) {
        LOG.info(() -> "Retrieving secret: " + secretOcid);

        GetSecretBundleResponse response = secretsClient.getSecretBundle(
                GetSecretBundleRequest.builder()
                        .secretId(secretOcid)
                        .build());

        Base64SecretBundleContentDetails content =
                (Base64SecretBundleContentDetails) response.getSecretBundle().getSecretBundleContent();

        return new String(Base64.getDecoder().decode(content.getContent()));
    }
}
