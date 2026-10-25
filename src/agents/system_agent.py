import asyncio
import websockets
import json
import logging
import sys
import os

# --- PATH HACK ---
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
# -----------------------------------

from config import settings
from src.utils.parser import parse_master_line, parse_subplan_file
from src.agents.base_agent import WSLogHandler						 

logging.basicConfig(level=settings.LOG_LEVEL, format=settings.LOG_FORMAT)
logger = logging.getLogger("SystemAgent")

class SystemAgent:
    def __init__(self, uri):
        self.uri = uri
        self.ws = None
        self.running = True

        # Gestione attese: { "NomeRisorsa": FutureObject }
        self.pending_feedbacks = {}

        # Evento di abort: impostato dalla UI per interrompere il piano corrente
        self._abort_event = asyncio.Event()

    async def connect(self):
        try:
            self.ws = await websockets.connect(self.uri)

            ws_handler = WSLogHandler(self.ws, "SUPERVISOR")
            logger.addHandler(ws_handler)

            await self.ws.send(json.dumps({"action": "register", "name": "SUPERVISOR", "type": "supervisor"}))
            logger.info(f"{settings.Icons.NET} Connesso a {self.uri}")
            asyncio.create_task(self.listen_for_messages())
            asyncio.create_task(self._heartbeat_loop())
        except Exception as e:
            logger.error(f"{settings.Icons.ERR} Errore connessione: {e}")
            self.running = False

    async def _heartbeat_loop(self):
        """Invia un heartbeat periodico al server per segnalare che il supervisore è attivo."""
        while self.running and self.ws:
            await asyncio.sleep(settings.HEARTBEAT_INTERVAL)
            try:
                await self.ws.send(json.dumps({"action": "heartbeat"}))
            except Exception:
                break

    async def listen_for_messages(self):
        try:
            async for message in self.ws:
                data = json.loads(message)
                msg_type = data.get("type") # Leggiamo il tipo per comodità

                # 1. GESTIONE LISTA RISORSE
                if msg_type == "resource_list":
                    resources = data["data"]
                    print(f"\n{settings.Icons.LIST} RISORSE ({len(resources)})")
                    for name, info in resources.items():
                        # info ha formato {"last_seen": ..., "services": {...}}
                        services = info.get("services", {}) if isinstance(info, dict) else {}
                        last_seen = info.get("last_seen", "N/A") if isinstance(info, dict) else "N/A"
                        print(f"{settings.Icons.RES} {name} | ultimo heartbeat: {last_seen}")
                        print(f"  ↳ Servizi: {list(services.keys())}")
                    print("-" * 20)

                # 2. GESTIONE FEEDBACK
                # Il server invia "feedback", quindi dobbiamo controllare quello!
                elif msg_type == "feedback": 
                    status = data.get("status")
                    target = data.get("resource") # Il server invia "resource"

                    logger.info(f"{settings.Icons.FB} Feedback da {target}: {status}")
                    
                    # LOGICA DI SBLOCCO DEL MASTERPLAN
                    # Controlliamo se c'è qualcuno in attesa (execute_masterplan) per questa risorsa
                    if target in self.pending_feedbacks:
                        future = self.pending_feedbacks[target]

                        # Se il semaforo è ancora rosso (non done), lo facciamo diventare verde
                        if not future.done():
                            if status == "SUBPLAN_COMPLETED":
                                future.set_result(True) # Sblocca l'await
                            elif status == "ERROR":
                                # Usa il messaggio originale dall'agente se disponibile
                                error_msg = data.get("message") or f"Errore remoto su {target}"
                                future.set_exception(Exception(error_msg))
                    else:
                        # Debug utile: se arriviamo qui significa che il feedback è arrivato
                        # ma il nome della risorsa non combacia con quello che stiamo aspettando
                        print(f"{settings.Icons.WARN} Warning: Feedback ricevuto per '{target}' ma nessuno lo stava aspettando.")

                # 3. COMANDI DALLA UI (via server)
                elif msg_type == "command":
                    cmd = data.get("command")
                    if cmd == "launch_plan":
                        plan_name = data.get("plan")
                        if plan_name:
                            logger.info(f"{settings.Icons.DOC} Lancio piano da UI: {plan_name}")
                            asyncio.create_task(self.execute_masterplan(plan_name))
                    elif cmd == "abort_plan":
                        logger.info(f"{settings.Icons.WARN} Abort richiesto dalla UI.")
                        self._abort_event.set()

                # 4. GESTIONE ERRORI GENERICI
                elif msg_type == "error":
                    logger.error(f"{settings.Icons.ERR} SERVER: {data.get('message')}")

        except Exception as e:
            logger.error(f"Errore ricezione: {e}")

    async def _send_progress(self, **kwargs):
        """Invia un evento di avanzamento al server, che lo redistribuisce ai client UI."""
        if self.ws:
            await self.ws.send(json.dumps({"action": "progress_event", **kwargs}))

    async def execute_masterplan(self, file_path):
        """
        Esegue un masterplan step per step. Supporta abort asincrono via _abort_event.
        Invia eventi di avanzamento al server (redistribuiti alla UI via broadcast_to_ui).
        """
        # Reset abort event: un abort del piano precedente non deve bloccare il nuovo
        self._abort_event.clear()

        if not os.path.exists(file_path):
            alternative_path = os.path.join(settings.PLANS_DIR, file_path)
            if os.path.exists(alternative_path):
                file_path = alternative_path
            else:
                logger.error(f"{settings.Icons.ERR} File non trovato: {file_path}")
                return

        logger.info(f"{settings.Icons.DOC} AVVIO MASTERPLAN: {file_path}")

        with open(file_path, 'r') as f:
            lines = f.readlines()

        # Pre-scansione per contare gli step effettivi (esclude righe vuote e commenti)
        total_steps = sum(1 for line in lines if parse_master_line(line) is not None)
        await self._send_progress(status="started", plan=os.path.basename(file_path), total=total_steps)

        step_counter = 0
        plan_status = "finished"  # Aggiornato a "aborted" in caso di break

        for line in lines:
            cmd_data = parse_master_line(line)
            if not cmd_data:
                continue

            step_counter += 1
            target = cmd_data['target']
            payload = {}

            # Preparazione payload
            if cmd_data['type'] == "subplan_call":
                sub_name = cmd_data['file']
                sub_path = os.path.join(settings.PLANS_DIR, sub_name)
                logger.info(f"{settings.Icons.LOAD} Step {step_counter}: Carico '{sub_name}' per {target}")
                steps = parse_subplan_file(sub_path, target)
                if not steps:
                    logger.error(f"{settings.Icons.ERR} Subplan invalido. Stop.")
                    await self._send_progress(status="error", step=step_counter, total=total_steps,
                                              message="Subplan invalido o non trovato")
                    plan_status = "aborted"
                    break
                payload = {"action": "execute_subplan", "steps": steps}

            elif cmd_data['type'] == "direct_command":
                logger.info(f"{settings.Icons.ACT} Step {step_counter}: Comando diretto -> {target}")
                payload = {"action": "execute_subplan", "steps": [cmd_data['step']]}

            # Notifica UI: step avviato
            service = cmd_data.get('step', {}).get('type', cmd_data.get('file', '?')).upper()
            await self._send_progress(status="running", step=step_counter, total=total_steps,
                                      target=target, service=service)

            # Invio comando
            await self.ws.send(json.dumps({
                "action": "dispatch_command",
                "target": target,
                "payload": payload
            }))

            logger.info(f"{settings.Icons.WAIT} Attendo {target}...")
            loop = asyncio.get_running_loop()
            feedback_future = loop.create_future()
            self.pending_feedbacks[target] = feedback_future
            abort_task = None

            try:
                # Attesa concorrente: feedback dell'agente OPPURE richiesta di abort
                abort_task = asyncio.create_task(self._abort_event.wait())
                done, pending = await asyncio.wait(
                    {feedback_future, abort_task},
                    return_when=asyncio.FIRST_COMPLETED,
                    timeout=settings.AGENT_RESPONSE_TIMEOUT
                )
                for t in pending:
                    t.cancel()

                if not done:
                    # Timeout: nessuno dei due ha risposto in tempo
                    raise asyncio.TimeoutError()

                if abort_task in done:
                    # L'utente ha premuto Abort dalla UI
                    logger.info(f"{settings.Icons.WARN} Piano interrotto dall'utente.")
                    plan_status = "aborted"
                    break

                # Il feedback_future ha vinto — rilancia l'eccezione se il risultato è un errore
                feedback_future.result()

                logger.info(f"{settings.Icons.OK} Step {step_counter} completato.")
                await self._send_progress(status="done", step=step_counter, total=total_steps)

            except asyncio.TimeoutError:
                logger.error(f"{settings.Icons.ERR} Timeout: {target} non ha risposto in tempo.")
                await self._send_progress(status="error", step=step_counter, total=total_steps,
                                          message=f"Timeout: {target} non ha risposto in {settings.AGENT_RESPONSE_TIMEOUT}s")
                plan_status = "aborted"
                break

            except Exception as e:
                logger.error(f"{settings.Icons.ERR} Errore durante step {step_counter}: {e}")
                await self._send_progress(status="error", step=step_counter, total=total_steps, message=str(e))
                plan_status = "aborted"
                break

            finally:
                if abort_task:
                    abort_task.cancel()
                self.pending_feedbacks.pop(target, None)

        logger.info(f"{settings.Icons.END} MASTERPLAN TERMINATO.")
        await self._send_progress(status=plan_status, total=total_steps)

    async def terminal_interface(self):
        """Interfaccia interattiva da terminale."""
        print("\n--- SYSTEM AGENT CONSOLE ---")
        print("Comandi: 'run' (esegui piano), 'list' (vedi risorse), 'exit' (chiudi)")
        
        loop = asyncio.get_running_loop() # Usa get_running_loop invece di get_event_loop
        
        while self.running:
            try:
                # Usa run_in_executor per non bloccare il loop mentre aspetti l'input
                # Nota: Questo metodo è standard e non richiede librerie esterne
                print("\nCOMMAND> ", end='', flush=True)
                cmd_line = await loop.run_in_executor(None, sys.stdin.readline)
                
                if not cmd_line:
                    break # Gestione EOF
                
                parts = cmd_line.strip().split(maxsplit=1)
                if not parts: continue
                
                cmd = parts[0].lower()

                if cmd == "run":
                    # Qui usiamo input() bloccante perché siamo dentro l'executor o chiediamo il path
                    # Per semplicità, chiediamo il path in modo asincrono allo stesso modo
                    print("Path Masterplan: ", end='', flush=True)
                    path = await loop.run_in_executor(None, sys.stdin.readline)
                    if path:
                        await self.execute_masterplan(path.strip())
                    
                elif cmd == "list":
                    # Invia la richiesta e torna subito al loop. 
                    # La risposta verrà stampata da 'listen_for_messages'
                    await self.ws.send(json.dumps({"action": "get_resources"}))
                    # Diamo un attimo di tempo al server per rispondere prima di ristampare il prompt
                    await asyncio.sleep(0.5) 

                elif cmd == "exit":
                    logger.info("Sconnessione e chiusura...")
                    self.running = False
                    await self.ws.close()
                    break

            except Exception as e:
                logger.error(f"Errore nel loop terminale: {e}")
                break


async def main():
    """
    Avvio del SystemAgent.
    Default: modalità headless (comandi via UI su /ws/ui).
    Con flag --cli: attiva l'interfaccia da terminale per debug/emergenze.
    """
    agent = SystemAgent(settings.WS_URI)
    await agent.connect()

    if not agent.running:
        return

    if "--cli" in sys.argv:
        logger.info("Modalità CLI attiva.")
        await agent.terminal_interface()
    else:
        logger.info("Modalità headless attiva. Comandi via UI (--cli per terminale).")
        while agent.running:
            await asyncio.sleep(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nArresto manuale (Ctrl+C).")