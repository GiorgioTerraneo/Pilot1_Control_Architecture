import asyncio
import csv
import os
import sys
import json
import logging
import websockets
from datetime import datetime, timezone

# --- PATH HACK ---
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
# -----------------------------------

from config import settings
from src.agents.base_observer import BaseObserver, main


class PrsCaricoCsvObserver(BaseObserver):
    """
    Observer che registra posizione asse PRS e cella di carico su file CSV (.txt).
    Ogni update scritto dal server genera una riga con i valori correnti di entrambi i nodi.
    Il file viene creato nella cartella logs/ con timestamp nel nome.
    """

    NAME = "PrsCaricoCsvObserver"

    NODES = [
        "mill_axis_prs_pos_attuale",
        "mill_carico",
    ]

    def __init__(self, uri: str):
        super().__init__(uri, self.NAME, self.NODES)
        self._latest = {node: None for node in self.NODES}

        self._log_dir = os.path.join(settings.BASE_DIR, "logs")
        self._csv_path = None
        self._csv_file = None
        self._csv_writer = None

    def _open_csv(self):
        """Crea il file CSV con timestamp del PRIMO dato ricevuto nel nome."""
        os.makedirs(self._log_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._csv_path = os.path.join(self._log_dir, f"prs_carico_{ts}.txt")
        self._csv_file = open(self._csv_path, "w", newline="", encoding="utf-8")
        self._csv_writer = csv.writer(self._csv_file)
        self._csv_writer.writerow(["timestamp_s", "prs_pos_attuale_mm", "carico_kg"])
        self._csv_file.flush()
        logging.getLogger(self.NAME).info(
            f"{settings.Icons.SAVE} CSV aperto: {self._csv_path}"
        )

    async def connect(self):
        try:
            await super().connect()
        finally:
            if self._csv_file and not self._csv_file.closed:
                self._csv_file.close()
                logging.getLogger(self.NAME).info(
                    f"{settings.Icons.SAVE} CSV chiuso: {self._csv_path}"
                )

    async def _listen_loop(self):
        """
        Override del loop base: oltre a persistere su DB e inviare data_event alla UI,
        scrive una riga CSV ad ogni aggiornamento ricevuto.
        """
        logger = logging.getLogger(self.NAME)
        try:
            async for message in self.ws:
                data = json.loads(message)
                if data.get("type") != "update":
                    continue

                node = data.get("node")
                value = data.get("value")
                timestamp = datetime.now(timezone.utc).isoformat()

                # Aggiorna lo stato locale
                if node in self._latest:
                    self._latest[node] = value

                # Persistenza DB (comportamento base)
                self._log_data(node, value, timestamp)

                # Forward alla UI (comportamento base)
                await self.ws.send(json.dumps({
                    "action": "data_event",
                    "observer": self.name,
                    "node": node,
                    "value": value,
                    "timestamp": timestamp
                }))

                # Apre il CSV al primo dato ricevuto, usando il timestamp di quel dato nel nome file
                if self._csv_writer is None:
                    self._open_csv()

                # Scrittura CSV: riga con timestamp e valori correnti di entrambi i nodi
                if self._csv_writer is not None:
                    self._csv_writer.writerow([
                        timestamp,
                        self._latest["mill_axis_prs_pos_attuale"],
                        self._latest["mill_carico"],
                    ])
                    self._csv_file.flush()

        except websockets.ConnectionClosed:
            logger.warning("Connessione WebSocket chiusa.")
        except Exception as e:
            logger.error(f"{settings.Icons.ERR} Errore nel loop di ascolto: {e}")


if __name__ == "__main__":
    observer = PrsCaricoCsvObserver(settings.WS_URI)
    try:
        asyncio.run(main(observer))
    except KeyboardInterrupt:
        print("\nArresto manuale (Ctrl+C).")
