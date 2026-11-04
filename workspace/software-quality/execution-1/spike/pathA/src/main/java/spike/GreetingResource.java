package spike;

import jakarta.ws.rs.GET;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.PathParam;
import jakarta.ws.rs.core.Response;

@Path("/greetings")
public class GreetingResource {

    @GET
    @Path("/{name}")
    public Response greet(@PathParam("name") String name) {
        if (name.isBlank() || name.length() > 20) {
            return Response.status(400).entity("invalid name").build();
        }
        return Response.ok("hello " + name).build();
    }
}
