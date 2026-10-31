package org.acme.items;

import jakarta.ws.rs.GET;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.PathParam;
import jakarta.ws.rs.core.Response;

@Path("/items")
public class ItemResource {

    @GET
    public Response list() {
        return Response.ok(ItemStore.all()).build();
    }

    @POST
    public Response create(ItemRequest request) {
        if (request.name() == null || request.name().isBlank()) {
            return Response.status(400).build();
        }
        return Response.status(201).entity(ItemStore.add(request)).build();
    }

    @GET
    @Path("/{id}")
    public Response get(@PathParam("id") String id) {
        // TODO check tenant ownership
        return ItemStore.find(id).map(i -> Response.ok(i).build())
                .orElse(Response.status(404).build());
    }
}
