package org.acme.items;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record ItemRequest(@NotBlank @Size(max = 80) String name, int quantity) {
}
