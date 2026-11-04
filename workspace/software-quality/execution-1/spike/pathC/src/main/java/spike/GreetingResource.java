package spike;

import jakarta.inject.Inject;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.PathParam;
import jakarta.ws.rs.core.Response;
import org.eclipse.microprofile.rest.client.inject.RestClient;

@Path("/greetings")
public class GreetingResource {

    @Inject
    @RestClient
    PartnerClient partner;

    @GET
    @Path("/{name}")
    public Response greet(@PathParam("name") String name) {
        if (name.isBlank() || name.length() > 20) {
            return Response.status(400).entity("invalid name").build();
        }
        return Response.ok("hello " + partner.title(name) + " " + name).build();
    }
}
