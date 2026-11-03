# greeting Specification

## Purpose
Greet a visitor by name.

## Requirements

### Requirement: R1 Greet a known visitor
The system SHALL greet a visitor by the given name.

#### Scenario: named visitor
- **WHEN** the visitor opens the greeting with the name "Ana"
- **THEN** the greeting is "Hello, Ana"

#### Scenario: blank name
- **GIVEN** a visitor without a name
- **WHEN** the visitor opens the greeting
- **THEN** the greeting is "Hello, guest"
- **AND** the status is 200
