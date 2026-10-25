# System Executor — Architecture v4: Complete Description
**CIRC4Me Pilot 1, Politecnico di Milano — rev. 2, 2026-07-07**
Companions: `piano_azione_v4.0.md` (implementation plan) · `literature_reviews_summary.md` (research grounding & paper roadmap) · `CIRC4Me_Pilot1_Contesto_Visione.md` (lab vision).

## 0. How to use this document
- **Code view** → §1 (current system, file-level), §2 (defect register with code locations), §5–§7 (protocol/data/plan specs), then `piano_azione_v4.0.md` for the change list.
- **Paper view** → §3 (design principles + their justifications), §4 (module catalog with reasons), §9 (contributions), then `literature_reviews_summary.md` §6 (paper roadmap).
- **Practical view** → §1.7 (how to run), §8 (operating guide + troubleshooting why-map), §10 (open questions/gates).

Provenance tags used everywhere: `[LIT: key]` adopted from literature · `[CONTRA: key]` deliberate divergence from literature · `[GAP-FILL]` fills a hole the literature doesn't cover (PhD novelty space) · `[ORIG]` original, no literature anchor (explicitly legitimate) · `[ARBITRATED]` explicitly decided by Giorgio.

---

# §1 CURRENT ARCHITECTURE (baseline, audited 2026-07-06/07)

## 1.1 Topology and components

```
[React UI (Vite build in src/ui/dist)] ══ /ws/ui ══╗
[SystemAgent  src/agents/system_agent.py]── /ws ───╬═[api_server (FastAPI :8000)]──[OPCUAManager src/server/opcua_core.py]
[ResourceAgent src/agents/resources/…_v3.py]─ /ws ─┤        │                              │ asyncua client
[Observers src/agents/observers/*]─────── /ws ─────╝        │                    [opc.tcp://192.168.0.200:4842]
                                              [services_database.db volatile]     = TTTech Nerve Data Gateway
                                              [data_log.db persistent]              aggregating: ns=3 CODESYS vars
                                                                                     (DOOSAN/SEIT) + ns=4 S7 DBs
                                                                                     (MULLUTENSIL) → Siemens PLC → machines
```

- **SystemAgent** (supervisor): parses masterplan line-by-line at dispatch time, sends one step, waits for terminal feedback, proceeds/halts. Registers on the broker under the literal name `"SUPERVISOR"` (hardcoded lookups server-side). Headless by default; `--cli` gives the interactive terminal (`run`, `list`, `exit`). Abort via `asyncio.Event` set by UI command.
- **api_server**: ONE process, TWO conflated functions — (a) message broker between all WS clients; (b) OPC UA front-end (`subscribe/read/write` actions handled inline via OPCUAManager). Maintains `connected_clients` (name→ws), `connected_supervisors` (RAM only), `ui_clients` set. REST: `GET /resources /status /plans /plans/{name} /observers /data/recent`.
- **OPCUAManager**: resolves ALL node_map entries at startup, caching asyncua Node objects and each node's real VariantType (used for typed writes — PG-1 resolved: PLC accepts `ua.VariantType.Double`). **Verification transport is a 100 ms polling loop** (`_data_poller`) notifying subscribers on value change; `OPCUAClient.create_subscription` exists but is never called (docs claiming "subscription-based with polling fallback" are wrong). `write()` optimistically updates the cache and notifies subscribers with the commanded value before any PLC readback (→ W5). `_monitor_connection` is an empty stub (placeholder for reconnect, v3.2 item 2.3).
- **OPCUAMachineClient** (`base_agent.py`): the resource-agent base class.
  - *Service auto-discovery*: any `async def service_<NAME>` is introspected (`inspect.getmembers` + `signature`) → `{SERVICE: {params:[...], ranges:{...}}}` sent at registration. `get_components_for_param()` lets subclasses declare selector params (e.g. `axis`) → ranges become `{axis:[enum], target_map:{x:{min,max,unit},…}, vel_map:{…}}`.
  - *Write-and-verify*: `write_and_verify(node, value)` = subscribe → write → await `write_response` future (`__write__<node>` key) → `verify_target(node, value, tolerance)`; `verify_target` loops on per-node futures fed by `update` messages, with a 2 s explicit-read fallback and an outer `DEFAULT_TIMEOUT=360 s`.
  - *Sequential engine*: `execute_sequence(steps)` calls `service_*` per step, halts on first exception, sends exactly one terminal feedback (`SUBPLAN_COMPLETED`/`ERROR`). Launched via `asyncio.create_task` from the listen loop (→ no busy guard, W8).
  - `pending_responses` is keyed **by node name** — one future per node, colliding under concurrency.
- **DisassemblyMachineAgent v3** (canonical; name `Disassembly_Machine`): components `x,y,z,c("360"),prs` = `AxisElectrical` (nodes pos_attuale/pos_step/step_enable/vel/acc/dec; `move_to_position` = enable-off → write target → enable-on → verify pos_attuale (tol 0.5) → enable-off; `set_params` = 3 verified writes; **agent-side range validation implemented** with messages `"range check agent-side: …"`), `avvitatore` = `AxisAir` (verified via pos0/pos1_attiva sensors), `barrier_back` = `AxisBarrier` (**timed 10 s actuation, no position sensors** — sensors not wired yet per node_map comment). Services: MOVE, SET_PARAMS, ACTIVATE, DEACTIVATE, ENGAGE, DISENGAGE (+ inherited WAIT). `_send_error` logs + raises (single-feedback discipline — v3.2 item 0.1 done).
  - **v1** (`disassembly_machine.py`): legacy, no ranges, contains a debug override of `write_and_verify` — dead code, dangerous if launched. **v2**: superseded; declares DIFFERENT physical limits than v3 (z max 270 vs 600 mm, prs 1000 vs 1500, x vel 100 vs 500) → gate G1.
- **Observers** (`base_observer.py`): register with `type:"observer"` + `dashboard_config`, subscribe to nodes, persist every update to `data_log.db` (synchronous sqlite insert per sample), forward `data_event` to UI. `DisassemblyObserver` (scatter carico-vs-PRS), `PrsCaricoCsvObserver` (adds CSV in `logs/`, overrides `_listen_loop` by copy-paste).
- **UI** (React, one WS per component — 4 sockets/tab): SupervisorPanel + ResourcePanel (poll REST every 15 s; ONLINE if `now - last_seen ≤ 15 s`), PlanLauncher (plan list, client-side resource extraction for the pre-launch online guard, launch/abort), PlanMonitor (progress_event-driven step list), LogPanel (level+source filters, 200-entry ring), Dashboard (generic renderer of observer `dashboard_config`: line charts + scatter).

## 1.2 Message flow — single command lifecycle (as-is)
1. UI `launch_plan` on `/ws/ui` → server forwards `{"type":"command","command":"launch_plan","plan":…}` to `connected_clients["SUPERVISOR"]`.
2. SystemAgent `execute_masterplan`: pre-counts steps (`parse_master_line` per line, None-filtered), then per line: parse (DB schema lookup **at parse time** = PG-2), build payload `{"action":"execute_subplan","steps":[…]}`, send `dispatch_command{target,payload}`, register `pending_feedbacks[resource]=Future`, `asyncio.wait({future, abort}, timeout=AGENT_RESPONSE_TIMEOUT=30 s)`.
3. Broker routes to target ws as `{"type":"command","payload":…}`; unknown target → `{"type":"error"}` back to the sender (NOT tied to the pending future → W7).
4. Agent listen-loop spawns `execute_sequence(steps)`; per step `service_*` → `write_and_verify` chains; on exception → `feedback ERROR` + stop; on success → single `feedback SUBPLAN_COMPLETED`.
5. Server forwards feedback to `"SUPERVISOR"` with `{resource,status,message}`.
6. Supervisor resolves/except's the future by RESOURCE NAME (→ W4), logs, `progress_event` to UI, next line (or break on error/timeout/abort).
7. UI receives `progress_event`/`log_event`/`data_event` broadcasts.

## 1.3 WebSocket taxonomy (as-is)
`/ws` client→server actions: `register` (types: supervisor|observer|resource), `dispatch_command`, `feedback`, `progress_event`, `log_event`, `data_event`, `heartbeat`, `get_resources`, `subscribe|unsubscribe|read|write` (unknown node → **silently ignored**, W13).
Server→client types: `status, update, read_response, write_response, command, feedback, resource_list, error`.
`/ws/ui` actions: `launch_plan, abort_plan`; broadcasts: `progress_event, log_event, data_event`.
Cleanup: on `WebSocketDisconnect`, anti-zombie check (only the ACTIVE socket for a name unregisters — good); on generic `Exception`, **no cleanup** (W6b).

## 1.4 Data stores (as-is)
- `services_database.db` — volatile, `reset_db_state()` at every server start. Tables: `resources(name PK, status, last_seen)`; `services(id, resource_name FK, service_name, params_json, ranges_json)` — **ranges_json written, never read by anyone** (W14); `observer_dashboards(name PK, dashboard_config)`.
- `data_log.db` — persistent, never reset: `data_log(id, timestamp TEXT, node_name, value REAL, observer)` — no indexes; `/data/recent` full-scans per observer then slices in Python (W17).
- Ad-hoc CSVs in `logs/` from the CSV observer.

## 1.5 Plan format (as-is; the contract with the upstream Planner)
`Resource | SERVICE | arg1 , arg2 , …` (POSITIONAL, comma-separated — note: older docs said `param=value`; **code is positional**, gate G4) · `Resource | RUN_FILE | subplan.txt` (subplan = same format without resource column; target inherited) · `#` comments, blank lines ignored. Existing plans: DEMO (uses z 330 + ENGAGE/DISENGAGE → requires v3), DENSO screw/shaft, RAKUN magnet extraction & induction, examples. `masterplan_example.txt` RUN_FILE points to an ABSOLUTE path of the old project (stale + traversal example).

## 1.6 config
`settings.py`: paths, `SERVER 0.0.0.0:8000`, `OPC_SERVER_URL`, `LOG_LEVEL/FORMAT`, `DEFAULT_TIMEOUT=360`, `AGENT_RESPONSE_TIMEOUT=30`, `HEARTBEAT_INTERVAL=5 / TIMEOUT=15`, ASCII `Icons`. (`RETRY_ATTEMPTS` zombie already removed per v3.2 0.1.)
`node_map.py`: ~100 entries — `dcob_*` (ns=3 CODESYS via Nerve), `seit_*` (ns=3), `mill_*` (ns=4 S7: axes X/Y/Z/360/PRS with ACC/DEC/POS_ATTUALE/VELOCITA_ALTA/PL_STEP/POS_STEP; air/HMI; sensors; `mill_carico` load cell).

## 1.7 How to run (practical, as-is) — ⚠ connects to the real PLC; humans only
```
python src/server/main.py                                  # broker+OPCUA (resets services DB, resolves ALL nodes — fail-fast W9)
python src/agents/resources/disassembly_machine_v3.py      # canonical agent (docs previously said v1/v2 — wrong)
python src/agents/system_agent.py [--cli]                  # supervisor (headless default)
python src/agents/observers/disassembly_observer.py        # optional observers
# UI: http://localhost:8000  (served from src/ui/dist)
```
**Standing safety rule: no AI session ever launches these without explicit per-instance human approval.**

## 1.8 Docs-vs-code discrepancies found (Phase 1)
1. "Subscription-based verify with polling fallback" → actually polling-only + optimistic write echo. 2. Plan args `param=value` in docs → positional CSV in code (G4). 3. Docs/CLAUDE.md point to v1/v2 agent → v3 is canonical (demo plans require it). 4. "5 services" → v3 exposes 7. 5. "Known limitations" list stale (heartbeat/UI/observer/timeout/range-validation all DONE). 6. Example masterplan RUN_FILE absolute path to old project. 7. Plan-doc filename drift (CLAUDE.md said `piano_azione.md`).

---

# §2 DEFECT REGISTER (Phase 1, full)

## 2.1 Weaknesses — CRITICAL
**[W1] Completion-vs-ack timeout conflation.** `system_agent` waits the WHOLE step/subplan under `AGENT_RESPONSE_TIMEOUT=30 s`; the only agent response is the terminal feedback. Any step >30 s (RAKUN induzione: x at vel 10 → MOVE to 365 ≈ 36 s) or any multi-step RUN_FILE → supervisor "timeout", plan aborted, **machine keeps executing** (split-brain). Fix A.3. `[LIT: SiLA2 observable commands]`
**[W2] Abort doesn't stop the machine.** Abort/timeout/error only stop DISPATCHING; no cancel path exists; UI prints "INTERROTTO" while axes move; on error the machine freezes mid-plan in an undefined posture. Fix A.7 (honest levels) + F.5 (safing, gate G3). `[LIT: JPL-FDIR]` `[GAP-FILL: physical saga]`
**[W3] Silent step skipping.** `parse_master_line`/`parse_line_with_schema` return None on unknown service / wrong param count / malformed line → `execute_masterplan` just `continue`s. Plan integrity violated; concrete scenario: DEMO plan against v2 schema silently drops ENGAGE/DISENGAGE → `MOVE x 1999` with barrier engaged → collision; or a dropped slow SET_PARAMS lets a press MOVE run at the previous high speed. Fix A.2. `[LIT: RP-check]`
**[W4] No correlation + no plan lock.** `pending_feedbacks` keyed by resource name; no message IDs anywhere; late feedback from a timed-out step can satisfy the NEXT plan's wait on the same resource. UI `isRunning` resets on refresh → double launch → two masterplans interleave (agent has no busy guard either, W8). Fix A.1+A.4. `[LIT: Leitão failure modes; FIPA conversation-id concept]`

## 2.2 Weaknesses — MAJOR
**[W5] Write echo defeats same-node verify.** `OPCUAManager.write()` updates cache + `_notify_subscribers(commanded value)` on success of the OPC write; `verify_target` on the same node matches the echo instantly → SET_PARAMS (vel/acc/dec) and step_enable verifications are illusory; MOVE remains genuinely verified (different node: pos_attuale). Docs claim subscriptions; code polls. Server-side fix A.6 — **gate G2** (adjacent to the protected agent pattern; the fix makes the documented property true). `[LIT: Simplex — guard must observe the plant, not its own command]`
**[W6] Dispatch can unwind the supervisor + dirty cleanup.** `dispatch_command` sends on the target socket from within the SUPERVISOR's handler; dead socket → exception → supervisor connection torn down (no reconnect exists yet); generic-Exception path performs no registry/DB cleanup → stale "online" entries. Fix A.5 (+D.1).
**[W7] Offline-target misdiagnosis.** Server replies `{"type":"error"}` untied to the pending future → supervisor waits full 30 s → reports "non ha risposto", wrong cause/latency. Fix A.5.
**[W8] No agent busy guard.** Every command spawns a new `execute_sequence` task → interleaved OPC writes on one machine possible. Fix A.4.
**[W9] Fail-fast node resolution (PG-3).** One unresolvable node_map entry aborts server startup → a PLC-side rename bricks the whole lab; blocks DOOSAN/SEIT onboarding. Fix D.6. `[LIT: FDIR isolation]`
**[W10] Poller single-fault stall.** One try/except wraps the whole subscriber sweep: one flaky node degrades ALL live updates to 1 Hz retry; verify survives only via its 2 s read fallback. Fix D.5.
**[W11] Range divergence across coexisting agent versions** (+docs pointing at v1). SSoT violated at repo level; hardware truth unknown → **gate G1**; consolidation A.0.
**[W12] Security cluster.** No auth on `/ws` (anyone on LAN can register as "SUPERVISOR" — name collision replaces the socket — or write raw nodes) nor `/ws/ui`; `GET /plans/{name}` path traversal (`os.path.join` with `..`); RUN_FILE accepts absolute paths; binds 0.0.0.0. Fix D.7 (+A.2 confines RUN_FILE).
**[W13] Unknown-node silence.** subscribe/read/write with unknown friendly name → `continue` (no reply) → a typo'd node in an agent yields a 360 s TimeoutError with a misleading message. Fix A.5.

## 2.3 Weaknesses — MINOR
**[W14]** `get_all_resources_schemas()` omits ranges_json and swallows exceptions into `{}` → planned DB-side validation had no data path; DB corruption masquerades as "service not found". Fix A.2/B.4. **[W15]** PlanLauncher fetches `/resources` once → pre-launch guard evaluates stale snapshots (false OFFLINE after 15 s idle; brief false ONLINE). Fix E.1/B.5. **[W16]** WSLogHandler added per connect, never removed (duplicates after reconnect); UILogHandler on root logger forever; emit() assumes running loop. Fix B.7. **[W17]** data_log unbounded/no index; `/data/recent` full scan; Dashboard scatter pairs x/y by ARRAY INDEX not timestamp → misaligned carico-vs-PRS points when update rates differ (research-data correctness). Fix B.4/E.7. **[W18]** `api_server.py` imports `opcua_core` twice (top-level AND package path) → two module objects; works only because running `main.py` puts `src/server` on sys.path. Fix C.1.

## 2.4 Technical debt (register)
Dead code: v1 agent (dangerous override), v2 agent, commented REST endpoints, `_is_connected` block, `_monitor_connection` stub, `create_subscription` unused, `masterplan_* copy.txt`, empty `Icons.WAIT`. Duplication: `calcStatus`+`HEARTBEAT_TIMEOUT_S` in 4 UI files (drifts from settings); CSV observer copy-pastes `_listen_loop`; v2/v3 near-identical classes. Magic numbers: 0.1 s poll, 2.0 s verify fallback, tolerances 0.05/0.5, barrier sleep(10), MAX_LOGS 200, windows 200/500. Naming: `contraints_data`, "rangeI FISICI", axis key `"c"`→prefix `"360"`, IT/EN mix. Structure: `sys.path.append` hacks everywhere (no package); parser is supervisor-only but lives in utils and couples to DB at parse time (PG-2, mitigated by pre-launch guard, properly fixed by A.2 validating against DB once, pre-flight); `node_modules` committed (~12k files); `*.db` committed; **no git repo** (fix A.0 — highest-leverage single item).

---

# §3 DESIGN PRINCIPLES & INVARIANTS (with merit-based justifications)

*(Per working rule: no principle below is justified by "the roadmap says so"; alignment with the vision may be noted, never used as the argument.)*

1. **Agents are target-blind.** They speak node names to the broker only. Justification: transparency (same plan, same code path, any world) becomes structural rather than procedural; zero per-agent configuration surfaces; virtual runs exercise the SAME agent code, so validation covers the executor itself.
2. **The broker stays dumb.** New capability = new client or new module, never broker logic. Justification: a logic-free routing core is the one component that never needs re-validation; extensibility for pilot-2 resources without touching supervision.
3. **Mechanism/policy split for worlds.** *Which* world a run uses = dispatcher/coordinator policy; *how* worlds are reached and kept un-mixed = Plant Gateway mechanism. Switching authority sits in the dispatcher layer because: (a) auditability — only the component that knows "run X, step k" can bind target→run records; (b) mis-dispatch must be structurally impossible (explicit ctx stamping) not procedurally avoided (gateway namespace merging makes world selection an implicit side effect of node naming — silent, catastrophic failure class); (c) testability — dispatcher switching is ordinary code under CI, gateway config is not; (d) vendor-independence — the capability ports to any future gateway; Nerve is a deployment substrate, not a dependency.
4. **SystemAgent is strictly single-world.** (a) fidelity: virtual validation validates the executor only if the SAME supervisor code executes both worlds — a dual-cursor supervisor runs virtual through a different internal path (shared state), quietly invalidating comparisons; (b) fault isolation: a crash in the virtual leg must not take down physical supervision. Cross-world logic lives in a separate, optional Coordinator.
5. **Safety authority belongs to the simplest verifiable component** (agent-side guard on declared ranges — an informal Simplex decision module; planner/DT/UI may propose, the guard disposes). `[LIT: Sha-Simplex]`
6. **The executor never invents behavior.** Plans come validated from upstream; even branches are regenerated at process→system planning level (KBS) and re-validated; the executor's adaptive envelope is bounded to retry/hold/safe-state. `[ARBITRATED]` `[CONTRA: unconstrained-replanning — bounded adaptivity as a safety position]`
7. **Deterministic glass box.** No learned/opaque logic in the execution path; learned artifacts (invariants, duration models) may only WARN or parametrize, never authorize. `[CONTRA: intelligent-MES]`
8. **Every run is scientific data.** Event-sourced records with run identity, context, pedigree; loss of a run's history is a defect, not an inconvenience. `[GAP-FILL]`
9. **SSoT for physical truth** in agent constructors (ranges, anchors, reversibility), everything else derived.
10. **Additive plan-format evolution only** (backward compatibility with the Planner contract).

---

# §4 TARGET ARCHITECTURE — module catalog (functionality + reason for existing)

```
                 ┌───────────────── UI v2 (observer-defined dashboards; target-aware chrome) ───────────────┐
                 │ /ws/ui                                                                                   │ REST
[Execution Coordinator]══ ledger/Δ ══╦═ [SystemAgent│virtual] ─┐                                            │
 (symbiotic simulation)              ╚═ [SystemAgent│physical]─┤ /ws                                        │
                                                               ▼                                            │
                                     [BROKER — pure message routing]                                        │
                                                │ internal API (ctx-stamped)                                │
                                     [PLANT GATEWAY — "node access in world W"] ────────────────────────────┘
                                      ├─ ctx: physical ───[Nerve Data Gateway]──PLC──machines
                                      ├─ ctx: MiL-behave ─[Python behavioral plant]···(digital shadow can mirror this — C.9)
                                      ├─ ctx: SiL-A ──────[PLCSIM Advanced — real S7 logic]
                                      ├─ ctx: SiL-B ──────[2nd CODESYS on Nerve — real 61131-3 logic]
                                      └─ ctx: MiL-geo ────[ISG Virtuos — kinematics/collision]
[ResourceAgents (target-blind)]── /ws ──▲     [EVENT LOG]     [KBS/Planner ⇄ HOLD/capsule/resume (F.3)]
[Observers]─────────────────────────────┘
```

## 4.1 Broker (slimmed `api_server.py`)
**Does:** WS client registry (supervisors, agents, observers, coordinator, UI), typed-message routing, UI broadcast, REST. **Why:** see §3.2. **Changes vs today:** OPC UA actions delegated to Plant Gateway; typed envelope forwarding (correlation/run/ctx/error fields); per-target send isolation (W6); cleanup in all exception paths; `GET /execution/current` (server-truth for UI rehydration); token check on register (D.7).

## 4.2 Plant Gateway (new `src/server/plant_gateway.py`)
**Does:** the ONLY OPC UA toucher. One manager per ExecutionContext (connection, per-context node resolution, poller, cache, subscriber sets); `read/write/subscribe/unsubscribe(node, ctx)`; refuses ctx-less commands when >1 context configured; hard-blocks state-injection writes on ctx=physical; per-node fault quarantine; (after G2) no optimistic write echo — only poller readback notifies.
**Why it exists:** one-sentence-per-module explainability `[ARBITRATED]`; structural impossibility of world mix-ups; clean home for W18/W5/W10 fixes; the natural future Nerve Docker workload. **Logical module now, separate process only when contexts multiply** — a process boundary adds a hop and a failure mode without adding explanatory power beyond the interface boundary.

## 4.3 ExecutionContexts — the validation ladder (C.2)
`{name, opcua_url, mode, validity_envelope, plant_binding}`; target = (control endpoint, plant behind it):

| Rung | Control | Plant | Endpoint | Validity envelope |
|---|---|---|---|---|
| **MiL-behave** | behavioral model | model | Python plant server | logic, sequencing, approximate timing — NEVER collision |
| **MiL-geometric** | model/coupled | Virtuos models | Virtuos OPC UA connector | + kinematics, collision, admissibility of motion |
| **SiL-A** | REAL S7 logic (PLCSIM Advanced) | virtual (opt. Virtuos-coupled) | PLCSIM's own OPC UA server | + control-logic correctness (MULLUTENSIL) |
| **SiL-B** | REAL 61131-3 (2nd CODESYS on Nerve) | virtual | its OPC UA exposure | + control-logic correctness (DOOSAN/SEIT) |
| **HiL** | real PLC hardware | simulated I/O | same physical endpoint | timing on real control HW (lab wiring undefined — open) |
| **physical** | real | real | Nerve gateway | reality |

**Why:** validation-before-physical-execution is the lab's core requirement; the ladder prices it (cheap→expensive) with ONE plan format and ONE dispatch path. Envelopes prevent reading "passed on MiL-behave" as "collision-free"; every verdict and learned invariant carries the envelope of the rung that produced it `[LIT: FTRT validity limits; LoD-2015]`.
**Implementation trap:** node_map hardcodes ns INDICES; namespace indices are server-local (PLCSIM/CODESYS renumber) → per-context resolution via namespace URI or generated per-context maps (C.3) or every virtual endpoint fails silently.

## 4.4 MiL-behave — the behavioral virtual plant (C.5) `[name ARBITRATED]`
**Does:** standalone asyncua OPC UA **server** exposing the same node names as the PLC. Per-component state machines: electrical axes `IDLE →(step_enable ↑, target=pos_step)→ MOVING (pos_attuale integrated on a trapezoidal profile from commanded vel/acc/dec) → IN_POSITION → IDLE`; air actuators = timed two-state setting pos0/pos1_attiva; barriers = pure delays. Parameters derived from the canonical agent's declared ranges (SSoT pays twice). Explicit write-latency parameter. Scriptable fault injection (C.6): stuck axis, slow drift, sensor flicker, delayed settle, **ack-without-apply** (the W5/A.6 proof case). **State-injection API from day one** (`set_state(node,value)`) — the resync primitive the Coordinator will need; the literature's one hard problem (initialization from live state) designed first, not last `[LIT: online-sim-review-2024]`.
**Relation to Giorgio's thesis MiL (ISG Virtuos C# blocks)** — the design descends from it with one structural simplification. The thesis blocks fused two layers:
| Thesis component | New home | Delta |
|---|---|---|
| Mission layer (mission string → sequence of action states → per-step targets; big C# switch tables) | **plans-as-data + executor** — subplans ARE the mission tables; `service_*` are the primitive action states | The layer that made Virtuos blocks unmaintainable (missions as code in block diagrams) is gone; missions never enter the model |
| Achievement transitions (`current within target ± T`) | `verify_target` (production code) | identical principle, already hardware-proven |
| Axis motion (Virtuos axis model blocks fed `target_*`, produced `current_*`) | plant SM trapezoidal integration | explicit, code-diffable, CI-runnable |
| `EndMission` handshake / edge+debounce hacks (`_LAST` vars, `count==100`) | terminal feedback / explicit write-latency parameter | modeled honestly instead of hand-debounced |
| System control module (watch EndMission, advance plan) | the REAL SystemAgent | thesis had a MODEL of control; now the real supervisor executes → a MiL run validates the executor software itself |
| 3D/geometry (Virtuos environment) | NOT here — MiL-geometric context | the only sense in which anything is "lighter"; plus C.9 below recovers visualization free |
Prototype lessons carried: sensor-less actuators need timed transitions (his commented-out Gripping states = today's AxisBarrier sleep(10)); manual edge detection must be replaced by proper event handling; models must live as organized code, not diagram blocks.

## 4.5 Digital shadow as virtual-run visualizer (C.9) ⭐ `[ORIG — Giorgio-favorite]`
**Does:** the existing unidirectional digital shadow (Virtuos side, already consuming OPC UA) is pointed at the MiL-behave context's server instead of the physical endpoint → **free 3-D visualization of virtual executions, zero new modeling**. **Why:** recovers the "watch the machine move" insight of the thesis setup for hardware-free runs; demo-grade artifact for visitors with zero machine risk; executor-side cost ≈ a config parameter + documentation (shadow re-pointing is a lab-side action).

## 4.6 SystemAgent (supervisor) — target-blind plan executor, single world
**Does (post Phase A):** pre-flight-validates the WHOLE plan (incl. RUN_FILE recursion, schema+range checks vs DB, path confinement) and refuses on any error — the silent-skip class dies structurally; executes the validated step list: dispatch (correlation+run stamped) → ACK ≤5 s (`NO_ACK` fail-fast) → PROGRESS-refreshed liveness window (60 s) → terminal; single-active-plan lock; HOLD (pause at step boundary, resumable) / STOP-DISPATCH (honest wording) / later SAFE-STOP (F.5); emits run-stamped progress; run records into the event log.
**Why each piece:** pre-flight `[LIT: RP-check]` = the cheap rung of the validation stack, years before the DT; ACK/completion split `[LIT: SiLA2 observable commands]` kills W1's split-brain by separating "agent alive" (ack/progress/heartbeat) from "work done" (terminal), with liveness instead of one wall-clock guess `[CONTRA: static timeout stack]`.

## 4.7 Execution Coordinator (separate module, built LAST — G.5/G.6) `[ARBITRATED: last]`
**Does:** supervisor-of-supervisors for dual-world runs. Owns exactly three things: (1) the **run ledger** — step k → {virtual verdict, duration, anchor end-state vector, ts}; (2) the **permission window Δ** — the physical SystemAgent may enter step k only after the virtual completed k, and may lag at most Δ; (3) **divergence & hold policy** — anchor-point comparison at step boundaries; virtual failure at k+Δ → HOLD physical at last validated step (SAME machinery as inspection-triggered replanning, F.3 — one pathway, two triggers); resync = state-inject physical actuals into the virtual plant, replay window. Non-interference rule: the virtual leg never delays the physical leg except at permission boundaries `[LIT: shadow-mode]`.
**The Δ spectrum unifies three capabilities in one mechanism:** Δ=∞ → full virtual validation then physical run (virtual commissioning); finite Δ → look-ahead execution `[LIT: FTRT]`; no virtual leg → today's direct execution (coordinator absent, zero cost).
**Staged autonomy** `[LIT: symbiotic simulation modes]`: stage 1 decision-support (verdict reports, human approves), stage 2 control (auto-HOLD).
**Why separate:** keeps SystemAgents simple/tested/single-world (§3.4); look-ahead optional; and it is precisely Giorgio's thesis "system control module" **promoted one level** — it tracks *worlds* reaching end-of-step, not machines reaching end-of-mission. Field name: **symbiotic simulation control system** — already applied to remanufacturing decision support in the literature (positioning anchor).

## 4.8 ResourceAgents — evolution, not revolution
Kept: introspection skill model (independently convergent with SiLA 2's discovery — strong evidence the pattern is right), SSoT constructor declarations, write-and-verify, sequential engine. Added: busy flag (W8; resource ownership `[LIT: holonic]`), ACCEPTED/PROGRESS/terminal with correlation echo (W1/W4), typed errors + **error context capsule** on failure (machine state snapshot: cached node values, last N updates, step index — post-mortems from data, not archaeology `[LIT: RemoteAgent-Livingstone; ESA safe-mode lessons]`), anchor-point declarations (C.8 `[LIT: anchor-points]`), later reversibility classes + `service_safe_state` (F.5, gate G3), `cancel_requested` checked between steps (A.7 — never mid-write).

## 4.9 Event Log (B.1) — the research-data backbone `[GAP-FILL]`
`execution_events(id, run_id, ts, source, event_type, step, payload_json)` in data_log.db; single writer = server (sees everything). Every dispatch/ack/progress/feedback/hold/resume/verdict, run- and ctx-stamped. **Why one table unlocks six features:** replay & time-scrub; golden-plan diffs (C.7); duration models & physics-based timeouts (G.8); conformance reports; coordinator ledger persistence; publishable disassembly execution datasets — the datasets the disassembly-planning literature itself lacks.

## 4.10 Inspection & replanning interface (F.1–F.3) — the alternation seam
Workflow: plan interleaves process steps with **READ** (measure → value into feedback+log) and **CHECK** (comparator → CHECK_PASSED/CHECK_FAILED) steps. On CHECK_FAILED or explicit HOLD: (1) machine brought to safe hold; (2) **inspection capsule** published upstream (REST/WS for the KBS): measurements, run_id, step reached, machine state snapshot, plan pedigree; (3) planner regenerates at PROCESS level → re-translates to a SYSTEM plan tail; (4) executor accepts `resume_plan` ONLY after the new tail passes full pre-flight. Pre-authored `ON_FAIL` branches exist ONLY for local safety contingencies (retreat/safing), never product-state routing.
**Why this shape** `[ARBITRATED: branches regenerate upstream]`: process-level branching is a planning competence (precedence knowledge, cost models live in the KBS); the executor's stable, scale-independent contract is HOLD/report/resume — and it is deliberately the SAME pathway the Coordinator triggers on virtual failure, so mid-run replanning and look-ahead repair share one tested mechanism.

## 4.11 Plan pedigree & capability hash (F.4) `[LIT: JPL sequence traceability; SiLA2 versioning]`
Plan header carries hashes of (plan text, capability schema of targeted resources, node_map version) + validation verdicts (which rung, when, envelope). Executor refuses execution on hash mismatch; agents register capability hashes; capability change invalidates cached validations AND learned invariants. **Why:** generalizes the v2/v3 range-divergence incident into a machine-checkable property: "this plan was validated against a machine that no longer exists".

## 4.12 Safing ladder — the "physical saga" (F.5, gate G3) `[GAP-FILL]`
Reversibility classes per step: *reversible* / *compensable-to-safe-state* / *irreversible-forward-only*. Per-machine `service_safe_state` (definitions = hardware truth = Giorgio). Abort ladder: HOLD → STOP-DISPATCH → SAFE-STOP (→ hardware E-stop is documentation-only; software never pretends to own it). **Why:** transactions roll back; physics doesn't. Saga's principle (declared compensation) is kept, its framing (undo) rejected `[LIT: Sagas-1987]` `[CONTRA: saga-as-undo]` — safing = "reach a known-safe configuration NOW".

## 4.13 Observers & UI v2 (E-phase) `[ARBITRATED: observer-defined UI]`
dashboard_config v2 — declared ENTIRELY in the observer class; React is a generic interpreter (zero observer-specific code):
```json
{ "group": "Disassembly Machine",
  "preview": { "type": "sparkline|stat|mini-scatter", "title": "...", "nodes": [...], "window": 100 },
  "detail":  { "layout":  [ {"type":"line|scatter|stat|table", "nodes":[...], "axes":..., "thresholds":...} ],
               "controls":[ {"type":"time_window","options":["live","5m","1h","run"]},
                            {"type":"node_toggle"}, {"type":"threshold_line","node":"..."},
                            {"type":"pause_resume"}, {"type":"export_csv"} ] } }
```
Main dashboard = grouped collapsible sections of small **preview** tiles; click → `/observer/{name}` in a **new browser tab** (survives refresh; second monitor) rendering the observer-declared **detail** page with its own filters/toggles. Styling: high-performance-HMI conventions (muted surfaces; color reserved for state/alarms; design tokens; card/badge components; tabs Monitor/Log/Dashboard) + Grafana-style preview→drill-down as the interaction model. Target-awareness: UI chrome shifts (amber) for virtual contexts; ctx badges on runs; ghost-run overlay (predicted position-vs-time per axis drawn before execution, live trace over it — deviation visible by eye). Armed-steps toggle (E.8): when ON, steps marked `ARMED` pause for explicit confirmation.

## 4.14 Invariant distillation (G.7) `[ARBITRATED: Giorgio's idea]` `[GAP-FILL]`
Mine recurring virtual-rejection preconditions ("x>1900 while barrier engaged ⇒ rejected, 7/7") into candidate invariants → human-confirmed (or N-consistent auto-promoted) → pre-flight **WARNING** rules. Properties: restrictive-only (may flag, never authorize — the DT stays the sole admissibility authority); provenance (which runs taught it) + validity envelope of the producing rung; invalidated on capability-hash/layout change; exportable to the planner as constraints (planner-side use is the KBS's decision). **Why:** hand-authoring interlocks contradicts the DT's purpose (admissibility is a property of MOTION, unknowable a priori at FMS scale — vision §6) and can't scale; but each expensive DT rejection amortizes into a millisecond pre-check — validation without bottleneck at FMS throughput. Replaces the rejected "authored interlock table" idea.

## 4.15 Nerve — roles derived from capabilities (never forced)
IS: (1) Docker workload host for executor stack + MiL-behave + coordinator (managed deployment = software pedigree; always-on, adjacent to the PLC network); (2) Data Gateway = the PHYSICAL world's aggregation server (already merges ns=3 CODESYS + ns=4 S7 under one endpoint — do NOT merge virtual endpoints into it, §3.3); (3) CODESYS soft-PLC in real-time VM = **SiL-B host** (DOOSAN/SEIT logic already lives there — SiL without any Siemens toolchain); (4) common timestamp reference (all physical signals already pass through it); (5) storage volume for logs. IS NOT: world-selection policy; behavior-model authoring; Virtuos host.

---

# §5 PROTOCOL (target; PROTOCOL.md grows from A.1)
**Envelope (all messages):** `msg_id` (uuid12), `ts`, `source`, optional `correlation_id`, `run_id`, `ctx`.
**Feedback statuses:** `ACCEPTED | PROGRESS(step,total,message) | SUBPLAN_COMPLETED | ERROR(error_type,message,capsule?)`.
**Error taxonomy:** `VALIDATION, RANGE_AGENT, RANGE_DB, COMMS, HW_TIMEOUT, BUSY, UNKNOWN_NODE, DISPATCH_FAILED, STALE_FEEDBACK, NO_ACK` (retry policy D.4: only COMMS-class retriable).
**/ws actions:** register(name, type, services, capability_hash*, anchors*), dispatch_command(target,payload{action,steps,correlation_id,run_id,ctx*}), feedback(…), progress_event, log_event(structured), data_event(ctx-tagged), heartbeat, get_resources, subscribe|unsubscribe|read|write(node, ctx*). Unknown node → `error{error_type:UNKNOWN_NODE,node}`.
**/ws/ui:** launch_plan(plan, ctx*), abort_plan, hold_plan, resume_plan (+ arm_step later).
**REST:** `/resources /status /plans /plans/{name} /observers /data/recent /execution/current` + later `/capabilities /capabilities/pddl* /data/export`. (* = later phases)

# §6 DATA STORES (target)
services_database.db (volatile): resources; services(params_json, ranges_json — READ path fixed A.2); observer_dashboards(config v2).
data_log.db (persistent): data_log(+index (observer,id)); execution_events (B.1). Run provenance packaging (RO-Crate-style zip: plan+pedigree+events+data slice) = backlog extension.

# §7 PLAN FORMAT — evolution (additive ONLY, G4 pins arg style)
Today: `Resource | SERVICE | a, b, c` positional; `RUN_FILE`; `#`. Phase F additions: `READ | node`, `CHECK | node, op, value`, `ARMED` marker, pedigree header block, `ON_FAIL | RUN_FILE | safety_contingency.txt` (safety-only). Later: `$variables` templating. NEVER added: product-state branching (regenerates upstream, §4.10) `[ARBITRATED]`; BPMN engine `[CONTRA: BPMN-engine — wrong semantics for hardware: no native write-and-verify/safe-state; weight/opacity]`; BT tick semantics `[CONTRA: BT-ticking — 90 s heating steps don't want 10 Hz ticks; guarded-step semantics à la PLEXIL fit better if a richer language is ever needed]`.

# §8 PRACTICAL GUIDE
**Add a machine agent:** subclass `OPCUAMachineClient`; declare components with ranges (+anchors, later reversibility) in the constructor; write `async def service_*` methods; add nodes to node_map; run (human) — self-registers.
**Add an observer:** subclass `BaseObserver`; list nodes; override `get_dashboard_config()` (v2 schema §4.13). No server/UI changes ever.
**Write a plan:** one step per line; RUN_FILE for reusable sequences; keep SET_PARAMS adjacent to the MOVE they configure; after A.2 the pre-flight report lists every problem before anything moves; check estimated durations in the pre-launch panel (E.3).
**Troubleshooting why-map:**
| Symptom | Component | Item |
|---|---|---|
| Abort ~30 s into a long step, machine still moving | supervisor timeout semantics | A.3 |
| A plan line seems ignored | (pre-A.2: silent skip!) validation | A.2 |
| Abort pressed, machine continues | abort levels/safing | A.7/F.5 |
| Feedback matched to wrong step / ghost unblock | correlation | A.1 |
| Two plans at once after browser refresh | plan lock + rehydration | A.4/B.5 |
| SET_PARAMS "verified" but PLC didn't apply | write echo | A.6 (G2) |
| Supervisor connection dies when an agent dies | dispatch isolation | A.5 |
| 6-min timeout on typo'd node | unknown-node replies | A.5 |
| Server won't start after PLC rename | fail-fast resolution | D.6 |
| One flaky node freezes all live data | poller quarantine | D.5 |
| Dashboard slow after months | data_log index/limits | B.4 |
| Scatter carico-PRS looks wrong | index-pairing bug | E.7 |
| "Validated" plan on changed machine | pedigree/capability hash | F.4 |
| Which world did run X use? | ctx stamps | C.2 |
| Virtual ≠ physical outcome | anchors + validate-the-validator | C.8/G.1 |

# §9 RESEARCH CONTRIBUTIONS EMBEDDED (paper hooks → lit doc §6)
1. Mission-operations framing for de-remanufacturing execution (rule-check→testbed→execute pipeline, safing, pedigree) — unoccupied in manufacturing literature. 2. Minimum viable capability model (introspection skills + ranges/units/anchors/reversibility; convergent evolution with SiLA 2 as evidence) vs heavy AAS ontologies. 3. Physical saga (reversibility classes + safe-state driving). 4. Bounded adaptivity as a safety position (branches regenerate upstream; validated-window look-ahead). 5. Invariant distillation from virtual validation (counterexample-guided pre-flight rules). 6. Executor as scientific instrument (event-sourced runs → published execution datasets; empirical cost coefficients closing the loop to the KBS cost model). 7. Δ-window unification of virtual commissioning, shadow-mode and look-ahead in one coordinator.

# §10 OPEN AMBIGUITIES & GATES (never assume)
G1 true axis ranges (v2 vs v3) · G2 write-echo fix approval · G3 per-machine safe states · G4 plan arg contract with Planner · G5: TIA project availability (SiL-A), Virtuos OPC UA connector availability/mode (MiL-geo), confirm 4842 = Nerve Data Gateway aggregation, thesis-plan format detail; HiL wiring for this lab undefined; barrier has no position sensors (timed 10 s actuation) until wired.

## Glossary
**Masterplan/subplan** plan files (§7) · **service** auto-discovered agent method = skill · **write-and-verify** write + readback-confirmation pattern · **anchor point** designated node compared across worlds/runs · **ExecutionContext** named (endpoint, mode, envelope) target world · **MiL-behave** Python behavioral plant (§4.4) · **MiL-geometric** Virtuos context · **SiL-A/B** real-logic virtual controllers (PLCSIM / 2nd CODESYS) · **Δ window** permission distance between virtual and physical cursors · **capsule** machine-state snapshot attached to errors/holds · **pedigree** hash-bound validation history of a plan · **safing** driving to a declared safe state (≠ rollback) · **golden plans** regression suite of known-good plans + expected anchor trajectories · **invariant distillation** learning restrictive pre-flight warnings from DT rejections.
