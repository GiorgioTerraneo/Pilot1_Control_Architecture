# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Reference Documents
- `piano_azione.md` in the project root is the current action plan. Always re-read it before starting implementation of any new phase or point — it may have been updated since the last read.

## Development Workflow

Architectural plans are produced in a separate planning chat (Opus) with full context on the system's module map, interfaces, and design principles. Claude Code receives the plan, validates it against the actual codebase, flags conflicts, and proposes implementation details. Divergences are arbitrated by Giorgio in the planning chat. Implementation proceeds only after convergence between planning and code validation. Each implemented feature is tested by Giorgio before moving to the next.

## Project Overview

Distributed multi-agent orchestration system for industrial automation. A System Agent (supervisor) parses hierarchical execution plans and dispatches commands to Resource Agents that control physical machines via OPC UA protocol.

## Running the System

The three components must be started in order:

```bash
# 1. Start the API/WebSocket server
python src/server/main.py

# 2. Start resource agent(s) (each machine in a separate terminal)
python src/agents/resources/disassembly_machine.py

# 3. Start the system supervisor (interactive terminal)
python src/agents/system_agent.py
```

Inside the system agent, use `run` to execute a masterplan, `list` to view connected resources, and `exit` to quit.

## Architecture

Three-tier system:

```
SystemAgent (supervisor)
    ↓ WebSocket (ws://localhost:8000/ws)
API Server (FastAPI, port 8000) — acts as broker
    ↓ WebSocket
Resource Agents (one per physical machine)
    ↓ HTTP (app state)
OPCUAManager → asyncua client → PLC/hardware at opc.tcp://192.168.0.200:4842
```

**Key classes:**
- `OPCUAMachineClient` (`src/agents/base_agent.py`) — base class for all resource agents; auto-discovers services via Python method introspection (methods named `service_*` become callable services)
- `OPCUAManager` (`src/server/opcua_core.py`) — manages the OPC UA connection, subscriptions, and value cache; shared via FastAPI `app.state`
- `api_server.py` — FastAPI app with `/ws` WebSocket endpoint; brokers registration, command dispatch, and feedback routing between SystemAgent and resource agents
- `db_manager.py` — SQLite manager; tables `resources` and `services` are reset on each server startup to clear stale sessions

**Plan execution hierarchy:**
- Masterplan (`.txt` in `plans/`) → one line per step: `ResourceName | SERVICE | args`
- Subplan (referenced via `RUN_FILE` in a masterplan) → same format but without the resource prefix
- SystemAgent sends steps sequentially, waits for `done`/`error` feedback before proceeding

## Configuration

`config/settings.py` — central constants: server host/port, OPC UA URL, DB path, plans directory, timeout (360s), log level.

`config/node_map.py` — maps human-readable names to OPC UA node IDs for all connected hardware (DOOSAN cobot, SEIT induction heater, MULLUTENSIL disassembly machine).

## Adding a New Resource Agent

1. Create a new file in `src/agents/resources/`.
2. Subclass `OPCUAMachineClient` from `src/agents/base_agent.py`.
3. Define services as `async def service_<NAME>(self, ...)` methods — they are automatically registered and exposed.
4. Add relevant node IDs to `config/node_map.py`.
5. Run the agent file directly; it self-registers with the API server on startup.

## Notes

- Code comments and plan files are primarily in Italian.
- No test suite exists currently.
- `disassembly_machine_v2.py` (currently untracked) is an in-progress revision of the disassembly machine agent.
- The `services_database.db` file is committed but is volatile runtime state — it is reset on every server start.
