# Architecture

## Agents

Agents are the core execution unit in the system.

### Responsibilities
- Execute tasks assigned by the orchestrator
- Maintain conversation state
- Use tools to interact with the environment

### Handoff protocol

When an agent determines it cannot complete a task, it initiates a **handoff** to another agent.

The handoff protocol works as follows:

1. The current agent produces a summary of work done.
2. The orchestrator selects the best agent for the remaining work.
3. The target agent receives the context and continues.

### Lifecycle

Each agent goes through:
- **Initialization** – loading configuration and tools
- **Execution** – processing the assigned task
- **Completion** – returning results or initiating handoff
