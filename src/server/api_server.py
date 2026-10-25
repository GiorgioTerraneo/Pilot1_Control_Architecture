# api_server.py

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel
import asyncio
import logging
import os
import sqlite3
import typing as t
from opcua_core import OPCUAManager # Import the manager class
from config import settings
from config.node_map import get_node_id, NODES # Importiamo NODES per il reverse lookup
from src.server import db_manager
from src.server.opcua_core import OPCUAManager

app = FastAPI(
    title="OPC UA Manager API",
    description="REST and WebSocket interface for OPC UA data.",
)

logger = logging.getLogger("APIServer")
_ui_log_handler = None  # Inizializzato alla prima connessione UI

# Mappa delle connessioni attive (RAM) — canale di controllo (/ws)
# Struttura: { "NomeRisorsa": {"ws": websocket_object} }
connected_clients: dict = {}

# Registro supervisori connessi (RAM) — separato dalle risorse, non persiste su DB
# Struttura: { "NomeSupervisore": {"ws": websocket, "last_seen": datetime_str} }
connected_supervisors: dict = {}

# Registro client UI connessi — canale di osservazione (/ws/ui)
ui_clients: t.Set[WebSocket] = set()


async def broadcast_to_ui(payload: dict):
    """Invia un messaggio JSON a tutti i client UI connessi su /ws/ui."""
    for ws in list(ui_clients):
        try:
            await ws.send_json(payload)
        except Exception:
            ui_clients.discard(ws)


class UILogHandler(logging.Handler):
    """Inoltra i log del server stesso a tutti i client UI come log_event."""
    def __init__(self, source_name: str):
        super().__init__(level=logging.INFO)
        self.source_name = source_name
        self._loop = None

    def emit(self, record: logging.LogRecord):
        if "Update:" in record.getMessage():
            return
        try:
            loop = self._loop or asyncio.get_event_loop()
            loop.create_task(broadcast_to_ui({
                "type": "log_event",
                "source": self.source_name,
                "level": record.levelname,
                "message": record.getMessage()
            }))
        except RuntimeError:
            pass


# --- Pydantic Models for Data Validation ---

class WritePayload(BaseModel):
    value: t.Any

# # --- REST Endpoints --- per comunicazione tramite HTTP (ex. connessione con un browser)

# @app.get("/read/{name}", summary="Read a node value (latest or cached)")
# async def read_node(name: str):
#     """Retrieves the current value for a node, either a fresh read or from cache."""
#     node = get_node_id(name)
#     if not node:
#         raise HTTPException(status_code=404, detail=f"Unknown node name: {name}")
    
#     manager: OPCUAManager = app.state.opcua_manager
#     value = await manager.read(node)
    
#     if value is None:
#         raise HTTPException(status_code=503, detail="Could not read value, check OPC UA connection.")
        
#     return {"node": name, "value": value}

# @app.post("/write/{name}", summary="Write a value to an OPC UA node")
# async def write_node(name: str, payload: WritePayload):
#     """Writes the provided value to the specified OPC UA node."""
#     node = get_node_id(name)
#     if not node:
#         raise HTTPException(status_code=404, detail=f"Unknown node name: {name}")

#     manager: OPCUAManager = app.state.opcua_manager
#     ok = await manager.write(node, payload.value)
    
#     if not ok:
#         raise HTTPException(status_code=500, detail="Write failed, check server connection and permissions.")
        
#     return {"status": "ok", "node": name, "value": payload.value}


# @app.post("/dispatch/{resource_name}")
# async def dispatch_subplan(resource_name: str, payload: t.Dict[str, t.Any]):
#     """Forwards a command/subplan payload to a registered WebSocket client."""
#     ws = connected_clients.get(resource_name)
#     if not ws:
#         raise HTTPException(status_code=404, detail=f"Resource not connected: {resource_name}")
#     try:
#         await ws.send_json({"type": "command", "payload": payload})
#         return {"status": "dispatched", "resource": resource_name}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# --- REST Endpoints ---

@app.get("/resources", summary="Lista risorse registrate con stato e servizi")
async def get_resources_http():
    """Restituisce lo schema completo di tutte le risorse dal DB, incluso last_seen per il calcolo ONLINE/OFFLINE."""
    return db_manager.get_all_resources_schemas()

@app.get("/status", summary="Stato dei supervisori connessi")
async def get_supervisors_status():
    """Restituisce la lista dei supervisori con last_seen per il calcolo ONLINE/OFFLINE lato UI."""
    return {
        name: {"last_seen": info["last_seen"]}
        for name, info in connected_supervisors.items()
    }

@app.get("/plans", summary="Lista dei file masterplan disponibili")
async def get_plans():
    """Restituisce i file .txt presenti nella cartella plans/."""
    try:
        files = [f for f in os.listdir(settings.PLANS_DIR) if f.endswith(".txt")]
        return {"plans": sorted(files)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/observers", summary="Lista degli observer registrati con dashboard config")
async def get_observers():
    """Restituisce { name: { last_seen, dashboard_config } } per tutti gli observer."""
    return db_manager.get_all_observers()


@app.get("/data/recent", summary="Ultimi campioni per observer dal data_log.db")
async def get_recent_data(observer: str, limit: int = 200):
    """Restituisce gli ultimi N campioni per nodo per l'observer specificato."""
    try:
        conn = sqlite3.connect(settings.DATA_LOG_PATH)
        rows = conn.execute(
            "SELECT node_name, timestamp, value FROM data_log WHERE observer = ? ORDER BY id ASC",
            (observer,)
        ).fetchall()
        conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    result: dict = {}
    for node_name, ts, value in rows:
        result.setdefault(node_name, []).append({"ts": ts, "value": value})
    for key in result:
        result[key] = result[key][-limit:]
    return result


@app.get("/plans/{plan_name}", summary="Contenuto di un file masterplan")
async def get_plan_content(plan_name: str):
    """Restituisce il contenuto testuale di un masterplan. Usato dalla UI per la guardia pre-lancio."""
    plan_path = os.path.join(settings.PLANS_DIR, plan_name)
    if not os.path.isfile(plan_path):
        raise HTTPException(status_code=404, detail=f"Piano non trovato: {plan_name}")
    with open(plan_path, 'r') as f:
        return {"content": f.read()}


# --- WebSocket Endpoint for Live Updates ---

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket for bi-directional communication: 
    read/write commands, and live subscription updates.
    """
    await websocket.accept()
    subscriptions: t.Set[t.Tuple[str, t.Callable]] = set()
    manager: OPCUAManager = app.state.opcua_manager
    current_resource_name = None

    # Define the callback function that closes over the current WebSocket connection
    async def ws_cb(node_id: str, value: t.Any):
        """Sends the update to this specific WebSocket connection."""
       
        friendly_name = next((name for name, id_str in NODES.items() if id_str == node_id), node_id)
        
        try:
            await websocket.send_json({"type": "update", "node": friendly_name, "value": value})
        except Exception:
            pass # Gestito dal cleanup

    try:
        await websocket.send_json({"type": "status", "message": "Connected to OPC UA Manager"})
        current_resource_name = None # Identificativo di questa connessione

        while True:
            data = await websocket.receive_json()
            action = data.get("action")

            # --- 1. REGISTRAZIONE RISORSA ---
            if action == "register":
                current_resource_name = data.get("name")
                client_type = data.get("type", "resource")  # "supervisor" | "resource"
                services = data.get("services", {})

                if client_type == "supervisor":
                    # I supervisori vivono solo in RAM: non hanno servizi da persistere su DB
                    connected_supervisors[current_resource_name] = {
                        "ws": websocket,
                        "last_seen": None
                    }
                    connected_clients[current_resource_name] = {"ws": websocket}
                elif client_type == "observer":
                    # Observer: RAM + resources (heartbeat) + observer_dashboards (config UI)
                    connected_clients[current_resource_name] = {"ws": websocket}
                    dashboard_config = data.get("dashboard_config", {})
                    db_manager.register_observer(current_resource_name, dashboard_config)
                else:
                    # Resource agent: RAM + DB
                    connected_clients[current_resource_name] = {"ws": websocket}
                    db_manager.register_resource(current_resource_name, services)

                print(f"{settings.Icons.NET} Client registrato: {current_resource_name} (tipo: {client_type})")
                continue

            # --- 2. ORCHESTRAZIONE: Da System Agent a Resource Agent ---
            elif action == "dispatch_command":
                target = data.get("target")
                payload = data.get("payload")

                if target in connected_clients:
                    target_ws = connected_clients[target]["ws"]
                    await target_ws.send_json({"type": "command", "payload": payload})
                    print(f"{settings.Icons.OK} SERVER: Dispatch -> {target}")
                else:
                    print(f"{settings.Icons.ERR} SERVER: Target '{target}' non trovato.")
                    await websocket.send_json({"type": "error", "message": f"Target {target} offline"})
                continue

            # --- 3. FEEDBACK: da Resource Agent a System Agent (Supervisor) ---
            elif action == "feedback":
                # Inoltra il feedback al supervisore se connesso, incluso il campo message per gli errori
                if "SUPERVISOR" in connected_clients:
                    await connected_clients["SUPERVISOR"]["ws"].send_json({
                        "type": "feedback",
                        "resource": current_resource_name,
                        "status": data.get("status"),
                        "message": data.get("message")
                    })
                continue

            # --- 4. PROGRESS EVENT: da SystemAgent alla UI ---
            elif action == "progress_event":
                # Redistribuisce l'evento di avanzamento piano a tutti i client UI
                await broadcast_to_ui({"type": "progress_event", **{k: v for k, v in data.items() if k != "action"}})
                continue

            # --- 4b. LOG EVENT: da qualsiasi agente alla UI ---
            elif action == "log_event":
                await broadcast_to_ui({"type": "log_event", **{k: v for k, v in data.items() if k != "action"}})
                continue

            # --- 4c. DATA EVENT: da un Observer alla UI (dati OPC UA per dashboard) ---
            elif action == "data_event":
                await broadcast_to_ui({"type": "data_event", **{k: v for k, v in data.items() if k != "action"}})
                continue

            # --- 6. HEARTBEAT: da Resource Agent o Supervisore al Server ---
            elif action == "heartbeat":
                if current_resource_name in connected_supervisors:
                    # Supervisore: aggiorna timestamp in RAM (non su DB)
                    from datetime import datetime, timezone
                    connected_supervisors[current_resource_name]["last_seen"] = \
                        datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                elif current_resource_name:
                    # Resource agent: aggiorna last_seen su DB
                    db_manager.update_heartbeat(current_resource_name)
                continue

            # --- 7. LISTA RISORSE (System Agent -> Richiesta) ---
            elif action == "get_resources":
                # Recupera lo schema completo dal DB
                all_schemas = db_manager.get_all_resources_schemas()
                
                # Filtra per mostrare solo chi è effettivamente connesso ora (opzionale)
                # Ma per ora mandiamo tutto ciò che è nel DB per completezza
                await websocket.send_json({"type": "resource_list", "data": all_schemas})
                continue

            # --- 5. LOGICA COMANDI OPC UA STANDARD ---
            node_name = data.get("node")
            node_id = get_node_id(node_name)

            if not node_id and action in ["subscribe", "unsubscribe", "read", "write"]:
                # await websocket.send_json({"type": "error", "message": f"Unknown node: {node_name}"})
                continue

            if action == "subscribe":
                manager.subscribe(node_id, ws_cb)
                subscriptions.add((node_id, ws_cb))
                # await websocket.send_json({"type": "status", "message": f"Subscribed to {node_name}"})

            elif action == "unsubscribe":
                manager.unsubscribe(node_id, ws_cb)
                subscriptions.discard((node_id, ws_cb))
                # await websocket.send_json({"type": "status", "message": f"Unsubscribed from {node_name}"})

            elif action == "read":
                val = await manager.read(node_id)
                await websocket.send_json({"type": "read_response", "node": node_name, "value": val})

            elif action == "write":
                ok = await manager.write(node_id, data["value"])
                status = "ok" if ok else "error"
                await websocket.send_json({"type": "write_response", "status": status, "node": node_name})

            # else:
            #     await websocket.send_json({"type": "error", "message": f"Unknown action: {action}"})
                
    except WebSocketDisconnect:
        print(f"{settings.Icons.ERR} Disconnessione socket rilevata.")
        
        # --- LOGICA ANTI-RACE CONDITION ---
        should_cleanup = False
        
        # Controlliamo se la risorsa è registrata
        if current_resource_name and current_resource_name in connected_clients:
            
            # Recuperiamo quale websocket è considerato "attivo" dal server
            active_socket = connected_clients[current_resource_name]["ws"]
            
            # SE E SOLO SE il socket che si sta chiudendo è quello attivo...
            if active_socket == websocket:
                should_cleanup = True
                del connected_clients[current_resource_name]
            else:
                # Se sono diversi, significa che è caduta una VECCHIA connessione "zombie"
                # mentre una nuova è già subentrata. NON DOBBIAMO CANCELLARE IL DB.
                print(f"{settings.Icons.WARN} Ignorato cleanup per '{current_resource_name}': connessione obsoleta.")

        if should_cleanup:
            if current_resource_name in connected_supervisors:
                # Supervisore: rimuove solo dalla RAM
                del connected_supervisors[current_resource_name]
            else:
                # Resource agent: rimuove anche dal DB
                db_manager.unregister_resource(current_resource_name)

    except Exception as e:
        print(f"Error in WebSocket communication: {e}")
        # (Opzionale) Puoi replicare la logica should_cleanup anche qui per sicurezza
        
    finally:
        for node_id, cb in list(subscriptions):
            manager.unsubscribe(node_id, cb)


@app.websocket("/ws/ui")
async def websocket_ui_endpoint(websocket: WebSocket):
    """
    Canale WebSocket dedicato ai client UI (canale di osservazione).
    Riceve eventi broadcast dal server (progress, log, heartbeat status).
    I comandi dalla UI (lancio piano, abort) arrivano qui e vengono tradotti
    in azioni sul canale di controllo (/ws) — implementato in 1.3.
    """
    global _ui_log_handler
    await websocket.accept()
    ui_clients.add(websocket)

    # Al primo client UI, attacca l'handler che inoltra i log del server stesso alla UI
    if _ui_log_handler is None:
        _ui_log_handler = UILogHandler("APIServer")
        logging.getLogger().addHandler(_ui_log_handler)

    logger.info(f"{settings.Icons.NET} Client UI connesso. Totale: {len(ui_clients)}")
    try:
        async for message in websocket.iter_json():
            action = message.get("action")

            if action == "launch_plan":
                # Inoltra il comando di lancio al SUPERVISOR
                plan_name = message.get("plan")
                if plan_name and "SUPERVISOR" in connected_clients:
                    await connected_clients["SUPERVISOR"]["ws"].send_json({
                        "type": "command",
                        "command": "launch_plan",
                        "plan": plan_name
                    })
                elif "SUPERVISOR" not in connected_clients:
                    await websocket.send_json({"type": "error", "message": "Nessun supervisore connesso"})

            elif action == "abort_plan":
                # Inoltra il comando di abort al SUPERVISOR
                if "SUPERVISOR" in connected_clients:
                    await connected_clients["SUPERVISOR"]["ws"].send_json({
                        "type": "command",
                        "command": "abort_plan"
                    })

    except WebSocketDisconnect:
        pass
    finally:
        ui_clients.discard(websocket)
        logger.info(f"{settings.Icons.WARN} Client UI disconnesso. Totale: {len(ui_clients)}")
