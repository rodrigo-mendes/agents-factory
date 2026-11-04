# greeting Specification

## Requirements

### Requirement: R1 Greet a known visitor
The system SHALL greet a visitor by the given name.

#### Scenario: named visitor
- **WHEN** the visitor opens the greeting with the name "Ana"
- **THEN** the greeting is "Hello, Ana"

#### Scenario: blank name
- **WHEN** the visitor opens the greeting
- **THEN** the greeting is "Hello, guest"
