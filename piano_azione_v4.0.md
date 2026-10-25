# ACTION PLAN v4.0 — System Executor (CIRC4Me Pilot 1)
**rev. 2, 2026-07-07 — full-detail edition.** Supersedes `current_piano_azione_v3.2.md` (kept for history).

> Self-contained implementation plan, executable by a fresh Claude session (Opus-class) with no prior context.
> **Read first:** `architecture_v4_full_description.md` (§ references: W* = weaknesses §2, module designs §4) and `CIRC4Me_Pilot1_Contesto_Visione.md`. Research grounding + paper roadmap: `literature_reviews_summary.md`.

---

## RULES FOR ANY EXECUTING SESSION (non-negotiable)
1. **NEVER run project entry points (server, agents, observers, plans) without Giorgio's explicit per-instance approval** — the server lifespan connects to the real PLC (`opc.tcp://192.168.0.200:4842`); agents can physically move machines. Allowed without asking: reading, editing, `python -m py_compile`, and PLC-free unit tests (stdlib `unittest`, temp SQLite, no sockets to non-localhost, no asyncua connections).
2. Never modify the agent-side write-and-verify pattern. The server-side echo fix (A.6) strengthens it and is allowed **only after gate G2**.
3. Never weaken/remove hardware range limits in agent constructors; values change only per gate G1.
4. Masterplan `.txt` backward compatibility — all format changes additive.
5. `/ws` (control) stays isolated from `/ws/ui` (observation).
6. Hardware ambiguity → flag to Giorgio; never assume.
7. One item at a time; tests written alongside; unexpected issue → STOP and report; git commit per item (`A.1: <summary>`); never modify more than one logical layer per step; preserve existing comments unless factually wrong (codebase comments are Italian — keep the style). **Follow the MASTER SEQUENCE in "Execution order, roles & checkpoints": HV-*/FR-* checkpoints are plan items — when one is reached, STOP, prompt the named actor with the template, and only continue with the listed parallel-safe items.**
8. Never justify a choice by citing the lab's own documents as authority — technical merits only.
9. Tag findings/decisions: `[LIT: key] [CONTRA: key] [GAP-FILL] [ORIG] [ARBITRATED]`.
10. After each completed PHASE, output the phase report:
```
═══ PHASE [X] EXECUTION COMPLETE ═══
Items implemented: [...] | Tests written: N | Passing: N
Files modified: [...] | Limitations introduced: [...] | Recommended next: [...]
```

## ⚖ GIORGIO GATES
| Gate | Question | Blocks | Status |
|---|---|---|---|
| G1 | True physical axis ranges (v2: z≤270, prs≤1000, x-vel≤100 · v3: z≤600, prs≤1500, x-vel≤500). Which is the machine? | range values in canonical agent | **OPEN** — keep v3 values + `# TODO(G1)` marker |
| G2 | Approve write-echo removal in `opcua_core.write()` | A.6 | **OPEN — do not implement A.6 until approved** |
| G3 | Define "safe state" per machine (axis park positions, press retract, screwdriver off?) | F.5 | OPEN |
| G4 | Plan arg contract: positional CSV (code today) vs `param=value` (old docs) — align with upstream Planner | format evolution | OPEN — positional assumed |
| G5 | TIA project available for PLCSIM Advanced? Virtuos OPC UA connector licensed (server mode)? Confirm 4842 = Nerve Data Gateway. Thesis-plan format detail | G.2–G.4 | OPEN |

---

# EXECUTION ORDER, ROLES & CHECKPOINTS
**This section governs the whole plan. The executing model (Opus) follows the Master Sequence below and STOPS at every checkpoint, prompting the right actor with the given template. Checkpoints are plan items: they appear in the ledger and have dependencies like any other item.**

## Actors
- **Opus (executing session):** implements items in order; runs ONLY PLC-free tests; updates the ledger + commit per item; at each checkpoint stops and prompts. While a checkpoint is pending, works ONLY on items marked "parallel-safe" for that checkpoint.
- **Giorgio:** answers gates (decisions), performs HV checkpoints (hardware/lab actions) following the scripts below. Nobody else ever runs entry points.
- **Fable (separate review session):** reviews risk-concentrated diffs at FR checkpoints. Opus prepares the review package; Giorgio pastes it into a Fable session and brings findings back.

## Checkpoint prompting templates (Opus uses these verbatim)
- **To Giorgio (gate):** `🟡 GATE Gx NEEDED — question: <text>. Blocks: <items>. I will meanwhile continue with: <parallel-safe items>.`
- **To Giorgio (hardware):** `🔴 CHECKPOINT HV-n REACHED — your presence needed (~<duration>). Follow script HV-n in piano_azione_v4.0.md. Blocking: <items>. Parallel-safe work I'll continue: <items>. Preconditions all green: <checklist>.`
- **For Fable (review):** `🟣 CHECKPOINT FR-x — please open a Fable session and paste: "Review commits <range> in C:\...\OPCUA_Control_Architecture_v6. Context: architecture_v4_full_description.md §<n>, piano_azione_v4.0.md item(s) <ids>. Focus: <focus list>. Report findings as CONFIRMED/PLAUSIBLE with file:line and a failure scenario each; flag anything that weakens write-and-verify, range limits, or abort semantics."` Opus applies CONFIRMED findings, discusses PLAUSIBLE ones with Giorgio, and re-runs the test suite.

## MASTER SEQUENCE (implementation order with blocking semantics)
```
HV-0 (G1+G2 decision session — 15 min, desk)  ← do FIRST or in parallel with A.0–A.2; HARD-BLOCKS HV-1 and A.6
A.0 → A.1 → A.2 → A.3 → A.4 → A.5 → A.6(only if G2=yes) → A.7 → B.1
  → FR-A (Fable reviews Phase A diff; BLOCKING for HV-1)
  → HV-1 (lab session ≈2h; BLOCKING for: C.7 baselines, G.1 data, any physical run)
      parallel-safe while waiting for FR-A/HV-1: B.2 B.3 B.4 B.5 B.6 B.7, E.1, PROTOCOL.md
B.2–B.7 → C.1 → C.2 → C.3 → C.4 → C.5
  → FR-C (gateway refactor + MiL-behave semantics; BLOCKING for HV-2)
  → HV-2 (approval, may be remote, ~15 min; BLOCKING for any MiL-behave execution)
C.6 → C.7 (consumes HV-1 recordings) → C.8 → C.9 → C.10
E.2–E.8 (anytime after B; parallel-safe with C and D)
D.1 → D.2 → D.3 → FR-D (reconnect/resume idempotency; BLOCKING for HV-3) → HV-3 (lab ≈45 min) → D.4 → D.5 → D.6 → D.7
F.1 → F.2 → F.3 → F.4 → FR-F1 (HOLD/resume contract) → [G3 via HV-4a] → F.5 → FR-F2 (safing) → HV-4b (safing witness session) → F.6
[G5 via HV-5 lab setup] → G.1 → G.2 ∥ G.3 ∥ G.4 → G.5 → HV-6a (approve stage-1 use) → FR-G (G.6 design review BEFORE implementation) → G.6 → G.7 → G.8 → HV-6b (look-ahead demo)
```
**Blocking rules:** an item may start only when everything left of it on its chain is done, EXCEPT items listed parallel-safe for a pending checkpoint. Opus never performs an HV itself and never skips an FR.

## FABLE REVIEW CHECKPOINTS (FR) — what each focuses on
| FR | After | Focus (why Fable and not self-review) |
|---|---|---|
| **FR-A** | A.7+B.1 | A.3 supervisor wait rework (queue-per-correlation, ack/liveness races, abort interleavings — the subtlest async surgery in the plan); A.1 stale-feedback paths; A.6 if implemented (verify-chain adjacency); A.2 path-confinement bypasses |
| **FR-C** | C.5 | Gateway refactor completeness (no OPC path left in broker), ctx refusal logic, C.3 namespace translation, MiL-behave state-machine edge cases (step_enable toggling mid-motion, write-latency vs verify race), state-injection blocked on physical |
| **FR-D** | D.3 | Reconnect storms, duplicate-execution risk on resume (idempotency per reversibility class), half-open sockets, event-log consistency across reconnects |
| **FR-F1/F2** | F.4 / F.5 | HOLD/resume contract vs KBS (capsule completeness, tail-validation bypasses); safing ladder (can SAFE-STOP itself fail? ordering, re-entrancy) |
| **FR-G** | before G.6 coding | Design review of permission-window protocol, divergence thresholds, resync procedure — cheaper to fix on paper |
On-demand: Opus may request an extra Fable review whenever a change touches write-and-verify, ranges, abort/safing, or when a test cannot be made PLC-free.

## GIORGIO CHECKPOINTS (HV) — detailed scripts

### HV-0 — Decision session (15 min, desk, do first)
1. **G1 ranges:** open `archive/disassembly_machine_v2.py` vs `src/agents/resources/disassembly_machine_v3.py`, compare the `ranges` blocks. Evidence hint: DEMO/DENSO plans command z=530–571.6 and ran on the machine, which suggests v3 (z≤600) is right and v2 (z≤270) is stale — but only you know if those runs really executed or crashed. Answer per axis: target min/max, vel/acc/dec max. Tell Opus: "G1: v3 correct" or provide corrected numbers → Opus edits the constructor + removes the TODO(G1) marker (this is the ONE permitted range edit, rule 3).
   ⚠ G1 is a HARD BLOCK for HV-1: running plans with too-wide limits risks physical overtravel.
2. **G2 write-echo:** decision. Recommendation on record: YES (it makes the documented verify property true; agent code untouched; cost ≤100 ms per write). If yes → Opus implements A.6 in sequence. If unsure, say "defer" — everything else proceeds, SET_PARAMS verification stays cosmetic until then.
3. Optionally G4 (plan arg style) if you've spoken with the Planner side; otherwise leave open.

### HV-1 — Stabilization lab session (~2 h, machine powered, area clear)
**Preconditions (Opus confirms all green in its prompt):** G1 closed; FR-A findings applied; all Phase A+B.1 tests passing; ledger updated; fixture plans present in `plans/hw_checkpoint/` (Opus prepares: `hv1_invalid_range.txt` with one out-of-range target; `hv1_runfile.txt` master+subplan >60 s total; plus you'll use existing RAKUN induzione).
**You do, in order (all launches from the UI):**
1. Start, in 4 terminals: server (`python src/server/main.py`), agent v3, supervisor, one observer. Open UI. ✅ Expect: resources ONLINE, supervisor badge ONLINE, no errors in Log panel.
2. **Validation refusal:** launch `hv1_invalid_range.txt`. ✅ Expect: refused BEFORE any motion ("validation_failed" with line number). ❌ If ANY axis moves: hit Abort, end session, report "HV-1 step 2 FAILED" to Opus.
3. **Long-step proof (W1):** launch RAKUN induzione. ✅ Expect: the slow x move (~36 s) completes with PROGRESS updates and NO false timeout/abort.
4. **RUN_FILE proof:** launch `hv1_runfile.txt`. ✅ Expect: ACCEPTED, per-step progress, total >60 s, completes.
5. **HOLD/RESUME:** relaunch step-4 plan; press ⏸ Hold mid-run. ✅ Expect: current step finishes, status "holding", machine still; ▶ Resume continues to completion.
6. **Honest ABORT:** relaunch; press ■ Abort mid-step. ✅ Expect: confirm dialog with the honest wording; in-flight step completes; nothing further dispatched; UI says exactly that.
7. **(only if A.6 done)** run a SET_PARAMS-heavy plan (any DENSO). ✅ Expect: normal completion; no perceptible slowdown.
8. **Wrap-up (important):** note the run_ids shown in the UI for steps 3–4; copy `data_log.db` to `data_log_backup_HV1.db`. These recordings become the C.7 golden baselines and G.1 calibration data — this is why B.1 ran before this session.
**Report to Opus:** "HV-1 PASS" or "FAILED at step N, run_id X, observed: …". On failure Opus stops feature work and triages (with Fable if async-related).

### HV-2 — MiL-behave execution approval (~15 min, may be REMOTE)
Purpose: authorize the first execution of entry points against the VIRTUAL context only. **Precondition (Opus states explicitly):** C.2 implements a `physical_enabled=false` startup mode so server+agents+MiL-behave run with ZERO possibility of PLC contact (verify: `OPC_SERVER_URL` unused, no socket to 192.168.0.200). FR-C passed. You reply: "HV-2 approved: virtual-only runs authorized until revoked" (a standing approval — Opus may then run MiL-behave test suites autonomously). Optionally later, visit the lab once to see C.9: the digital shadow mirroring a virtual run in 3-D (pure joy, no risk).

### HV-3 — Resilience lab session (~45 min)
Preconditions: FR-D applied; D.1–D.3 tests green on MiL-behave. Use a motion-light plan (WAIT-heavy fixture `hv3_soft.txt`).
1. Mid-run, kill the agent process (Ctrl+C). ✅ Expect: supervisor reports the drop within seconds (not 30 min); agent restarted → reconnects, re-registers, resync_report visible; plan resumes or HOLDs per D.3 policy — verify NO step executed twice (check event log).
2. Briefly unplug/replug the PLC network path. ✅ Expect: gateway reconnects, nodes re-resolve, poller resumes; quarantine list empty afterward.
3. Kill and restart the SERVER mid-plan. ✅ Expect: agents+supervisor reconnect with backoff; system reaches a coherent idle/HOLD state; no ghost execution.

### HV-4 — Safety definition + safing witness
**HV-4a (desk, ~30 min, gate G3):** write, per machine, the safe state: axis park positions (or "hold in place"?), press retract height, screwdriver state, barrier state; note which are position-dependent. Give the table to Opus → F.5 implements `service_safe_state` from it.
**HV-4b (lab, ~60–90 min, MANDATORY presence — this is safety):** trigger SAFE-STOP from ≥3 different plan situations you choose (e.g., mid XY travel; press partially extended at low speed; screwdriver active). ✅ Expect: declared safe state reached each time, events logged, UI ladder (HOLD/STOP-DISPATCH/SAFE-STOP) truthful. Also re-verify honest-abort wording end-to-end. Reminder: hardware E-stop remains the physical chain — software never claims it.

### HV-5 — Phase-G lab setup (your hands, spread over days; gate G5)
1. Confirm endpoint identity: is `192.168.0.200:4842` the Nerve Data Gateway aggregated server? (Check Nerve MS config.) 2. Export/locate the MULLUTENSIL TIA project; check CPU OPC UA license availability; install/verify PLCSIM Advanced ≥ v4 + TIA ≥ V16. 3. Check ISG Virtuos license for the OPC UA connector (server mode) and that the digital shadow currently consumes OPC UA from the gateway. 4. Ask TTTech-side: can a second CODESYS instance (or second Nerve VM) run the DOOSAN/SEIT app sandboxed? 5. Answer the thesis-plan-format question (was the Virtuos MiL consuming the same masterplan text?) — refines G.1 regression checks.

### HV-6 — Coordinator acceptance
**HV-6a (~30 min):** review the first G.5 validation report on a real plan (virtual verdict vs your expectations); approve decision-support usage. **HV-6b (demo, ~1 h):** look-ahead run with small Δ on a benign plan; provoke a virtual failure (fault-injection) → watch physical HOLD at last validated step; verify resync; sign off stage 2.

## CURRENT-STATE AUDIT (2026-07-07)
Implemented from v3.2 (verified in code): 0.1 error propagation + single-feedback `_send_error`; 0.2 feedback timeout (wrong semantics → A.3); 0.3 agent-side range validation (v2 AND v3); 0.4 heartbeat (agents+supervisor, `last_seen`, UI grace); 1.0–1.6 full web UI + observers + `data_log.db`; 2.6 partial (source filters). `RETRY_ATTEMPTS` zombie already removed.
Defects W1–W18 fully specified in architecture doc §2 — **read §2 before Phase A**. Canonical agent = `disassembly_machine_v3.py` (docs previously pointed at v1/v2 — A.0 fixes). No git repo yet. `.gitignore` already created at root. Three docs (this + architecture + literature) exist at root.

---

# PHASE A — CRITICAL STABILIZATION (~7 days)
**Sequencing rationale:** identity first (A.1 — everything else correlates through it), then plan integrity (A.2 — gives tests a refusal path), then execution semantics (A.3), then concurrency guards (A.4), then routing robustness (A.5); A.6 gated; A.7 makes abort honest. Safety fixes precede ALL feature work regardless of old phasing.
**Entry:** prompt 🟡 HV-0 (G1/G2) on day 1 — G1 HARD-BLOCKS HV-1; G2 blocks only A.6. **Exit:** A.7 → B.1 → 🟣 FR-A → 🔴 HV-1. **Parallel-safe while FR-A/HV-1 pend:** B.2–B.7, E.1, PROTOCOL.md.

### A.0 Repository + agent-version consolidation (fixes W11 + repo debt)
**Effort: S** | **Files:** repo root, `src/agents/resources/`, `CLAUDE.md` | **Depends:** —
**Steps:** (1) `git init`; verify `.gitignore` covers `venv/ __pycache__/ *.pyc src/ui/node_modules/ src/ui/dist/ *.db logs/ versions/`. (2) Baseline commit of the untouched tree FIRST (v1/v2 preserved in history). (3) `mkdir archive/`; `git mv src/agents/resources/disassembly_machine.py archive/` (v1 — contains a debug override of `write_and_verify`: must not remain importable under `src/`); `git mv src/agents/resources/disassembly_machine_v2.py archive/`. (4) `CLAUDE.md`: canonical agent = v3 (fix run instructions), action-plan pointer = `piano_azione_v4.0.md`, add rule 1 (never-run). (5) In v3 constructor add a comment block: `# TODO(G1): range values provisional — v2 declared different limits (z 270/prs 1000/vel 100); Giorgio must confirm physical truth.`
**Edge cases:** nothing may import v1/v2 (grep `disassembly_machine[^_]` and `_v2`); `plans/masterplan_example.txt` references the OLD project's absolute path — leave file, it becomes a pre-flight test fixture for A.2's path confinement.
**Test:** `py_compile` every `src/**/*.py` + `config/*.py`; grep gates above; `git log` shows baseline + A.0.

### A.1 Typed message envelope + correlation IDs (fixes W4-correlation; enables A.3/A.5) `[LIT: SiLA2/LAP; FIPA conversation-id]`
**Effort: M** | **Files:** new `src/utils/protocol.py`; `api_server.py`; `base_agent.py`; `system_agent.py` | **Depends:** A.0
**protocol.py spec:**
```python
new_id() -> str                    # uuid4().hex[:12]
stamp(payload: dict, source: str, correlation_id=None, run_id=None) -> dict
    # adds msg_id, ts (time.time()), source; adds correlation_id/run_id only if not None
# feedback statuses:
ST_ACCEPTED="ACCEPTED"; ST_PROGRESS="PROGRESS"; ST_DONE="SUBPLAN_COMPLETED"; ST_ERROR="ERROR"
# error taxonomy (A.5/D.4 retry policy: only COMMS retriable):
ERR_VALIDATION, ERR_RANGE_AGENT, ERR_RANGE_DB, ERR_COMMS, ERR_HW_TIMEOUT,
ERR_BUSY, ERR_UNKNOWN_NODE, ERR_DISPATCH_FAILED, ERR_STALE_FEEDBACK, ERR_NO_ACK
```
**Wiring:** supervisor: per-run `run_id=new_id()`; per-dispatch `correlation_id=new_id()` placed INSIDE `payload` (agents echo it back); waiting structures keyed by correlation_id (full rework lands in A.3 — here: key the existing future dict by correlation instead of resource name). Server `feedback` branch forwards: `resource,status,message,correlation_id,run_id,error_type,step,total` (dict-comprehension over allowed keys). Agent `_send_feedback(status, message=None, *, correlation_id=None, error_type=None, step=None, total=None)`; `execute_sequence` receives the correlation_id from the command payload and echoes it in every feedback.
**Backward compatibility:** all fields additive; supervisor logs uncorrelated feedback as `STALE_FEEDBACK` warning and drops it (it must NEVER resolve a wait — this kills the ghost-unblock race).
**Edge cases:** duplicate terminal feedback (idempotent — second is stale); feedback arriving after timeout-abort (stale by definition: its correlation entry was removed).
**Test (PLC-free, `tests/test_protocol.py`):** stamp adds/omits fields correctly; ids unique; constants exported. Integration behavior covered by A.3's fake-agent tests.

### A.2 Whole-plan pre-flight validation — the end of silent skips (fixes W3, W14; completes v3.2 1.3) `[LIT: RP-check]`
**Effort: M** | **Files:** `src/utils/parser.py`; `src/server/db_manager.py`; `src/agents/system_agent.py` | **Depends:** A.1
**db_manager:** add `get_service_ranges(resource, service) -> dict` (parse `ranges_json`); extend `get_all_resources_schemas()` service values to `{"params":[...], "ranges":{...}}` — audited consumers (`system_agent` `list`, UI ResourcePanel) only use `.keys()`, safe; replace the bare `except Exception: pass` with logged error + re-raise-safe empty result distinguishable from "no resources" (log line mandatory).
**parser:** new `validate_and_parse_line(line, resource) -> (step|None, error:str|None)` — existing behavior + range validation: for each param `p`: if `ranges[p]` is a list → membership check (selector, e.g. axis); if `ranges[f"{p}_map"]` exists and the selector's value is known → `min ≤ float(v) ≤ max` (ValueError on non-numeric → error). New `validate_masterplan(path) -> {"run_steps":[{target, payload, line_no, service}...], "errors":[{line_no, text, error}...], "total_steps":N}`: iterates the masterplan; direct commands validated per above; `RUN_FILE`: resolve against `PLANS_DIR` ONLY — reject absolute paths and any path escaping PLANS_DIR (`os.path.realpath` prefix check) — then recurse-validate every subplan line; empty/comment-only subplan = error. Keep old `parse_master_line`/`parse_line_with_schema` as thin wrappers (other callers unaffected).
**system_agent:** `execute_masterplan` calls `validate_masterplan` FIRST. If `errors`: log each with line numbers, `_send_progress(status="validation_failed", errors=[...], total=total)`, **return without dispatching anything**. Execution iterates `run_steps` (already-parsed) — mid-run parsing disappears, so the silent-skip class is structurally dead. Keep the pre-scan step count consistent with `total_steps`.
**Edge cases:** resource offline/not in DB → validation error ("resource not registered — is the agent running?"); WAIT has no ranges (params-count only); numeric strings like `"1e5"` (no dot) previously parsed as str — treat as error if a `_map` exists for that param; `masterplan_example.txt` absolute RUN_FILE must be REFUSED (fixture!).
**Test (`tests/test_preflight.py`, PLC-free, temp SQLite via `settings.DB_PATH` override):** register fake resource schema incl. ranges+maps → good plan passes with correct `total_steps`; each failure mode above yields an error with the right `line_no`; the "DEMO plan against v2 schema" scenario (ENGAGE unknown) → REFUSED, zero `run_steps` consumed.

### A.3 ACK/completion split + liveness timeouts (fixes W1; upgrades v3.2 2.1; delivers B.6 events) `[LIT: SiLA2 observable commands]` `[CONTRA: single static timeout]`
**Effort: M** | **Files:** `base_agent.py`; `system_agent.py`; `settings.py` | **Depends:** A.1
**Agent:** `execute_sequence(steps, correlation_id)`: (1) immediately `_send_feedback(ST_ACCEPTED, correlation_id=…)`; (2) before each step `_send_feedback(ST_PROGRESS, step=i+1, total=n, message=service_name, correlation_id=…)`; (3) terminal `ST_DONE` or `ST_ERROR(error_type=…)`. Unknown wrapper action → typed ERROR (not just a warning log).
**Supervisor:** replace `pending_feedbacks[target]=Future` with `self.pending[correlation_id] = asyncio.Queue()`; `listen_for_messages` pushes any feedback with known correlation into its queue. Per step: `await queue.get()` with `ACK_TIMEOUT=5.0` → missing/ERROR(BUSY/DISPATCH_FAILED) ⇒ step fails fast (`ERR_NO_ACK` / propagated type); then loop: `await queue.get()` with `PROGRESS_LIVENESS_TIMEOUT=60.0` per wait — every PROGRESS resets the clock, terminal ends the loop; absolute cap `EXECUTION_TIMEOUT_MAX=1800.0` from step start ⇒ `ERR_HW_TIMEOUT`. Abort integration: `asyncio.wait({queue.get(), abort_event.wait()}, FIRST_COMPLETED)` per wait cycle (cancel losers; pop pending entry in `finally`).
**settings.py:** add the three constants; comment-deprecate `AGENT_RESPONSE_TIMEOUT` ("superseded by ACK_TIMEOUT — kept for reference").
**Why (for the record):** the 30 s wait conflated "agent alive" with "work done": RAKUN-induzione's `x` at vel 10 → MOVE ≈36 s falsely aborted; ANY multi-step RUN_FILE (one terminal feedback) broke; supervisor "aborted" while the machine continued (split-brain). Liveness now comes from progress+heartbeat; wall-clock is only a last-resort cap.
**Edge cases:** PROGRESS after terminal → stale-drop; agent ACKs then dies → liveness timeout with honest message ("no progress for 60 s"); two feedbacks racing abort → abort wins, feedback becomes stale.
**Test (`tests/test_exec_semantics.py` + `tests/fake_agent.py`, PLC-free, localhost-only):** fake agent = plain `websockets` client registering a fake resource, scriptable per-step durations/failures. Scenarios: 5-step 2-minute sequence completes; ack-silence 6 s → NO_ACK ≤7 s; death after step 2 → liveness timeout ≈60 s (not 30 min); late terminal after abort → STALE logged, next run unaffected. *(These tests open localhost sockets only; still ask Giorgio before first run per rule 1 if in doubt.)*

### A.4 Single-active-plan lock + agent busy flag (fixes W4-lock, W8) `[LIT: holonic resource ownership]`
**Effort: S** | **Files:** `system_agent.py`; `api_server.py`; `base_agent.py` | **Depends:** A.1
Supervisor: `self.active_run` guard — `launch_plan` while set → `_send_progress(status="rejected_busy", run=self.active_run)`; cleared in `finally`. Server: module-level `current_execution` dict updated from every `progress_event` (plan, run_id, status, step, total, ts); REST `GET /execution/current` returns it (UI rehydration = B.5). Agent: `self._busy` — overlapping `execute_subplan` → immediate `ST_ERROR/ERR_BUSY` with the NEW correlation_id; running sequence untouched; cleared in task done-callback (exception-safe).
**Test:** second launch during fake run → `rejected_busy`; overlapping dispatch → BUSY while first completes normally.

### A.5 Dispatch robustness + typed routing errors (fixes W6, W7, W13) `[LIT: Leitão failure modes]`
**Effort: M** | **Files:** `api_server.py`; `base_agent.py` | **Depends:** A.1
Server: `dispatch_command` — target missing OR `send_json` raises ⇒ reply to SENDER `{"type":"feedback","resource":target,"status":"ERROR","error_type":ERR_DISPATCH_FAILED,"correlation_id":payload.get("correlation_id"),"message":...}` (supervisor's queue path handles it uniformly; connection never unwinds). Unknown node on subscribe/read/write ⇒ `{"type":"error","error_type":ERR_UNKNOWN_NODE,"node":name}`. Extract `_cleanup_connection(name, ws)` and call it from BOTH `WebSocketDisconnect` and generic `Exception` handlers (keep the existing anti-zombie active-socket check).
Agent: handle `type=="error"` with `error_type==UNKNOWN_NODE`: set exception on `pending_responses[node]` and `__write__<node>` futures → `verify_target`/`write_and_verify` fail in milliseconds with the true cause instead of a 360 s TimeoutError.
**Test:** kill fake agent between register and dispatch → DISPATCH_FAILED ≤1 s, supervisor alive; fake agent reads a typo'd node → UNKNOWN_NODE error surfaces in the step ERROR.

### A.6 Write-echo removal — **GATED G2. Do not implement until approved.** `[LIT: Simplex]` (fixes W5)
**Effort: S** | **Files:** `opcua_core.py`
Change: `write()` performs the typed write and returns success/failure ONLY — no `self.cache[...] = value`, no `_notify_subscribers(...)`; the 100 ms `_data_poller` readback remains the sole source of cache updates and notifications. Consequence: `verify_target` sees PLC truth; SET_PARAMS verification becomes real; verify latency +≤1 poll cycle.
**Test:** unit with a mock client that ACKS writes but never changes the read value ⇒ `verify_target` must TIME OUT (today it false-passes — that failing-then-fixed test is the proof of W5); end-to-end via MiL-behave fault `ack_without_apply` (C.6).

### A.7 Honest abort + HOLD groundwork (fixes W2 minimally; full safing = F.5/G3) `[LIT: JPL-FDIR abort levels]`
**Effort: M** | **Files:** `system_agent.py`; `api_server.py`; `src/ui/src/components/PlanLauncher.jsx` | **Depends:** A.3
Supervisor: `self._hold_event`; before dispatching EACH step: if hold set → emit `status="holding"`, wait for resume/abort. UI commands via server: `hold_plan`, `resume_plan` (add to `/ws/ui` handler, forwarded like abort). Abort semantics unchanged (stop dispatch after in-flight step) but ALL wording becomes honest: progress event `status="aborted", message="in-flight step on <target> runs to completion — machine NOT stopped"`. Agent: `cancel_requested` flag set by a new lightweight `cancel` command; checked BETWEEN steps of a subplan (never mid-write) → terminal `ERROR/ABORTED_BY_REQUEST` at the next boundary.
UI (PlanLauncher): add ⏸ Hold / ▶ Resume next to Abort; Abort gets a confirm dialog with the honest sentence above.
**Test:** fake-agent 10-step subplan: HOLD pauses at boundary (progress shows holding), RESUME continues, ABORT stops dispatch with honest message; cancel command ends fake subplan at next boundary.

---

# PHASE B — OBSERVABILITY BACKBONE (~4 days)
*Rationale: every later phase (golden plans, duration models, coordinator ledger, papers P1/P5) reads from this.*
**Ordering note:** B.1 executes BEFORE FR-A/HV-1 (its recordings are the HV-1 payoff: golden baselines + calibration data). B.2–B.7 are the designated parallel-safe work during the FR-A/HV-1 wait.

### B.1 Execution event log `[LIT: event-sourcing JSS-2021; XES]` `[GAP-FILL: execution datasets]`
**Effort: M** | **Files:** new `src/server/event_log.py`; `api_server.py` hooks | **Depends:** A.1
`execution_events(id INTEGER PK, run_id TEXT, ts TEXT, source TEXT, event_type TEXT, step INTEGER, payload_json TEXT)` in `data_log.db` (never reset). Single writer = the server (it already sees dispatch/feedback/progress; add hooks in those branches). Event types: `run_started, validation_failed, dispatched, accepted, progress, step_done, step_error, held, resumed, aborted, run_finished`. Reader API: `get_run(run_id)`, `list_runs(limit)`.
Test: scripted fake run → complete ordered stream; `list_runs` pagination.
### B.2 Error context capsule `[LIT: RemoteAgent-Livingstone; ESA safe-mode lessons]` — **M** — agent keeps a small ring buffer of last N received updates + a dict of last-known node values; on ERROR attach `capsule={"values":…, "recent_updates":…, "step":…}` to the feedback; server logs it into the event log. Test: fake failure carries capsule.
### B.3 Structured log payloads `[LIT: XES]` — **S** — `log_event` gains optional `run_id, step, event` fields (WSLogHandler enriched via contextvars or explicit calls at key points); terminal formatting unchanged.
### B.4 Data-path hygiene (fixes W14 remainder, W17-perf) — **S** — index `CREATE INDEX IF NOT EXISTS idx_datalog ON data_log(observer, id)`; `/data/recent` uses `ORDER BY id DESC LIMIT ?` then reverses; document data_log growth policy (no auto-delete; export+archive manual).
### B.5 UI rehydration (fixes W15/refresh) — **S-M** — PlanLauncher/PlanMonitor fetch `GET /execution/current` (+ event-log tail endpoint `GET /execution/{run_id}/events`) on mount; `isRunning` from server truth; PlanLauncher also re-polls `/resources` on an interval (same cadence as ResourcePanel) for the pre-launch guard.
### B.6 Sub-step progress in UI — **S** — PROGRESS events (emitted since A.3) rendered as "step k.i/n" nested lines in PlanMonitor.
### B.7 Log-handler lifecycle (fixes W16) — **S** — before adding WSLogHandler remove any previous instance for the same source; UILogHandler detached when `ui_clients` empties.

# PHASE C — PLANT GATEWAY & MiL-behave (~8 days)
*Architecture: §4.2–§4.5 of the architecture doc. Rationale: mechanism/policy split; MiL-behave unlocks hardware-free everything.*
**Checkpoints:** after C.5 → 🟣 FR-C → 🔴 HV-2 (virtual-only execution approval; remote OK) — **no MiL-behave execution before HV-2**. C.7 consumes HV-1 recordings (blocked until HV-1 passed). C.9 lab-side re-pointing of the shadow = Giorgio (no deadline; demo-driven).

### C.1 Plant Gateway extraction `[ARBITRATED: one function per module]` (fixes W18)
**Effort: M** | **Files:** new `src/server/plant_gateway.py`; `api_server.py`; `main.py`
Move OPCUAManager ownership + the `subscribe/read/write/unsubscribe` handling out of `api_server.py` into a `PlantGateway` class: `read(node_name, ctx="physical")`, `write(node_name, value, ctx)`, `subscribe(node_name, cb, ctx)`, `unsubscribe(...)`; friendly-name→id resolution inside the gateway (per context after C.3). Broker calls the gateway; no behavior change yet (single context). Kill the duplicate top-level `from opcua_core import ...` import (W18). `main.py` builds the gateway in lifespan; `app.state.plant_gateway`.
Test: full fake-agent regression from Phase A stays green (imports/py_compile; A.3 test suite re-run).
### C.2 ExecutionContext registry `[LIT: VC-review-2023; shadow-mode authority]` — **S-M** — `settings.EXECUTION_CONTEXTS = {"physical": {"url": OPC_SERVER_URL, "mode":"PHYS", "envelope":["reality"]}}` (+virtual entries later); optional `ctx` on subscribe/read/write/dispatch (default "physical"); when >1 context configured, ctx-less commands are REFUSED (`ERR_VALIDATION`); run records + data_events ctx-stamped; gateway lazily instantiates one manager per context. **Mandatory: `physical_enabled` startup flag — when `false`, the physical context is never instantiated and no socket toward the PLC can be opened (verify: no connection attempt to `OPC_SERVER_URL` anywhere). This flag is the precondition that makes HV-2's standing approval and CI runs zero-risk.**
### C.3 Namespace-robust resolution `[ORIG — ns indices are server-local; PLCSIM/CODESYS renumber]` — **S-M** — resolve per-context: read the server's NamespaceArray, translate node_map ids by namespace URI where possible; fallback = per-context override map `config/node_map_<ctx>.py` generated from the master map. Document the trap loudly in node_map.py header.
### C.4 Per-context poller/cache isolation `[LIT: shadow non-interference]` — **S** — poller task, cache, subscriber sets instantiated per context (falls out of C.1 class design); UI dashboards can filter by ctx.
### C.5 MiL-behave virtual plant `[LIT: SIMIT/WinMOD class; LoD-2015]` `[ARBITRATED: thesis plant layer reborn; name by Giorgio]`
**Effort: M-L** | **Files:** new `src/virtual/mil_behave.py` (+ `src/virtual/components.py`)
asyncua **Server** exposing the same friendly node set (namespace URI `urn:circ4me:mil-behave`): per-component state machines —
`ElectricalAxisModel`: `IDLE --step_enable↑ (target=pos_step)--> MOVING --|pos-target|≤ε--> IN_POSITION --step_enable↓--> IDLE`; MOVING integrates `pos_attuale` on a trapezoidal profile from the CURRENT vel/acc/dec node values (default parameters loaded from the canonical agent's declared ranges — import the agent class, read `axes[*].ranges`; SSoT). `AirAxisModel`: pos1_step↑ → after `actuation_delay` set pos1_attiva/clear pos0_attiva (and mirror); `BarrierModel`: timed transition only. Global `write_latency` parameter (default 20 ms) between accepted write and visible value change — the honest version of the thesis `count==100` debounce. **State injection API** (`set_state(node,value)`, exposed as an OPC UA method or side TCP endpoint) from day one — the resync primitive `[LIT: online-sim-review]`; the Plant Gateway hard-blocks state-injection on ctx=physical.
Validity envelope: `["logic","sequencing","timing-approx"]` — NEVER collision (that's MiL-geometric/Virtuos).
Test: with Giorgio's approval to run locally: server main pointed at ctx=MiL-behave, real agent + supervisor processes, every plan in `plans/` executes green end-to-end; assert final pos_attuale per axis == plan targets.
### C.6 Fault-injection library `[LIT: JPL testbed fault injection]` (upgrades v3.2 3.6) — **S-M** — scenario files (YAML/JSON) applied to MiL-behave: `stuck_axis(axis, at)`, `slow_drift(axis, rate)`, `sensor_flicker(node, period)`, `delayed_settle(axis, extra_s)`, `ack_without_apply(node)` ← the W5/A.6 proof. Chaos suite = scripted scenarios × golden plans.
### C.7 Golden-plan regression suite `[ORIG]` — **S-M** — `tests/golden/` = curated plans + expected anchor trajectories (recorded from a validated MiL-behave run, reviewed by Giorgio); CI job replays and diffs anchors within tolerances. Purpose: W-class regressions (silent skips, timeout conflations, echo bugs) detectable without hardware, before demo day.
### C.8 Anchor-point declaration `[LIT: anchor-points-2018]` — **S** — agents declare `self.anchors=[...]` in the constructor (e.g. every `pos_attuale`, key sensors, `mill_carico`); included in the registration schema + DB; consumed by C.7 diffs, conformance reports, G.6 divergence.
### C.9 ⭐ Digital shadow as virtual-run visualizer `[ORIG — Giorgio-favorite]` — **S** — the existing digital shadow consumes OPC UA; point it at the MiL-behave server (config parameter + short how-to in this repo) → free 3-D visualization of virtual runs, zero new modeling; also the demo artifact with zero machine risk. Executor-side deliverable: documented endpoint + stable namespace URI; lab-side re-pointing: Giorgio.
### C.10 Execution-target UI `[LIT: shadow-mode explicitness]` — **S-M** — PlanLauncher target dropdown (contexts from settings via REST); UNMISTAKABLE visual coding: amber page chrome + "VIRTUAL — <ctx>" banner for any non-physical ctx; red-accented confirm for physical; ctx badge on PlanMonitor and run history; ghost-run overlay: predicted per-axis position-vs-time (piecewise from plan targets+params) drawn under the live trace.

# PHASE D — RESILIENCE & SECURITY (~5 days; v3.2 Phase 2 carried & refined)
**Checkpoints:** D.1 → D.2 → D.3 → 🟣 FR-D → 🔴 HV-3 (45-min lab) → then D.4–D.7. **Parallel-safe during FR-D/HV-3 wait:** E-phase items.
### D.1 WS auto-reconnect (agents + supervisor) `[v3.2 2.2]` — **M** — exponential backoff 1,2,4,8…60 s (placeholder comments already in `base_agent.connect` and `system_agent.connect`); on reconnect: re-register AND send a `resync_report` (was a sequence in flight? which step?) so the supervisor reconciles instead of assuming `[LIT: RemoteAgent]`. Edge: WSLogHandler re-attach via B.7 logic.
### D.2 OPC UA reconnect per context `[v3.2 2.3]` — **M-L** — implement `_monitor_connection` in the gateway's manager: periodic health read; on failure reconnect with backoff and **re-run `_resolve_nodes`** (asyncua Node objects don't survive reconnection).
### D.3 Execution resumption `[v3.2 2.4]` — **L** — supervisor persists current run/step (event log is the source of truth); on both-sides-reconnected: re-dispatch policy by reversibility class — MOVE/SET_PARAMS idempotent (safe re-send); ACTIVATE-class requires a pre-retry state read; unknown class ⇒ HOLD for human.
### D.4 Selective retry `[v3.2 2.5]` — **M** — reintroduce `RETRY_ATTEMPTS` (settings) used in the supervisor around a failed step ONLY for `ERR_COMMS`-class errors (never VALIDATION/RANGE/BUSY); backoff between attempts; every retry logged as an event.
### D.5 Poller quarantine (fixes W10) — **S** — per-node try/except with failure counter; after N consecutive failures the node is quarantined (skipped, logged ONCE, listed in `/resources` health block); manual unquarantine via REST.
### D.6 Non-fatal node resolution (fixes W9/PG-3; prerequisite for DOOSAN/SEIT `[v3.2 4.4]`) `[LIT: FDIR isolation]` — **M** — `_resolve_nodes` collects failures instead of raising; unresolved nodes → quarantine list surfaced in UI + logs; agents whose nodes are ALL unresolved marked degraded; server starts regardless.
### D.7 Security quick wins (fixes W12) — **S** — shared token (settings/env) required in `register` and on `/ws/ui` connect; `GET /plans/{name}`: `os.path.basename` + whitelist ext; bind `127.0.0.1` default, `0.0.0.0` opt-in; (RUN_FILE confinement already in A.2).

# PHASE E — UI v2 (~6 days)
### E.1 Shared WS provider — **S-M** — one `/ws/ui` connection via React context; auto-reconnect with backoff + "DISCONNECTED" banner; `ws://`→derive from `location.protocol`.
### E.3 Pre-launch panel `[LIT: RP-check report]` — **M** — render the A.2 validation report per line (✓/✕ + reason), estimated step durations (naive: distance/vel until G.8's model), target-vs-current positions; Launch enabled only on all-green. *(This is the operator's "what is about to happen" view for one-of-a-kind plans.)*
### E.4 Observer-defined dashboards v2 `[ARBITRATED]` — **L** — implement dashboard_config v2 (schema in architecture doc §4.13): `group` sections (collapsible) of `preview` tiles (sparkline/stat/mini-scatter) on the main dashboard; click → **new tab** `/observer/{name}` rendering the observer-declared `detail` layout with observer-declared `controls` (time_window live/5m/1h/run · node_toggle · threshold_line · pause_resume · export_csv). React = generic interpreter; ZERO observer-specific code. BaseObserver default config auto-upgraded (v1 config → preview-only).
### E.5 HP-HMI restyle — **M** — design tokens (CSS vars), muted surfaces, color=state/alarm only, shared Card/Badge components, tabs Monitor/Log/Dashboard (absorbs v3.2 2.6), viewport meta for tablet.
### E.6 Log panel — **S-M** — source-side timestamps (from record), server-side ring buffer endpoint (survives refresh), text search box, export button; reconcile DEBUG (in colors but not filters).
### E.7 Data correctness+export (fixes W17-data) — **S** — scatter pairs by nearest timestamp (tolerance) instead of array index; `GET /data/export?observer&from&to&format=csv`.
### E.8 Armed-steps toggle `[ARBITRATED: enable/disable on the interface]` — **S** — plans may mark a step `ARMED` (extra column token); global UI toggle "Arming mode": when ON, execution pauses at ARMED steps until an explicit Arm click (hold-to-confirm); when OFF, marks ignored. Supervisor treats it as an implicit HOLD-at-step.

# PHASE F — INSPECTION & CAPABILITY CONTRACT (~6 days)
**Checkpoints:** F.1 → F.2 → F.3 → F.4 → 🟣 FR-F1 (HOLD/resume contract) → 🟡 HV-4a (G3 safe-state definitions, desk) → F.5 → 🟣 FR-F2 → 🔴 HV-4b (safing witness session — Giorgio's presence MANDATORY) → F.6.
### F.1 READ step — **S-M** — `Resource | READ | node_name` → agent `service_read` (base class) returns the value in feedback (`message` + typed `value` field) → event log. Pre-flight checks node existence for that resource's declared nodes.
### F.2 CHECK step `[LIT: PLEXIL guarded steps]` — **M** — `Resource | CHECK | node, op, value` (op ∈ <,>,==,!=,<=,>=; tolerance for ==) → agent evaluates against a live read → `CHECK_PASSED` / `CHECK_FAILED` (typed, not generic ERROR). Supervisor policy: CHECK_FAILED → HOLD (F.3), not abort.
### F.3 HOLD + inspection capsule + validated resume `[ARBITRATED: branches regenerate UPSTREAM]` — **M-L** — on CHECK_FAILED or explicit `HOLD` step: (1) safe hold (A.7 machinery; safe-state F.5 when available); (2) publish **inspection capsule** on a REST/WS interface for the KBS: `{run_id, step, measurements, machine_snapshot, plan_pedigree}`; (3) accept `resume_plan {tail_steps|tail_file}` — accepted ONLY after full A.2 pre-flight of the tail; resume events logged. Pre-authored `ON_FAIL | RUN_FILE | x.txt` allowed ONLY as safety contingency (safing/retreat), never product-state routing. *(Deliberately the same pathway the Coordinator triggers on virtual failure — one tested mechanism, two triggers.)*
### F.4 Plan pedigree + capability hash `[LIT: JPL traceability; SiLA2 versioning]` — **M** — plan header block (comment-syntax, backward compatible): `#PEDIGREE plan_sha=… caps_sha=… nodemap_sha=… validated=[{ctx,ts,verdict}]`; agents send `capability_hash` at registration (sha of canonical schema JSON); supervisor refuses execution on mismatch (override flag logged loudly); capability change invalidates cached validations + G.7 invariants.
### F.5 Safe-state services + safing ladder — **GATED G3** `[LIT: Sagas+JPL-FDIR]` `[GAP-FILL: physical saga]` — **L** — per-machine `service_safe_state` (definition from Giorgio); per-step reversibility class metadata in schemas; abort ladder completed: HOLD → STOP-DISPATCH → SAFE-STOP (drives safing subplan); UI three buttons with honest semantics.
### F.6 Capability export + browser `[LIT: CSS-ETFA; AAS-PDDL-2026]` (+v3.2 3.4 metadata) — **M** — `GET /capabilities` (versioned JSON: services, params, ranges, units, anchors, reversibility, hash); UI browser panel rendering it; service catalog metadata (units/descriptions) added to schema generation; optional `GET /capabilities/pddl` stub for the KBS bridge (R2.7).

# PHASE G — SiL RUNGS & EXECUTION COORDINATOR (final; gated G5; ~12 days)
**Checkpoints:** entry = 🔴 HV-5 (G5 lab setup, Giorgio, spread over days). G.5 → 🔴 HV-6a (approve decision-support use). **Before writing G.6 code:** 🟣 FR-G design review. End: 🔴 HV-6b (look-ahead demo).
### G.1 Validate-the-validator `[LIT: DT-behavioural-model-validation-2025]` — **M** — replay tool: feed a recorded physical run's command stream to MiL-behave; score per-step duration deltas + anchor end-state deltas; report per axis. A model that hasn't been scored issues no trusted verdicts.
### G.2 SiL-A: PLCSIM Advanced context — **M** — load MULLUTENSIL TIA project; enable CPU OPC UA server (license!); PLCSIM Virtual Eth Adapter; register as context (C.2/C.3 namespace mapping); envelope `+control-logic (MULLUTENSIL)`. Optional plant: Virtuos via its PLCSIM connector.
### G.3 SiL-B: second CODESYS on Nerve `[ORIG]` — **M** — deploy the same 61131-3 app to a sandboxed CODESYS instance (Nerve workload) with its own OPC UA exposure; context for DOOSAN/SEIT logic; no Siemens toolchain involved.
### G.4 MiL-geometric: Virtuos context — executor-side ≈0 beyond C.2/C.3 (it's just another endpoint); lab-side: expose Virtuos models via OPC UA connector; envelope `+kinematics,collision`. *(This rung is what actually checks admissibility of motion.)*
### G.5 Coordinator stage 1 — decision support `[LIT: symbiotic simulation]` — **L** — separate module/process (`src/coordinator/`), own client type on the broker; mode Δ=∞: launch plan on a virtual ctx via a virtual-bound SystemAgent instance; collect verdict; produce **validation report** (verdict, envelope, anchor traces, predicted durations) bound to the plan pedigree (F.4); UI shows report; human approves physical launch. Ledger persisted via event log.
### G.6 Coordinator stage 2 — control (look-ahead) `[LIT: FTRT; anchor-points; shadow non-interference]` — **L-XL** — two SystemAgent instances (both single-world, unmodified); finite Δ permission window: physical may enter step k only after virtual completed k (permission tokens over `/ws`); anchor divergence monitor at step boundaries; virtual failure → auto-HOLD physical at last validated step (F.3 pathway); resync: state-inject physical actuals into the virtual plant, replay window; non-interference: virtual leg never delays physical except at permission boundaries.
### G.7 Invariant distillation `[ARBITRATED: Giorgio's idea]` `[GAP-FILL]` — **L** — miner over virtual-rejection events: recurring failure preconditions → candidate invariants (`x>1900 ∧ barrier_engaged ⇒ reject, 7/7 runs`); human confirm (or N-consistent auto-promote) → pre-flight **WARNING** rules; restrictive-only (flag, never authorize); provenance + producing rung's envelope attached; invalidated on capability-hash change; export endpoint for the planner.
### G.8 Model calibration + duration model — **M** — fit MiL-behave dynamics (effective vel, settle times) and per-(service,axis,distance,velocity) duration estimates from physical event-log data; feeds E.3 predictions and physics-based execution timeouts (replacing static A.3 defaults).

## CROSS-CUTTING (continuous)
`PROTOCOL.md` grows from A.1 (formal payload docs incl. VariantType.Double note) `[v3.2 3.3]` · type hints + docstrings on every touched file `[3.2]` · node-name consistency script `tests/check_node_map.py` `[3.1]` · per-run conformance report (planned-vs-executed durations/anchors) once B.1+C.8+G.8 exist.

## OPTIONAL BACKLOG (Giorgio's dispositions — do not schedule unless promoted)
**Teach-mode plan recorder** (record manual jog → draft plan; pairs with C.5) · **Blast-radius strip** (per-axis swept intervals + declared zones — pre-DT spatial awareness) · **Wear/cost ledger** (usage stats per axis/actuator; empirical cost coefficients for the KBS cost model — no auto component-change decisions) · **Time-scrub replay UI** (cursor over event log + data_log) · **Plan lineage/diff** · **Run-provenance packaging** (RO-Crate-style zip) · **STL alert rules** (upgrade of threshold alerts, FEATURE-5) · **guard-module extraction + margin analytics** (R2.3) · **CNP-lite capability-addressed dispatch** (when 2 resources share a capability).

## PRIORITY MATRIX & NEXT 5 DAYS (6 h/day)
| Day | Work |
|---|---|
| 1 | 🟡 prompt **HV-0** (G1/G2 — 15 min of Giorgio's time, ideally same day) · A.0 · A.1 start |
| 2 | A.1 finish + tests |
| 3 | A.2 |
| 4 | A.3 |
| 5 | A.4 + A.5 start |
Week 2: A.5 finish → A.6 (only if HV-0 approved G2) → A.7 → B.1 → 🟣 **FR-A** → 🔴 **HV-1** (ask Giorgio to book the ~2 h lab slot ALREADY during week 1, so it lands right after FR-A). While FR-A/HV-1 pend: B.2–B.7, E.1, PROTOCOL.md.
Effort roll-up: A ≈7d · B ≈4d · C ≈8d · D ≈5d · E ≈6d · F ≈6d · G ≈12d.

## IMPLEMENTATION STATUS LEDGER *(executing session: update per item — checkpoints included)*
| Item | Status | Commit / date | Notes |
|---|---|---|---|
| 🟡 HV-0 | pending | — | G1+G2 decisions — request on day 1; G1 HARD-BLOCKS HV-1 |
| A.0 | pending | — | .gitignore exists; git init NOT yet run (interrupted 2026-07-07) |
| A.1 · A.2 · A.3 · A.4 · A.5 | pending | — | strict order |
| A.6 | **gated G2** | — | implement only if HV-0 approves |
| A.7 | pending | — | |
| B.1 | pending | — | BEFORE FR-A (recordings needed at HV-1) |
| 🟣 FR-A | pending | — | Fable review, Phase A diff — blocks HV-1 |
| 🔴 HV-1 | pending | — | ~2 h lab session — blocks C.7 baselines, G.1 data, any physical run |
| B.2–B.7 | pending | — | parallel-safe during FR-A/HV-1 wait |
| C.1 · C.2 · C.3 · C.4 · C.5 | pending | — | C.2 must include `physical_enabled` flag |
| 🟣 FR-C | pending | — | blocks HV-2 |
| 🔴 HV-2 | pending | — | virtual-only execution approval (remote OK, standing) |
| C.6 · C.7 · C.8 · C.9 · C.10 | pending | — | C.7 needs HV-1 recordings |
| E.1–E.8 | pending | — | parallel-safe any time after B |
| D.1 · D.2 · D.3 | pending | — | |
| 🟣 FR-D | pending | — | blocks HV-3 |
| 🔴 HV-3 | pending | — | ~45 min lab (reconnect/resume) |
| D.4 · D.5 · D.6 · D.7 | pending | — | |
| F.1 · F.2 · F.3 · F.4 | pending | — | |
| 🟣 FR-F1 | pending | — | HOLD/resume contract review |
| 🟡 HV-4a | pending | — | G3 safe-state definitions (desk) — blocks F.5 |
| F.5 | **gated G3** | — | |
| 🟣 FR-F2 → 🔴 HV-4b | pending | — | safing witness — Giorgio's presence MANDATORY |
| F.6 | pending | — | |
| 🔴 HV-5 | pending | — | G5 lab setup (TIA/PLCSIM, Virtuos connector, 2nd CODESYS, endpoint identity) |
| G.1 · G.2 · G.3 · G.4 · G.5 | pending | — | G.2–G.4 parallelizable after HV-5 |
| 🔴 HV-6a | pending | — | approve decision-support use of coordinator |
| 🟣 FR-G | pending | — | design review BEFORE G.6 coding |
| G.6 · G.7 · G.8 | pending | — | |
| 🔴 HV-6b | pending | — | look-ahead demo, stage-2 sign-off |
