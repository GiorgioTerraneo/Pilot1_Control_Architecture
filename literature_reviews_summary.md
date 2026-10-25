# Literature Reviews — Complete Maps & Paper Roadmap
**System Executor, CIRC4Me Pilot 1 — rev. 2, 2026-07-07**
Companions: `architecture_v4_full_description.md` (§ references below point there) · `piano_azione_v4.0.md`.

Three review rounds: **Round 1** (5 domain areas, ~16 queries, ~180 results), **Round 2** (4 cross-domain areas, 11 queries, ~102 results), **Round 3** (5 targeted areas for the virtual-execution workstream, 6 queries, ~50 results). 61 papers retained. Method: web search on primary venues (CIRP Annals, Procedia CIRP, IEEE TII, RCIM, JMS, IJAMT + arXiv/standards), 5 most relevant per area, recency preferred, seminal accepted.
⚠ = author list not verified from search results — **verify before formal citation**. Tags: `[LIT] [CONTRA] [GAP-FILL] [ORIG] [ARBITRATED]` (definitions in architecture doc §0).

---

# 1. ROUND 1 — Domain literature

## 1.A Landscape summary
The executor is a **lightweight, domain-specific MES** at ISA-95 Level 3 (dispatching/execution) reaching into L1/2 via OPC UA — a compression of the Purdue stack that current MES research explicitly endorses for CPS (service-oriented, broker-mediated architectures). Its SystemAgent/ResourceAgent split is a textbook **supervisor–worker MAS** between the "Hierarchical" and "Federation" categories: central supervisor + autonomous self-describing machine agents + pure broker — close to the holonic tradition (PROSA-style resource holons) but without a negotiation layer (dispatch by name, not bidding). The domain frame is **Tolio et al. 2017** (CIRP keynote on de/remanufacturing systems); the CIRP community has since published on exactly this system class (adaptive/condition-aware disassembly control, 2025), and a 2025 IJCIM paper presents the executor's **closest published sibling** (distributed multi-agent control of a battery-disassembly cell) — the benchmark for novelty claims. On the software side, `service_*` auto-discovery instantiates the **Capability–Skill–Service (CSS) model**: the executor implements the *skill* half elegantly (introspection = zero-boilerplate registration) but lacks the *capability* half (units, pre/postconditions, semantics) that enables planner feedback and validation. The masterplan is a workflow: BPMN-on-shop-floor, the **saga pattern**, **behavior trees**, and **event sourcing** are the relevant mature machinery; the lab's DT roadmap milestones 4–6 correspond to **virtual commissioning / X-in-the-loop** with the key transferable principle of *twin-transparent execution* (same plan, same dispatch path, virtual or physical target).

## 1.B Key papers
**Area 1 — MES & control architecture**
- **Tolio, Bernard, Colledani, Kara, Seliger, Duflou, Battaia, Takata (2017)**, *Design, management and control of demanufacturing and remanufacturing systems*, CIRP Annals 66(2):585–609. Relevance: defines the system class (one-of-a-kind input, condition-driven planning). Key concept: de/remanufacturing control must be designed around input-condition uncertainty, not adapted from forward manufacturing.
- ⚠ (2025), *Adaptive production control for agile disassembly systems in remanufacturing*, CIRP Annals — [link](https://www.sciencedirect.com/science/article/pii/S0007850625000459). Relevance: CIRP's current answer to condition-variability control; the executor is its missing execution layer. Key concept: reactive control re-parameterizing as product-condition information arrives.
- ⚠ (2025), *Condition-aware capacity planning for agile hybrid disassembly systems*, CIRP JMST — [link](https://www.sciencedirect.com/science/article/pii/S1755581725000574). Key concept: capability-based system modeling with product-condition deviations as first-class inputs.
- ⚠ (2022), *Intelligent manufacturing execution systems: a systematic review*, JMS — [link](https://www.sciencedirect.com/science/article/abs/pii/S0278612522000048). Key concept: next-gen MES as thin orchestration over service-oriented machine interfaces.
- Derigent, Cardin, Trentesaux (2021), *Industry 4.0: contributions of holonic manufacturing control architectures*, J. Intell. Manuf. — [arXiv](https://arxiv.org/pdf/2002.04525). Key concept: holon = physical resource + information counterpart (= ResourceAgent) with explicit disturbance-handling duties the current agents lack.
- ⚠ (2016), *Agent-based MES for short-series production scheduling*, Computers in Industry — [link](https://www.sciencedirect.com/science/article/pii/S0166361516301233). Key concept: ISA-95 MOM activities mapped onto agent responsibilities.

**Area 2 — Multi-agent systems**
- Smith (1980), *The Contract Net Protocol*, IEEE Trans. Computers (seminal). Key concept: capability-based task award decouples plans from resource identity — the upgrade path when two resources share a capability.
- Leitão (2009), *Agent-based distributed manufacturing control: a state-of-the-art survey*, Eng. Appl. AI (seminal). Key concept: canonical failure modes — supervisor SPOF, deadlock, stale registry; agents must own local recovery.
- ⚠ (2021), *Employing agent beliefs during fault diagnosis for IEC 61499 industrial CPS* — [arXiv](https://arxiv.org/pdf/2105.03851). Key concept: an agent maintaining an explicit hardware belief state distinguishes "write failed" from "hardware in unexpected state".
- ⚠ Xia et al. (2024), *Control industrial automation system with LLM agents* — [arXiv](https://arxiv.org/pdf/2409.18009). Key concept: NL-to-plan above a stable schema-described service layer — strengthens the case for formal service schemas.
- ⚠ (2026), *CASCADE: cascaded scoped communication for multi-agent re-planning in disrupted industrial environments* — [arXiv](https://arxiv.org/pdf/2604.00451). Key concept: failure information propagates only as far as recovery needs.

**Area 3 — CPS / Capability–Skill–Service**
- ⚠ Köcher et al. (2022), *Capabilities and skills in manufacturing: a survey over the last decade of ETFA* — [arXiv](https://arxiv.org/pdf/2204.12908). Relevance: answers "is `service_*` a known pattern?" — yes, a lightweight skill model. Key concept: capability (implementation-independent description) vs skill (executable implementation) — the executor has skills without capabilities.
- ⚠ (2026), *From capability models to automated planning: an AAS-native approach for automatic PDDL generation* — [arXiv](https://arxiv.org/pdf/2606.02167). Key concept: capability models GENERATE the PDDL domain — the planner always plans against what the executor can execute (→ F.6, R2.7).
- ⚠ (2019), *Apply SOA paradigms in CPS to enhance interoperability: state-of-the-art review* — [arXiv](https://arxiv.org/pdf/1903.00065). Key concept: service contracts (schema+semantics+QoS) as the interoperability unit.
- ⚠ Pop et al. (2021), *The FORA fog computing platform for industrial IoT* — [arXiv](https://arxiv.org/pdf/2007.02696). Key concept: edge node as deterministic substrate hosting containerized control services (TTTech-adjacent; → Nerve deployment).
- ⚠ (2023), *Investigation of microservice-based workflow management solutions for industrial automation*, Appl. Sci. 13(3) — [link](https://www.mdpi.com/2076-3417/13/3/1835). Key concept: workflow lifecycle (model→validate→deploy→execute→analyze) as the checklist for an execution engine.

**Area 4 — Flexible/reconfigurable & disassembly control**
- ⚠ (2025), *A distributed control architecture for a multi-agent robotic cell: a battery pack disassembly case study*, IJCIM — [link](https://www.tandfonline.com/doi/full/10.1080/0951192X.2025.2531488). **Closest published sibling — read to sharpen novelty claims.**
- ⚠ (2024), *A comprehensive review on human–robot collaboration remanufacturing towards uncertain and dynamic disassembly*, Manufacturing Review — [link](https://mfr.edp-open.org/articles/mfreview/full_html/2024/01/mfreview240001/mfreview240001.html). Key concept: uncertainty classes (condition/geometry/process) map to distinct control responses → typed error taxonomy.
- ⚠ (2025), *Hierarchical planning and scheduling for reconfigurable multi-robot disassembly systems under structural constraints* — [arXiv](https://arxiv.org/pdf/2509.14564). Key concept: system plan = resource-annotated refinement of the process plan, feasibility checked at refinement (formalizes vision §5).
- ⚠ (2023), *Digital-twin-driven robotic disassembly sequence dynamic planning under uncertain missing condition* (IEEE TII ⚠). Key concept: the twin arbitrates plan validity when reality diverges from the product model.
- ⚠ (2025), *From CAD to POMDP: probabilistic planning for robotic disassembly of EOL products* — [arXiv](https://arxiv.org/pdf/2511.23407). Key concept: backup actions attached to plan steps — minimal branching worth supporting before full policies.

**Area 5 — Workflow & orchestration**
- Garcia-Molina & Salem (1987), *Sagas*, ACM SIGMOD (seminal). Key concept: step + compensating action; reverse-order compensation on failure; orchestrated variant fits the SystemAgent directly.
- Iovino, Scukins, Styrud, Ögren, Smith (2022), *A survey of behavior trees in robotics and AI*, RAS — [link](https://www.sciencedirect.com/science/article/pii/S0921889022000513). Key concept: Fallback nodes = per-step recovery as data; the masterplan is a degenerate BT (one Sequence).
- ⚠ (2024), *Towards using behavior trees in industrial automation controllers* — [arXiv](https://arxiv.org/html/2404.14030v1). Key concept: BT supervisory layer over device skill libraries — structurally identical to SystemAgent over `service_*`.
- ⚠ (2024), *Executing automotive test workflows with BPMN and web service orchestration in software-defined car manufacturing*, Production Engineering — [link](https://link.springer.com/article/10.1007/s11740-024-01302-1). Key concept: BPMN buys branching/parallelism/tooling at engine-weight cost → informs "subset, not engine".
- ⚠ (2021), *Improving observability in event sourcing systems*, JSS — [link](https://www.sciencedirect.com/science/article/abs/pii/S0164121221001126) + ⚠ *SensorStream: an XES extension for enriching event logs with IoT sensor data* — [arXiv](https://arxiv.org/pdf/2206.11392). Key concept: append-only, sensor-enriched event logs → replay, conformance, process mining.
- ⚠ (2024), *Autonomous robot task execution in flexible manufacturing: integrating PDDL and behavior trees in ARIAC* — [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC11504948/). Key concept: PDDL planner feeding an executor — the lab's KBS+executor as a published pattern.

## 1.C Architectural patterns identified (9)
1. **Holonic resource pairing** — maps to ResourceAgent; would add explicit local disturbance handling. 2. **Contract Net** — dispatch is by name; CNP is the capability-addressed upgrade (adopt addressing, skip bidding until 2 resources compete). 3. **Capability–Skill–Service** — introspection = skill layer; would add typed, unit-annotated, pre/postcondition capability metadata. 4. **Orchestrated saga** — SystemAgent is an orchestrator without a compensation table; would add per-service compensation → transmuted into safing (physical saga). 5. **Behavior trees** — masterplan = degenerate Sequence; would add Fallback/Retry semantics → adopted only as guarded steps, not tick engines. 6. **Orchestration vs choreography** — orchestration is correct for a safety-critical single cell (auditability, single halt point); mitigation for supervisor SPOF is state checkpointing, not choreography. 7. **Event sourcing + XES** — feedbacks are transient today; would add an append-only run store. 8. **Virtual commissioning / X-in-the-loop, twin-transparent execution** — would add an execution-target abstraction behind the SAME dispatch path. 9. **ISA-95 placement** — vocabulary for papers/transferability; not a build plan.

## 1.D Gaps and opportunities (10)
1. No conditional branching for inspection→decision→process (vision §4) — later resolved as: bounded, upstream-regenerated branching + HOLD interface `[ARBITRATED]`. 2. No compensation/safe-state semantics for irreversible ops. 3. No persistent execution event log — runs evaporate. 4. Skills without capabilities (blocks planner loop, dry-run, AAS/PDDL bridge). 5. No twin-transparent execution target. 6. Failure handling below SOTA (SPOF, fatal disconnections, untyped single ERROR). 7. Name-addressed dispatch blocks procedural flexibility. 8. No dry-run/validation mode in the executor itself. 9. No security on control channels. 10. Observability not process-mining-ready.

## 1.E Round-1 recommended reading
Tolio 2017 (the frame every reviewer applies) · CIRP 2025 adaptive disassembly control (the current position on your problem) · IJCIM 2025 battery cell (closest competitor) · ETFA CSS survey (vocabulary to position introspection as contribution) · BT survey (most transferable single idea for plan-format evolution).

---

# 2. CRITICAL RE-EVALUATION (the "third lens" — where papers fall short & where to push back)

**Area 1.** *Falls short:* MES research targets forward manufacturing at volume; research observability (runs as scientific data) and lab-scale one-off DEmanufacturing are absent; taxonomies abound, reference implementations don't → `[GAP-FILL]` a minimal, open, research-grade execution layer with honest empirical failure reporting. *Push back:* ISA-95 layering is descriptive — the executor's L3/L2 compression is a feature; resist "intelligent MES" AI-in-the-execution-path — deterministic glass box `[CONTRA: intelligent-MES]`.
**Area 2.** *Falls short:* classic MAS validated on simulations/toy cells; FIPA-stack engineering cost underreported; silent hardware failure (the write-and-verify problem) essentially unaddressed → empirically grounded minimal-MAS-on-real-hardware is novelty space. *Push back:* CNP is recommended reflexively — with 3–4 machines of disjoint capabilities, bidding is ceremony → capability-addressed lookup `[CONTRA: CNP-wholesale]`; full BDI is overkill — the useful kernel is a verified-hardware-state "belief" `[CONTRA: BDI-wholesale]`; keep the broker dumb `[CONTRA: smart-middleware]`.
**Area 3.** *Falls short:* CSS/AAS models are ontologically heavy (OWL, submodels) with thin adoption; nobody quantifies the MINIMUM capability annotation that unlocks validation → define the **minimum viable capability model** (units, ranges, pre/post, reversibility, anchors) `[GAP-FILL]`. *Push back:* map/export to AAS, don't adopt natively `[CONTRA: AAS-native]`; RAMI 4.0 is a classification aid; don't decompose finer than agent-per-machine `[CONTRA: microservice-decomposition]`.
**Area 4.** *Falls short:* disassembly research is planner-obsessed — papers end where execution begins; DRL/POMDP planners presuppose data that one-off EOL motors don't provide → double `[GAP-FILL]`: the executor IS the missing layer, and its event logs are the missing datasets. *Push back:* against free-form runtime replanning → **bounded adaptivity**: pre-validated behavior only, everything else escalates (HOLD→upstream) — constrained adaptivity as a *safety feature* `[CONTRA: unconstrained-replanning]`.
**Area 5.** *Falls short:* BPMN engines have no physical-state/safe-state concepts; saga theory assumes compensable transactions — heating/pressing/extraction have physical entropy → **physical saga** (reversibility classes + safing) is essentially unwritten `[GAP-FILL]`; industrial BT adoption embryonic, tick semantics fit long ops poorly. *Push back:* `[CONTRA: BPMN-engine, saga-as-undo, BT-ticking]` — typed plan extensions + safe-state driving + guarded steps instead.

**Synthesis that motivated Round 2:** four recurring blind spots — (1) irreversibility of physical actions, (2) validate-before-execute as first-class workflow, (3) execution-layer honesty about hardware, (4) runs as scientific data. Spaceflight ops, AI acting, runtime assurance, and self-driving labs each own one or more.

---

# 3. ROUND 2 — Cross-domain

## 3.A Landscape
**The executor is a mission-operations system for the factory floor.** Deep-space operations solved this problem class under harsher constraints: one-of-a-kind command sequences on unique, irreplaceable hardware, irreversible actions, mandatory pre-execution validation. Their stack — rule-check (**RP-check**, daily use on Curiosity) → high-fidelity testbed execution → layered fault protection with autonomous **safing** — maps rung-for-rung onto the lab's needs, including the practice of layering CHEAP validation before EXPENSIVE validation. The AI-robotics community names the executor's discipline (**acting**: Ingrand & Ghallab; PLEXIL as the mature executable-plan language with formally verifiable semantics); **runtime assurance** (Simplex) formalizes agent-side range validation as a named architecture; chemistry's **self-driving laboratories** are the executor's closest cultural siblings (heterogeneous instruments, runtime-generated one-off plans, everything-is-data) and independently standardized the introspection idea (**SiLA 2** zero-config discovery + **observable commands**); **W3C PROV / RO-Crate** completes "runs as citable research objects".

## 3.B Key papers
**Area 6 — high-consequence sequence execution:** Muscettola, Nayak, Pell, Williams (1998), *Remote Agent*, AIJ 103 — planner–executive–diagnosis three-tier, flight-proven; the missing third tier (mode estimation, Livingstone) = explicit hardware-state inference. · JPL ⚠, *RP-check: an architecture for spaceflight command sequence validation* — [pdf](https://www-robotics.jpl.nasa.gov/media/documents/rp_check_v4.pdf) — executable flight rules over every sequence pre-execution; validation as a pipeline. · Morgan (JPL), *Fault protection techniques in JPL spacecraft* — [pdf](https://s3vi.ndc.nasa.gov/ssri-kb/static/resources/05-2750.pdf) — FDIR ladder; **safing ≠ rollback**. · ⚠ ESA, *Lessons learned from safe modes on Mars Express/Venus Express/Rosetta* — most safe-mode entries trace to interaction effects between nominally-correct subsystems (only system-level validation catches them). · JPL ⚠ (2025), *Improving sequence traceability* — [pdf](https://www-robotics.jpl.nasa.gov/media/documents/IEEE25-sequence-traceability-v3.pdf) — every sequence carries its validation pedigree.
**Area 7 — plan execution & acting:** ⚠ Verma et al. (2006), *PLEXIL* — [NTRS](https://ntrs.nasa.gov/archive/nasa/casi.ntrs.nasa.gov/20060019246.pdf) — per-node Start/End/Invariant/Skip conditions; deterministic; + *PLEXIL-V* formal verification ([GitHub](https://github.com/nasa/PLEXIL-V)) — choose plan semantics small enough to model-check. · Ingrand & Ghallab (2017), *Deliberation for autonomous robots*, AIJ 247 — five functions (planning/acting/monitoring/observing/learning); acting = legitimate executor-side refinement scope. · Muscettola, Morris, Tsamardinos (1998) + Hunsberger & Posenato (2024) — STN(U) dispatchability: per-step temporal windows as the formal ceiling of timeout work. · ⚠ (2024), *Constructing behavior trees from temporal plans* — [arXiv](https://arxiv.org/html/2406.17379) — accepted format ≠ executed structure (compile, keep the .txt contract).
**Area 8 — runtime assurance:** Sha (2001), *Using simplicity to control complexity*, IEEE Software — Simplex: safety authority belongs to the simplest verifiable component. · ⚠ Mehmood et al., *Black-box Simplex* — [arXiv](https://arxiv.org/abs/2102.12981) — runtime action checks without verifying the advanced controller (matches unverifiable planner/DT). · Bartocci, Deshmukh, Donzé, Fainekos, Maler, Ničković, Sankaranarayanan (2018), *Specification-based monitoring of CPS* (Lectures on RV) — STL with quantitative robustness margins. · ⚠ (2022), *A distributed Simplex architecture for multi-agent systems*, JSA — per-agent guards composing to system safety. · ⚠ Reelay STL tooling — [arXiv](https://arxiv.org/pdf/2604.22384).
**Area 9 — self-driving labs & provenance:** ⚠ Aspuru-Guzik group (2024), *Self-driving laboratories for chemistry and materials science*, Chem. Rev. — [ACS](https://pubs.acs.org/doi/10.1021/acs.chemrev.4c00055) — lab-autonomy maturity levels (thesis narrative device). · ⚠ (2024), *ChemOS 2.0*, Matter — [link](https://www.sciencedirect.com/science/article/pii/S2590238524001954) — orchestrator persists ALL inter-module traffic by design. · ⚠ (2022), *SiLA 2: the next generation lab automation standard* — [PubMed](https://pubmed.ncbi.nlm.nih.gov/35639108/) — independent standardization of introspection-style discovery; **observable commands** = the most transferable increment. · ⚠ (2026), *LAP: an agent-to-instrument protocol for autonomous science* — [arXiv](https://arxiv.org/pdf/2606.03755) — typed capability schemas consumed by planning agents. · ⚠ (2024), *Recording provenance of workflow runs with RO-Crate*, PLOS ONE + W3C PROV-DM — provenance = plan + environment + trace bound together.

## 3.C Patterns (9): planner–executive–diagnosis three-tier · layered validation rule-check→testbed→execute · safing/FDIR ladder · PLEXIL node conditions · dispatchable temporal plans · Simplex guard · STL monitoring · self-describing instrument services + observable commands · workflow-run provenance objects.
## 3.D Gaps (10, provenance-tagged): layered validation pipeline `[LIT: RP-check]+[GAP-FILL]` · safing + reversibility classes `[LIT: FDIR]+[CONTRA: saga-as-undo]+[GAP-FILL]` · guarded steps `[LIT: PLEXIL]+[CONTRA: BPMN/BT]` · mode-estimation tier `[LIT: Livingstone]+[GAP-FILL vs MAS lit]` · observable commands `[LIT: SiLA2]` · Simplex framing of the two-level validation `[LIT]` · STL monitors over OPC UA `[LIT]` · provenance-grade run records `[LIT: RO-Crate]+[GAP-FILL]` · STNU-lite temporal windows `[LIT]` · **the mission-ops positioning claim itself `[GAP-FILL]`**.
## 3.E Reading: Remote Agent · RP-check · Ingrand & Ghallab · SiLA 2 chapter · Sha 2001.

---

# 4. ROUND 3 — Virtual-execution workstream (validation of the MiL/SiL/coordinator design)

## 4.A Landscape
The independently-derived design has names in three literatures. The execution-target ladder = the **virtual commissioning** MiL/SiL/HiL taxonomy (their SiL = virtual controller + virtual plant → PLCSIM Advanced rung; "soft commissioning"/HiL = real controller + simulated plant). The Python behavioral plant = an open **SIMIT/WinMOD-class behavior model**, with level-of-detail research endorsing low-fidelity signal models for logic validation, and a live thread on VC models *outliving* commissioning as runtime twins. The Execution Coordinator belongs to **symbiotic simulation** (20 years of literature, already applied to remanufacturing decision support); the temporal margin is **faster-than-real-time simulation**; the Δ=∞ degenerate mode maps to software engineering's **shadow-mode deployment** (zero authority, zero interference). The freshest anchor — a systematic review of **online simulation at machine level** — identifies *initialization from live system state* as the field's hard problem, exactly the resync/state-injection element, hence designed first-class. Co-simulation standards (FMI, **DCP**) are the formal coupling alternative: watch-item, not adoption `[CONTRA: DCP-now]`.

## 4.B Key papers
- ⚠ (2023), *Concepts and trends of virtual commissioning — a comprehensive review*, JMS — [link](https://www.sciencedirect.com/science/article/pii/S0278612523002145) — the taxonomy + tooling reference (SIMIT/WinMOD; PLCSIM/PLCSIM Advanced).
- ⚠ (2015), *Levels of detail and appropriate model types for virtual commissioning* — fidelity matched to the property validated.
- ⚠ (2025), *Continued use of virtual commissioning models toward digital twins*, IJAMT — [link](https://link.springer.com/article/10.1007/s00170-025-17195-y) — VC model as maintained runtime asset.
- ⚠ (2025), *Development and validation of DT behavioural model for VC of CPS*, Appl. Sci. — [link](https://www.mdpi.com/2076-3417/15/5/2859) — validate the behavior model against the physical system before trusting it as validator (→ G.1).
- ⚠ Vogel-Heuser group (2018), *Consistency check to synchronize the digital twin based on anchor points* — [link](https://www.sciencedirect.com/science/article/pii/S221282711830324X) — designated-variable consistency (→ C.8, G.6).
- ⚠ (2024), *Synchronization evaluation of DT for a robotic assembly system using computer vision* — independent channel to score sync (lab-feasible: 3D scanner).
- ⚠ Aydt, Turner, Cai, Low, *Symbiotic simulation systems: an extended definition* — decision-support vs control modes (→ staged coordinator autonomy).
- ⚠ (2019), *Extending decision-making in remanufacturing service contracts using symbiotic simulation* — [RG](https://www.researchgate.net/publication/334233935) — the field already touches remanufacturing (positioning anchor).
- ⚠ (2021), *Faster than real-time simulation: methods, tools, applications* — [arXiv](https://arxiv.org/pdf/2104.04149) — look-ahead margin bounded by model speed AND validity envelope.
- ⚠ (2024), *Online simulation at machine level: a systematic review* — [arXiv](https://arxiv.org/pdf/2401.07841) — **top reading**; initialization-from-live-state is THE hard problem.
- FMI standard — [fmi-standard.org](https://fmi-standard.org/); ⚠ (2019), *The Distributed Co-simulation Protocol (DCP)* — [RG](https://www.researchgate.net/publication/330810562) — formal real-time/simulation coupling (watch-item).
- ⚠ (2024), *Shadow testing in autonomous vehicles* + industry shadow-deployment practice — candidate consumes live inputs with zero authority; promotion is a separate explicit step.

## 4.C Validation verdicts on the workstream design
| Design element | Verdict | Refinement adopted |
|---|---|---|
| MiL/SiL/HiL/Phys ladder | VALIDATED | adopt VC vocabulary exactly |
| MiL-behave (axis-level SMs, mission layer absent) | VALIDATED (SIMIT/WinMOD class) | + G.1 validate-the-validator |
| Coordinator as separate module, last | VALIDATED + NAMED (symbiotic simulation) | staged autonomy: decision-support → control |
| Δ-window unification (∞→finite) | VALIDATED (complete VC ≈ Δ=∞; FTRT ≈ finite; shadow ≈ no authority) | non-interference rule |
| Resync / state injection | VALIDATED as the hard part | designed first-class in C.5 |
| Divergence monitoring | REFINED | anchor points, not full state vectors |
| (new) validity envelopes per context | ADOPTED | verdicts + learned invariants carry producing rung's envelope |
| OPC UA as coupling fabric | VALIDATED | DCP watch-item `[CONTRA: DCP-now]` |

## 4.D Technical groundings (tool facts, searched)
ISG-virtuos: MiL→SiL→HiL platform; Connector Manager includes **OPC UA**, **PLCSIM (threaded sync mode)**, EtherCAT sim, ADS/TwinCAT, B&R ([release notes](https://www.isg-stuttgart.de/en/news/details/isg-virtuos-v36-now-available)). S7-PLCSIM Advanced: virtual S7-1500 with REAL logic; exposes the CPU's own OPC UA server via PLCSIM Virtual Eth Adapter (TIA ≥V16, CPU OPC UA license) ([manual](https://cache.industry.siemens.com/dl/files/153/109739153/att_895955/v1/s7-plcsim_advanced_function_manual_en-US_en-US.pdf)). TTTech Nerve: Data Gateway OPC UA server+client; CODESYS soft-PLC in real-time VM (≥1 ms); Docker(-Compose) workloads ([docs](https://docs.nerve.cloud/developer_guide/data/)) — node_map evidence (ns=3 `|var|Nerve.Application.PLC_PRG.*` + ns=4 S7 DBs under one endpoint) ⇒ 4842 is the Nerve aggregation server (confirm = G5) ⇒ **DOOSAN/SEIT logic already runs in CODESYS ⇒ SiL-B needs no Siemens toolchain**.

---

# 5. CONSOLIDATED TRACEABILITY — source → plan item (piano_azione_v4.0.md)
| Source key | Generated / validated |
|---|---|
| SiLA2 observable commands | A.3, B.6 |
| FIPA conversation-id (concept) | A.1 |
| RP-check | A.2, E.3, F.4; layered-validation concept |
| Leitão failure modes | A.5, D.1–D.3 |
| Sha Simplex / Black-Box | A.6 rationale; guard-as-component framing |
| JPL FDIR / safing | A.7, F.5, C.6 |
| Holonic (Derigent) | A.4 busy = resource ownership |
| Event sourcing + XES | B.1, B.3 |
| Remote Agent / Livingstone | B.2, D.1 reconciliation; future mode-estimation tier |
| Anchor points 2018 | C.8, G.6 |
| SIMIT/WinMOD + LoD 2015 | C.5 design + fidelity scope |
| VC review 2023 | C.2 vocabulary; G.2–G.4 rungs |
| Online-sim review 2024 | C.5 state injection first-class |
| Shadow mode | C.4, C.10, G.6 permission-boundary rule |
| Symbiotic simulation (+remanufacturing 2019) | G.5/G.6, staged autonomy |
| FTRT 2021 | G.6 margins; validity envelopes |
| DT behavioural model validation 2025 | G.1 |
| PLEXIL (+PLEXIL-V) | F.2 guarded steps; plan-language ceiling |
| Sagas 1987 | F.5 reversibility classes (via `[CONTRA: saga-as-undo]`) |
| CSS/ETFA + AAS-PDDL 2026 | F.6; minimum-viable-capability-model contribution |
| STL (Bartocci 2018) | alert/monitor rules (FEATURE-5, Phase E/F adjacent) |
| JPL traceability 2025 + SiLA versioning | F.4 |
| RO-Crate / W3C PROV | run-provenance packaging (B.1 extension) |
| Process-mining conformance | per-run conformance report (cross-cutting) |
| PLCSIM manual / Nerve docs / ISG connectors | G.2 / G.3 / G.4 facts |
| Tolio 2017 + CIRP 2025 + IJCIM 2025 | positioning & novelty benchmarks (papers P1/P2 below) |
| **[ORIG] (deliberately unsourced)** | C.7 golden plans; C.9 shadow-as-visualizer; C.3 namespace trap; ghost run; teach-mode recorder (backlog); armed steps (E.8) |
| **[ARBITRATED] (Giorgio)** | upstream branch regeneration (F.3); coordinator last; Plant Gateway module; observer-defined UI (E.4); MiL-behave naming; armed-steps toggle; invariant distillation (G.7); justify-on-merits rule |

# 6. PAPER ROADMAP (formalization targets)
**P1 — "A research-grade multi-agent execution architecture for automated de-remanufacturing"** (venue: RCIM or J. Intelligent Manufacturing; CIRP CMS as conference step). Claims: minimal MAS on real industrial hardware; introspection-based minimum viable capability model (SiLA-2 convergence as evidence); write-and-verify honesty incl. the echo pitfall; typed error taxonomy; empirical failure-mode reporting. Evidence needed: Phase A+B implemented; golden-plan + fault-injection results on MiL-behave; ≥1 hardware campaign. Cite: Tolio 2017, IJCIM 2025 sibling, ETFA CSS, SiLA 2, Leitão.
**P2 — "Mission operations for the factory floor: layered validation and safing for irreversible manufacturing plans"** (position/architecture paper; CIRP Annals-track ambition via lab co-authors). Claims: rule-check→behavioral→geometric→SiL validation ladder with validity envelopes; physical saga (reversibility classes + safing); plan pedigree. Cite: RP-check, JPL FDIR, ESA lessons, Sagas, VC review, FTRT.
**P3 — "Symbiotic execution: Δ-window coordination of virtual and physical de-remanufacturing"** (after G.5/G.6; JMS or IEEE TII). Claims: Δ-unification of VC/shadow/look-ahead; anchor-based divergence; HOLD/resume shared pathway with inspection-triggered replanning. Cite: symbiotic simulation corpus, FTRT, anchor points, online-sim review, shadow mode.
**P4 — "Learning restrictive invariants from virtual plan validation"** (after G.7; RCIM/ETFA). Claims: counterexample-guided distillation, restrictive-only semantics, envelope-scoped validity, amortized validation cost at FMS throughput. `[GAP-FILL — no direct prior found]`.
**P5 — dataset/short paper: "Execution logs of robotic EV-motor disassembly"** (after B.1 + hardware campaigns): the datasets the disassembly-planning literature lacks; plus empirical cost coefficients feeding KBS cost models (link to the lab's planning line).
*All ⚠ author lists must be verified before submission; verification is a one-hour task with the links above.*
