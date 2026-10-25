# PIANO D'AZIONE — System Executor v3.2

## Revisioni rispetto a v3.0

### v3.1 (validazione Claude Code)
- **PG-1 eliminato:** il PLC accetta `ua.VariantType.Double`, non è un bug
- **0.1 riformulato:** include fix doppio feedback da `_send_error()` + inoltro campo `message` al SUPERVISOR
- **0.2 riformulato:** il filtraggio messaggi è già OK; il problema reale è `await feedback_future` senza timeout → riformulato come "timeout sull'attesa feedback"
- **0.3 precisato:** validazione range va in `disassembly_machine_v2.py`, non è generalizzabile in `base_agent.py`
- **0.4 precisato:** riusare colonna `last_seen` esistente invece di aggiungere `last_heartbeat`
- **1.2 precisato:** usare contatore step eseguiti, non indice riga (che include commenti/vuote)
- **1.3 aggiunto:** SystemAgent headless di default, CLI come fallback con flag `--cli`
- **1.4 precisato:** log degli agenti via WebSocket (`action: "log_event"`), non via handler Python condiviso (processi separati)
- **1.5 precisato:** DB SQLite separato (`data_log.db`), mai resettato; dati on-change sufficienti per dashboard
- **Log/Dati separati:** aggiornamenti OPC UA ad alta frequenza vanno solo alla dashboard come dati grafici, mai nel pannello log UI
- **Ordine Fase 0:** rivisto secondo SA-5 (0.1 → 0.3 → 0.2 → 0.4)
- **PG-2 integrato:** la UI (1.3) deve bloccare il lancio se le risorse richieste non sono tutte online
- **SA-4 integrato:** `RETRY_ATTEMPTS` zombie in `settings.py` da rimuovere ora, riaggiungere in 2.5

### v3.2 (validazione range a due livelli)
- **0.3 confermato come safety net agent-side:** la validazione range nell'agente è l'ultimo baluardo prima dell'hardware — usa i range locali del costruttore (Single Source of Truth)
- **1.3 esteso con validazione anticipata DB-side:** aggiunta validazione dei parametri contro `ranges_json` nel DB prima di inviare il comando. I log di entrambi i livelli devono esplicitare l'origine del controllo (`"range check: agent-side"` vs `"range check: DB-side"`) per diagnostica chiara

## Legenda

- **[DEMO]** = Prioritario per la demo live
- Dipendenze tra parentesi: `(→ richiede X.Y)`

---

## FASE 0 — STABILIZZAZIONE RAPIDA (pre-demo, giorni 1-2)

Interventi piccoli e ad alto impatto sulla stabilità. Necessari prima di costruire la UI.
**Ordine di implementazione interno:** 0.1 → 0.3 → 0.2 → 0.4

### 0.1 Propagazione errori parametri + fix doppio feedback [B2]
**Effort: S** | **File:** `api_server.py`, `system_agent.py`, `disassembly_machine_v2.py`

Tre fix coordinati:
1. `api_server.py` riga ~140: aggiungere `"message": data.get("message")` nel JSON inoltrato al SUPERVISOR (oggi il campo viene omesso)
2. `system_agent.py` riga ~70: leggere il campo `message` dal JSON ricevuto invece di usare testo hardcoded nell'eccezione
3. `disassembly_machine_v2.py`: `_send_error()` deve solo loggare e fare `raise ValueError(msg)` — **rimuovere** la chiamata a `_send_feedback()` interna; sarà `execute_sequence()` a mandare il feedback ERROR (oggi ne manda due)

Pulizia associata: rimuovere `RETRY_ATTEMPTS = 3` da `settings.py` (costante zombie, non usata da nessuna parte — verrà reintrodotta in 2.5 quando implementeremo il retry).

### 0.2 Timeout sull'attesa feedback [B3]
**Effort: S** | **File:** `system_agent.py`, `settings.py`

Il problema non è il filtraggio dei messaggi (già corretto), ma `execute_masterplan()` che fa `await feedback_future` senza timeout. Se un agente crasha senza inviare feedback, il masterplan si blocca indefinitamente.

**Fix:** sostituire `await feedback_future` con `await asyncio.wait_for(feedback_future, timeout=settings.AGENT_RESPONSE_TIMEOUT)`. Il blocco `except asyncio.TimeoutError` esiste già nel codice ma non è raggiungibile senza `wait_for` — diventa attivo con questa modifica.

Aggiungere a `settings.py`: `AGENT_RESPONSE_TIMEOUT = 30` (secondi).

### 0.3 Validazione range a runtime — safety net agent-side [B7]
**Effort: S** | **File:** `disassembly_machine_v2.py`

I range sono dichiarati nei costruttori delle classi `AxisElectrical` (righe 72-103) ma `set_params()` e `move_to_position()` non li controllano. Aggiungere check esplicito: prima di ogni scrittura OPC UA, verificare che il valore sia entro `self.ranges[chiave]["min"]` e `self.ranges[chiave]["max"]`. Se fuori range, `raise ValueError` con messaggio chiaro — `execute_sequence()` cattura e propaga come feedback ERROR (grazie al fix di 0.1).

**Questo è il livello di safety net (agent-side):** usa i range locali del costruttore, che sono la Single Source of Truth. È l'ultimo controllo prima dell'hardware fisico — protegge la macchina anche se il DB è desincronizzato o il comando arriva da un canale imprevisto.

**Il secondo livello di validazione (DB-side, anticipata)** verrà aggiunto in 1.3 come parte della guardia pre-lancio: i parametri del masterplan saranno verificati contro `ranges_json` nel DB prima ancora di inviare il comando all'agente. Quando entrambi i livelli saranno attivi, i messaggi di errore dovranno esplicitare l'origine: `"range check: agent-side"` vs `"range check: DB-side"`.

**Nota:** la validazione agent-side non è generalizzabile in `base_agent.py` perché la struttura dei range è specifica di `AxisElectrical`. Va nel file dell'agente specifico.

### 0.4 Heartbeat [D1]
**Effort: M** | **File:** `base_agent.py`, `api_server.py`, `db_manager.py`, `settings.py`

Ogni ResourceAgent invia un heartbeat periodico al server. Il server aggiorna la colonna `last_seen` già esistente nella tabella `resources` (oggi aggiornata solo alla registrazione — si riusa senza modifiche allo schema).

- `base_agent.py`: task asyncio `_heartbeat_loop()` avviato in `connect()`, invia `{"action": "heartbeat"}` ogni `HEARTBEAT_INTERVAL` secondi
- `api_server.py`: handler per `action == "heartbeat"` che chiama `db_manager.update_heartbeat(name)`
- `db_manager.py`: nuova funzione `update_heartbeat(name)` → `UPDATE resources SET last_seen = datetime('now') WHERE name = ?`
- `settings.py`: `HEARTBEAT_INTERVAL = 5`, `HEARTBEAT_TIMEOUT = 15`

Il SystemAgent (e la futura UI) determinano lo stato: se `now - last_seen > HEARTBEAT_TIMEOUT` → OFFLINE.

**Nota:** al primo avvio, `last_seen` è il momento del register — prevedere un grace period pari a `HEARTBEAT_TIMEOUT` prima di marcare un agente appena registrato come OFFLINE.

---

## FASE 1 — WEB UI + OSSERVABILITÀ (demo-ready, giorni 2-4) [DEMO]

### 1.0 Infrastruttura Web UI [C1/C2/C3 prerequisito]
**Effort: L** | **File:** `api_server.py`, `main.py`, nuova cartella `src/ui/`

Setup dell'infrastruttura:
- `api_server.py`: nuovo endpoint `@app.websocket("/ws/ui")`, registro separato `ui_clients: set[WebSocket]`, funzione helper `async def broadcast_to_ui(payload: dict)` usata da tutti i punti che devono notificare la UI
- `main.py`: `app.mount("/", StaticFiles(directory="src/ui/build", html=True), name="static")` — **DOPO** la definizione degli endpoint WebSocket (altrimenti il catch-all `html=True` intercetta le route WS)
- Progetto React (Vite) in `src/ui/`

**Principio architetturale:** `/ws` resta esclusivo per SystemAgent e ResourceAgent (canale di controllo). `/ws/ui` è per i client UI (canale di osservazione). La UI non invia mai comandi direttamente su `/ws` — li invia su `/ws/ui` e l'API Server li traduce internamente.

### 1.1 Pannello di controllo sistema [C1] [DEMO]
**Effort: M** | **Dipende da:** 0.4, 1.0 | **File:** `db_manager.py`, `api_server.py`, frontend

Vista d'insieme: lista agenti con stato (online/offline/busy), servizi registrati, ultimo heartbeat.

Estendere `get_all_resources_schemas()` in `db_manager.py` con JOIN su tabella `resources` per includere `status` e `last_seen`. La UI calcola localmente se l'agente è OFFLINE confrontando `last_seen` con `now`.

### 1.2 Monitor esecuzione piano [C2] [DEMO]
**Effort: M** | **Dipende da:** 1.0 | **File:** `system_agent.py`, `api_server.py`, frontend

Il SystemAgent invia eventi di avanzamento al server dopo ogni dispatch e dopo ogni feedback:
```
{"action": "progress_event", "step": N, "total": M, "target": "...", "status": "running|done|error"}
```
`api_server.py`: handler `action == "progress_event"` chiama `broadcast_to_ui()`.

**Attenzione:** usare un contatore separato per gli step effettivamente eseguiti (escludendo righe vuote e commenti), non l'indice di riga del file.

### 1.3 Lancio e controllo piani dalla UI [C3] [DEMO]
**Effort: L** | **Dipende da:** 0.2, 1.0, 1.2 | **File:** `system_agent.py`, `api_server.py`, frontend

**SystemAgent headless di default.** La CLI resta come fallback attivabile con `--cli` per debug/emergenze.

Funzionalità:
- **Discovery piani:** nuovo endpoint REST `GET /plans` in `api_server.py` che legge `os.listdir(settings.PLANS_DIR)` e restituisce lista `.txt`
- **Lancio:** `action == "launch_plan"` nel handler `/ws/ui` → il server inoltra al SystemAgent come comando WebSocket → il SystemAgent avvia `execute_masterplan()` come task asyncio
- **Abort:** `self._abort_event = asyncio.Event()` nel SystemAgent; in `execute_masterplan()`, `asyncio.wait([feedback_future, abort_event.wait()], return_when=FIRST_COMPLETED)`; se vince l'abort, break pulito
- **Guardia pre-lancio:** la UI deve verificare (via pannello 1.1) che tutte le risorse menzionate nel masterplan siano online prima di permettere il lancio. Questo risolve PG-2 (dipendenza temporale parser/DB).
- **Validazione anticipata range (DB-side):** prima di inviare ciascun comando all'agente, verificare i parametri contro `ranges_json` nel DB. Se fuori range, il comando non viene inviato e l'errore è mostrato nella UI con prefisso `"range check: DB-side"`. Questo è il secondo livello di validazione — il primo (agent-side, 0.3) resta come safety net. Entrambi i livelli devono esplicitare l'origine del controllo nei log per diagnostica chiara.

### 1.4 Log aggregato nella UI [C6] [DEMO]
**Effort: M** | **Dipende da:** 1.0 | **File:** `base_agent.py`, `system_agent.py`, `api_server.py`

Ogni componente (agenti + server) invia una copia dei propri log al server come messaggio WebSocket `{"action": "log_event", "source": "...", "level": "INFO|WARNING|ERROR", "message": "..."}`. Il server li ridistribuisce ai client UI via `broadcast_to_ui()`.

**Separazione log/dati:** gli aggiornamenti OPC UA ad alta frequenza ("Update: mill_axis_prs_pos_attuale → 335.26") **non** vanno nel pannello log. Vanno esclusivamente all'Observer (1.5) come dati per la dashboard. Il pannello log riceve solo messaggi di stato: inizio/fine sequenza, errori, comandi ricevuti, registrazioni.

**Nota tecnica:** gli agenti girano in processi separati — i log passano via WebSocket come normali messaggi, non via logging handler Python condiviso. Il server, avendo accesso diretto a `ui_clients`, può usare un handler in-process per i propri log.

I terminali dei processi **restano attivi** e continuano a stampare come oggi — la UI è un canale aggiuntivo, non sostitutivo.

### 1.5 Data logging Observer [C4] [DEMO]
**Effort: M** | **Dipende da:** 1.0 | **File:** nuovo `src/agents/observer.py`, `settings.py`

Nuovo agente "Observer" che si registra al server e si sottoscrive ai nodi OPC UA di interesse tramite le azioni `subscribe` e `read` già esistenti in `/ws`. Registra i dati con timestamp in un **DB SQLite separato** (`data_log.db`), **mai resettato** (a differenza di `services_database.db` che viene resettato a ogni avvio).

Schema time-series: `(timestamp TEXT, node_name TEXT, value REAL)`.

I dati arrivano on-change dal data poller (100ms, notifica solo se il valore cambia). Questo è sufficiente per la dashboard: durante un movimento si ricevono ~3 aggiornamenti/secondo; quando l'asse è fermo, nessun dato (il che è corretto — il grafico mostra una linea piatta).

L'Observer inoltra i dati anche su `/ws/ui` via il server per la dashboard live.

### 1.6 Dashboard live [C5] [DEMO]
**Effort: M** | **Dipende da:** 1.5 | **File:** frontend `src/ui/`

Sezione della Web UI con grafici real-time: posizione assi nel tempo, temperatura, velocità. Aggiornamento continuo via `/ws/ui`. Libreria: Recharts (leggera, React-native).

Dati storici caricati da `data_log.db` al caricamento pagina (endpoint REST); aggiornamenti live via WebSocket.

---

## FASE 2 — ROBUSTEZZA DI RETE (post-demo)

### 2.1 Timeout semantico [B1]
**Effort: M** | **Dipende da:** 0.1, 0.4 | **File:** `base_agent.py`, `system_agent.py`, `settings.py`

Tre livelli di timeout distinti:
1. **Write-confirm** (~5s): la scrittura OPC UA è stata recepita dal PLC. Già separabile in `write_and_verify` (`base_agent.py:266`).
2. **Execution** (configurabile per servizio): la macchina ha completato l'operazione. Dipende dal tipo di movimento e dalla distanza.
3. **Agent-response** (~30s): il ResourceAgent ha risposto al server. Già implementato in 0.2 come `AGENT_RESPONSE_TIMEOUT`.

### 2.2 Reconnect WebSocket [B4]
**Effort: M** | **File:** `base_agent.py`, `system_agent.py`

Riconnessione automatica con backoff esponenziale (1s, 2s, 4s, 8s, max 60s). `base_agent.py:129-132` ha già il commento placeholder `# INSERIRE LOOP DI RICONNESSIONE`. `system_agent.py:33-35` idem.

### 2.3 Reconnect OPC UA [B6]
**Effort: M-L** | **Dipende da:** 2.2 | **File:** `opcua_core.py`

Implementare `_monitor_connection()` (oggi stub vuoto, `opcua_core.py:212-216`). Task asyncio che verifica periodicamente la connessione al PLC, tenta riconnessione con backoff. **Dopo riconnessione, richiamare `_resolve_nodes()`** perché gli oggetti Node di asyncua non sopravvivono alla disconnessione.

### 2.4 Ripresa esecuzione post-disconnessione [B5]
**Effort: L** | **Dipende da:** 2.2, 2.3 | **File:** `base_agent.py`, `system_agent.py`

SystemAgent e ResourceAgent mantengono in memoria l'indice dello step corrente. Alla riconnessione: ritentano l'ultimo comando e proseguono.

**Nota idempotenza:** MOVE e SET_PARAMS sono idempotenti (re-invio safe). Operazioni con effetti fisici irreversibili (es. futura ACTIVATE pinze) non lo sono — per queste servirà un meccanismo di verifica stato pre-retry.

### 2.5 Retry configurabile [D3]
**Effort: M** | **File:** `base_agent.py`, `settings.py`

Su errore di un comando singolo (a connessione intatta), il sistema riprova N volte con backoff prima di dichiarare fallimento. Reintrodurre `RETRY_ATTEMPTS` in `settings.py` (rimosso in 0.1 perché zombie) e usarlo in `execute_sequence()` come wrapper attorno all'esecuzione del singolo step.

### 2.6 Log monitor per risorsa/supervisore (UI)
**Effort: M** | **Dipende da:** 1.4

Evoluzione del pannello Log aggregato (1.4): sistema a finestre/tab che mostra un canale di log dedicato per ciascuna risorsa e per il supervisore. Ogni tab filtra automaticamente i messaggi della propria sorgente e mantiene uno scroll indipendente.

Opzioni di layout da valutare: tab orizzontali affiancati al LogPanel, oppure pannelli flottanti apribili/chiudibili. L'infrastruttura WebSocket è già quella di 1.4 (`log_event` + source); serve solo la parte React.

---

## FASE 3 — QUALITÀ E DOCUMENTAZIONE

### 3.1 Validazione nomi variabili [A1]
**Effort: S** | Creare `tests/` e script che verifica coerenza `node_map.py` ↔ classi agenti.

### 3.2 Docstrings e type hints [A2]
**Effort: M** | Type hints stretti su `opcua_core.py`, `db_manager.py`, `parser.py`. Docstrings su funzioni pubbliche.

### 3.3 PROTOCOL.md [A3]
**Effort: S** | Documentazione formale JSON payload WebSocket, inclusi i nuovi messaggi (heartbeat, progress_event, log_event, launch_plan). Documentare anche che il PLC accetta `ua.VariantType.Double` per nodi Siemens Real (per futuri sviluppatori).

### 3.4 Service Catalog con metadata [A4]
**Effort: M** | Estendere schema DB `services` con unità di misura, descrizione, tipo dato. Richiede DROP+CREATE (SQLite), aggiornare `get_service_schema()` e generazione schema in `base_agent.py`.

### 3.5 MockOPCUAClient [A5]
**Effort: M** | Classe mock con stessa interfaccia di OPCUAClient: connect, disconnect, read, write, get_node_by_id. Attivabile con `--sim`.

### 3.6 Test di resilienza [A6]
**Effort: M** | **Dipende da:** 3.5 | Chaos Monkey: comandi errati, risorse inesistenti, parametri fuori range.

---

## FASE 4 — EVOLUZIONI ARCHITETTURALI (medio termine)

### 4.1 Event bus interno [D6]
**Effort: L** | Refactoring routing API Server da if/elif a pub/sub con topic. **Trigger:** quando il numero di elif supera ~8-10 (con le aggiunte delle fasi precedenti, ci si avvicina).

### 4.2 Esecuzione parallela intra-masterplan [D2]
**Effort: L** | Blocchi `PARALLEL { ... }` nel masterplan, `asyncio.gather` in `execute_masterplan()`. La decisione di cosa parallelizzare è responsabilità del System (De)production Planner.

### 4.3 Multi-masterplan / multi-prodotto [evoluzione D2]
**Effort: XL** | N masterplan concorrenti su risorse condivise. Resource locking nell'API Server. Architettura consigliata: N istanze SystemAgent con coordinatore a monte.

### 4.4 Resource Agent per DOOSAN e SEIT [D4]
**Effort: L per agente** | Nodi mappati, specifiche macchina da fornire. **Prerequisito:** risolvere PG-3 (`_resolve_nodes` fail-fast) rendendo la risoluzione non-fatal per nodi di macchine non collegate.

---

## Problemi globali da monitorare

| ID | Problema | Quando risolverlo |
|---|---|---|
| PG-2 | Parser consulta DB a runtime; se agente non connesso, parsing fallisce | Mitigato da guardia pre-lancio in 1.3 |
| PG-3 | `_resolve_nodes()` fail-fast blocca server se un nodo non esiste nel PLC | Prima di 4.4 (aggiunta DOOSAN/SEIT) |

---

## Dipendenze (grafo)

```
0.1 (errori + doppio feedback) 
  → 0.3 (range validation)
    → 0.2 (timeout feedback)
      → 0.4 (heartbeat)
        → 1.0 (infra UI)
           ├→ 1.1 (pannello) ← 0.4
           ├→ 1.2 (monitor)
           │    → 1.3 (lancio UI) ← 0.2
           ├→ 1.4 (log aggregato)
           ├→ 1.5 (observer) → 1.6 (dashboard)

2.1 (timeout semantico) ← 0.1, 0.4
2.2 (WS reconnect) → 2.3 (OPC UA reconnect) → 2.4 (ripresa exec)
2.5 (retry)

3.5 (mock) → 3.6 (chaos monkey)

4.4 (DOOSAN/SEIT) ← risolvi PG-3 prima
4.2 (parallelo) → 4.3 (multi-masterplan)
```
