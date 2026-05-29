# Architecture Overview

## System design

The system follows a modular architecture with clear separation of concerns.

### Layers

1. **Orchestration layer** – manages agents, routing, and workflows
2. **Agent layer** – individual agents with specific capabilities
3. **Tool layer** – tools that agents can use (search, code, etc.)
4. **Persistence layer** – state management and storage

### Data flow

1. User sends a request to the orchestrator.
2. Orchestrator parses the intent and selects an agent.
3. Agent processes the request, using tools as needed.
4. Results flow back through the orchestrator to the user.
