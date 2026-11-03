package spike;

import jakarta.ws.rs.GET;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.PathParam;
import org.eclipse.microprofile.rest.client.inject.RegisterRestClient;

@RegisterRestClient(configKey = "partner")
@Path("/titles")
public interface PartnerClient {
    @GET
    @Path("/{name}")
    String title(@PathParam("name") String name);
}
