import asyncio
import websockets
import json
import logging
import sqlite3
import sys
import os
from datetime import datetime, timezone

# --- PATH HACK ---
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
# -----------------------------------

from config import settings
from src.agents.base_agent import WSLogHandler

logging.basicConfig(level=settings.LOG_LEVEL, format=settings.LOG_FORMAT)
logger = logging.getLogger("BaseObserver")


class BaseObserver:
    """
    Classe base per tutti gli Observer.
    Un Observer si connette al server come un agente normale, si sottoscrive
    a un insieme di nodi OPC UA, registra i dati su data_log.db e li
    inoltra alla UI come data_event.
    Non ha servizi eseguibili — osserva solo, non agisce.

    Per creare un observer concreto: istanziare BaseObserver con un nome
    e la lista di nodi da monitorare, oppure sottoclassare per logica custom.
    """

    def __init__(self, uri: str, name: str, nodes_to_watch: list[str]):
        self.uri = uri
        self.name = name
        self.nodes_to_watch = nodes_to_watch
        self.ws = None

    # --- DB ---

    def _init_db(self):
        """Crea la tabella data_log se non esiste. Il DB non viene mai resettato."""
        conn = sqlite3.connect(settings.DATA_LOG_PATH)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS data_log (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                node_name TEXT NOT NULL,
                value     REAL,
                observer  TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    def _log_data(self, node_name: str, value, timestamp: str):
        """Scrive un campione nel DB. Chiamato in modo sincrono dal loop eventi."""
        try:
            float_value = float(value) if value is not None else None
            conn = sqlite3.connect(settings.DATA_LOG_PATH)
            conn.execute(
                "INSERT INTO data_log (timestamp, node_name, value, observer) VALUES (?, ?, ?, ?)",
                (timestamp, node_name, float_value, self.name)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"{settings.Icons.WARN} DB write error [{node_name}]: {e}")

    # --- RETE ---

    def get_dashboard_config(self) -> dict:
        """
        Restituisce la configurazione della dashboard per questo observer.
        Override nelle sottoclassi per personalizzare layout, colori, titoli.
        Schema minimo:
        {
            "window": 200,   # campioni massimi per chart
            "charts": [
                {
                    "id": "unique_key",
                    "title": "Titolo chart",
                    "nodes": [
                        {"name": "node_friendly_name", "label": "Label", "color": "#hex"}
                    ]
                }
            ]
        }
        """
        return {
            "window": 200,
            "charts": [
                {
                    "id": node,
                    "title": node,
                    "nodes": [{"name": node, "label": node, "color": "#22c55e"}]
                }
                for node in self.nodes_to_watch
            ]
        }

    async def connect(self):
        try:
            self.ws = await websockets.connect(self.uri)

            ws_handler = WSLogHandler(self.ws, self.name)
            logger.addHandler(ws_handler)

            self._init_db()

            await self.ws.send(json.dumps({
                "action": "register",
                "type": "observer",
                "name": self.name,
                "dashboard_config": self.get_dashboard_config()
            }))
            logger.info(f"{settings.Icons.NET} Observer '{self.name}' registrato. Nodi: {self.nodes_to_watch}")

            for node in self.nodes_to_watch:
                await self.ws.send(json.dumps({"action": "subscribe", "node": node}))

            asyncio.create_task(self._heartbeat_loop())
            await self._listen_loop()

        except Exception as e:
            logger.error(f"{settings.Icons.ERR} Errore connessione: {e}")

    async def _heartbeat_loop(self):
        while self.ws:
            await asyncio.sleep(settings.HEARTBEAT_INTERVAL)
            try:
                await self.ws.send(json.dumps({"action": "heartbeat"}))
            except Exception:
                break

    async def _listen_loop(self):
        try:
            async for message in self.ws:
                data = json.loads(message)
                if data.get("type") != "update":
                    continue

                node = data.get("node")
                value = data.get("value")
                timestamp = datetime.now(timezone.utc).isoformat()

                # Persistenza locale
                self._log_data(node, value, timestamp)

                # Forward alla UI tramite il server
                await self.ws.send(json.dumps({
                    "action": "data_event",
                    "observer": self.name,
                    "node": node,
                    "value": value,
                    "timestamp": timestamp
                }))

        except websockets.ConnectionClosed:
            logger.warning("Connessione WebSocket chiusa.")
        except Exception as e:
            logger.error(f"{settings.Icons.ERR} Errore nel loop di ascolto: {e}")


async def main(observer: BaseObserver):
    await observer.connect()
