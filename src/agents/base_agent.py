import asyncio
import websockets
import json
import logging
import inspect
import math
import sys
import os

# --- PATH HACK ---
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
# -----------------------------------

from config import settings


# Logger
logging.basicConfig(level=settings.LOG_LEVEL, format=settings.LOG_FORMAT)
logger = logging.getLogger("BaseAgent")


class WSLogHandler(logging.Handler):
    """
    Handler di logging che invia i messaggi al server via WebSocket come log_event.
    Filtra i messaggi di aggiornamento OPC UA ad alta frequenza (Update:) — vanno solo
    all'Observer come dati, non nel pannello log della UI.
    """
    def __init__(self, ws, source_name: str):
        super().__init__(level=logging.INFO)
        self.ws = ws
        self.source_name = source_name
        self._loop = asyncio.get_event_loop()

    def emit(self, record: logging.LogRecord):
        # Filtra aggiornamenti OPC UA ad alta frequenza
        if "Update:" in record.getMessage():
            return
        try:
            self._loop.create_task(self._send(record.levelname, record.getMessage()))
        except RuntimeError:
            pass  # Loop non attivo, ignora silenziosamente

    async def _send(self, level: str, message: str):
        try:
            await self.ws.send(json.dumps({
                "action": "log_event",
                "source": self.source_name,
                "level": level,
                "message": message
            }))
        except Exception:
            pass

class OPCUAMachineClient:
    def __init__(self, uri, name):
        self.uri = uri
        self.name = name
        self.ws = None
        self.pending_responses = {}

    def get_components_for_param(self, param_name):
        """
        Restituisce un dizionario {nome_comp: oggetto_comp} dei componenti
        che possono essere selezionati tramite 'param_name'.
        Es. se param_name="axis", ritorna self.axes
        Se il parametro non è un selettore, ritorna {}
        """
        return {}

    def get_service_ranges(self):
        """
        Costruisce automaticamente i vincoli scansionando i servizi e i componenti.
        """
        ranges = {}
        methods = inspect.getmembers(self, predicate=inspect.iscoroutinefunction)
        
        for name, method in methods:
            if not name.startswith('service_'): continue
            
            service_key = name.replace('service_', '').upper()
            sig = inspect.signature(method)
            params = list(sig.parameters.keys())
            
            srv_ranges = {}
            
            for p in params:
                # 1. Identifichiamo se 'p' è un selettore di componenti (es. "axis")
                comps = self.get_components_for_param(p)
                
                if comps:
                    # È un selettore! I valori possibili sono i nomi dei componenti.
                    srv_ranges[p] = list(comps.keys()) # Enum ["x", "y", ...]
                    
                    # 2. Cerchiamo vincoli condizionali per gli ALTRI parametri
                    # basati sui ranges definiti dentro questi componenti.
                    for other_p in params:
                        if other_p == p: continue
                        
                        # Costruiamo la mappa dei valori (es. target_map)
                        val_map = {}
                        for c_name, c_obj in comps.items():
                            # Se il componente ha 'ranges' e definisce un rangee per 'other_p'
                            if hasattr(c_obj, 'ranges') and other_p in c_obj.ranges:
                                val_map[c_name] = c_obj.ranges[other_p]
                        
                        if val_map:
                            # Aggiungiamo al JSON finale come "nomeparametro_map"
                            srv_ranges[f"{other_p}_map"] = val_map
            
            if srv_ranges:
                ranges[service_key] = srv_ranges
                
        return ranges

    def get_service_schema(self):
        """
        Genera dizionario dei servizi della risorsa da inviare al API Server che aggiornerà con essi l'ontologia.
        Trova i metodi 'service_' e legge i loro argomenti.
        """
        schema = {}

        all_ranges = self.get_service_ranges()

        # Trova tutti i metodi della classe che sono coroutine (async def)
        methods = inspect.getmembers(self, predicate=inspect.iscoroutinefunction)
        
        for name, method in methods:
            if name.startswith('service_'):
                # Nome servizio pulito: service_move -> MOVE
                service_key = name.replace('service_', '').upper()
                
                # Estrae la firma del metodo (i nomi dei parametri)
                sig = inspect.signature(method)
                params = [p.name for p in sig.parameters.values()]
                
                schema[service_key] = {
                    "params": params,
                    "ranges": all_ranges.get(service_key, {})
                }
                
        return schema

    async def connect(self):
        try:
            self.ws = await websockets.connect(self.uri)
													
            # Attacca il WSLogHandler al logger locale per inviare log alla UI
            ws_handler = WSLogHandler(self.ws, self.name)
            logger.addHandler(ws_handler)

            # --- Generazione Schema ---
            service_schema = self.get_service_schema()

            # Registrazione inviando lo Schema (Dizionario)
            await self.ws.send(json.dumps({
                "action": "register",
                "name": self.name,
                "services": service_schema
            }))
            logger.info(f"{settings.Icons.NET} Agente '{self.name}' registrato. Servizi esposti: {len(service_schema)}")

            # Avvia il loop heartbeat in background
            asyncio.create_task(self._heartbeat_loop())

            # Avvia il loop di ascolto
            await self._listen_loop()


        except Exception as e:
            logger.error(f"{settings.Icons.ERR} Errore connessione/registrazione al server: {e}")
            # INSERIRE LOOP DI RICONNESSIONE
            pass

    async def _heartbeat_loop(self):
        """Invia un heartbeat periodico al server per segnalare che l'agente è attivo."""
        while self.ws:
            await asyncio.sleep(settings.HEARTBEAT_INTERVAL)
            try:
                await self.ws.send(json.dumps({"action": "heartbeat"}))
            except Exception:
                break  # Il loop di ascolto gestirà la disconnessione

    async def _listen_loop(self):
        """Loop principale che smista i messaggi in arrivo."""
        try:
            async for message in self.ws:
                data = json.loads(message)
                msg_type = data.get("type")

                # 1. Update valori (OPC UA Subscriptions)
                if msg_type == "update":
                    node = data.get("node")
                    val = data.get("value")
                    # Log debug (o info) per vedere cosa succede
                    logger.info(f"{settings.Icons.BUSY} Update: {node} -> {val}")
                    
                    if node in self.pending_responses:
                        future = self.pending_responses[node]
                        if not future.done():
                            future.set_result(val)

                # 2. Risposte a Read/Write dirette
                elif msg_type == "read_response":
                    node = data.get("node")
                    if node in self.pending_responses:
                        future = self.pending_responses[node]
                        if not future.done():
                            future.set_result(data.get("value"))

                elif msg_type == "write_response":
                    node = data.get("node")
                    write_key = f"__write__{node}"
                    if write_key in self.pending_responses:
                        future = self.pending_responses[write_key]
                        if not future.done():
                            future.set_result(data.get("status"))

                # 3. Comandi dal System Agent 
                elif msg_type == "command":
                    payload = data.get("payload")
                    action_wrapper = payload.get("action") # es. 'execute_subplan'
                    steps = payload.get("steps", [])

                    logger.info(f"{settings.Icons.IN} RX Packet: {action_wrapper} | Steps: {len(steps)}")
                    
                    # Logica unificata: tutto e' una sequenza di step (anche se e' 1 solo)
                    if action_wrapper == "execute_subplan":
                        # Lancia task background per non bloccare il websocket (ping/pong)
                        asyncio.create_task(self.execute_sequence(steps))
                    else:
                        logger.warning(f"Azione wrapper sconosciuta: {action_wrapper}")

        except websockets.ConnectionClosed:
            logger.warning("Connessione WebSocket chiusa dal server.")

        except Exception as e:
            logger.error(f"Errore critico nel loop di ascolto: {e}")

    async def execute_sequence(self, steps):
        """
        Motore che trasforma i dati JSON in chiamate ai metodi della classe figlia.
        E' il motore di esecuzione dei passi.
        Fondamentale: deve SEMPRE restituire un feedback (OK o ERROR), 
        altrimenti il System Agent rimane bloccato.
        Es: {"type": "move"} --> self.service_move(...)
        """

        if len(steps) > 1:
            logger.info(f"{settings.Icons.START} Start Sequence ({len(steps)} passi)...")
        else:
            logger.info(f"{settings.Icons.START} Start Single Action...")
        
        for i, step in enumerate(steps):
            action_type = step.get("type").lower() # es. "move"
            service_name = f"service_{action_type}" # es. "service_move"
            params = step.get("params", {})

            # 1. Controllo esistenza servizio
            if not hasattr(self, service_name):
                logger.error(f"{settings.Icons.ERR} Step {i+1}: Servizio '{action_type}' non supportato")
                await self._send_feedback("ERROR", f"Service '{action_type}' not found")
                return # Interrompe tutto il piano

            # 2. Esecuzione
            method = getattr(self, service_name)
            try:
                # param_types = {k: type(v).__name__ for k, v in params.items()}
                # logger.info(f"{settings.Icons.STEP} [{i+1}/{len(steps)}] Exec: {action_type.upper()} {params} Types: {param_types}")
                logger.info(f"{settings.Icons.STEP} [{i+1}/{len(steps)}] Exec: {action_type.upper()} {params}")
                await method(**params) # Chiama la funzione (es. move_to_position)

            except Exception as e:
                logger.error(f"{settings.Icons.ERR} Errore durante esecuzione {action_type}: {e}")
                await self._send_feedback("ERROR", str(e))
                return # Interrompe il piano su errore


        # 3. Successo Finale
        logger.info(f"{settings.Icons.END} Sequenza Completata con successo.")
        await self._send_feedback("SUBPLAN_COMPLETED")

    async def _send_feedback(self, status, message=None):
        """Helper per inviare feedback al supervisore."""
        if self.ws:
            payload = {
                "action": "feedback", 
                "status": status, 
                "resource": self.name
            }
            if message:
                payload["message"] = message
            
            await self.ws.send(json.dumps(payload))


    # --- METODI BASE (read/write/wait) ---

    async def service_wait(self, seconds):
        """Servizio di pausa standard (utile nei piani)."""
        logger.info(f"{settings.Icons.WAIT} Attesa {seconds}s...")
        await asyncio.sleep(seconds)

    async def write_and_verify(self, node_name, target_value):
        """Scrive e aspetta che il valore sia confermato dal server."""
        await self.ws.send(json.dumps({"action": "subscribe", "node": node_name}))

        # Registra il future per la write_response PRIMA di inviare la scrittura
        write_key = f"__write__{node_name}"
        write_future = asyncio.get_running_loop().create_future()
        self.pending_responses[write_key] = write_future

        await self.ws.send(json.dumps({"action": "write", "node": node_name, "value": target_value}))

        try:
            status = await asyncio.wait_for(write_future, timeout=settings.DEFAULT_TIMEOUT)
            if status != "ok":
                raise RuntimeError(f"Scrittura OPC UA fallita su '{node_name}' (nodo inesistente o permesso negato)")
        finally:
            self.pending_responses.pop(write_key, None)

        await self.verify_target(node_name, target_value)

    async def verify_target(self, node_name, target_value, tolerance=0.05):
        """Blocca l'esecuzione finche' il valore non e' raggiunto."""
        # Assicuriamoci di essere iscritti
        await self.ws.send(json.dumps({"action": "subscribe", "node": node_name}))

        # logger.info(f"Wait target: {node_name} == {target_value}")

        start_time = asyncio.get_running_loop().time()
        outer_timeout = settings.DEFAULT_TIMEOUT  # Tempo massimo totale prima di dichiarare TimeoutError
        poll_interval = 2.0  # Tempo massimo di attesa per un singolo update: se scade, forza una lettura esplicita

        # Lettura immediata iniziale: evita race condition tra l'invio della subscribe
        # e la registrazione del future — se l'asse è già al target, lo rileva subito
        await self.ws.send(json.dumps({"action": "read", "node": node_name}))

        while True:
            # Controllo Timeout
            if asyncio.get_running_loop().time() - start_time > outer_timeout:
                raise TimeoutError(f"Timeout waiting for {node_name} to become {target_value}")

            future = asyncio.get_running_loop().create_future()
            self.pending_responses[node_name] = future

            try:
                # Aspettiamo il prossimo update dal server
                val = await asyncio.wait_for(future, timeout=poll_interval)
                match = False
                try:
                    if isinstance(target_value, (int, float)) and isinstance(val, (int, float)):
                        if math.isclose(val, target_value, abs_tol=tolerance): match = True
                    elif val == target_value: match = True
                except: pass
                if match: break

            except asyncio.TimeoutError:
                # Se il socket non manda update, proviamo una lettura esplicita per sbloccare
                await self.ws.send(json.dumps({"action": "read", "node": node_name}))
            finally:
                self.pending_responses.pop(node_name, None)

    async def read_variable(self, node_name):
        """Lettura one-shot."""
        future = asyncio.get_running_loop().create_future()
        self.pending_responses[node_name] = future
        await self.ws.send(json.dumps({"action": "read", "node": node_name}))
        try:
            return await asyncio.wait_for(future, timeout=settings.DEFAULT_TIMEOUT)
        finally:
            self.pending_responses.pop(node_name, None)