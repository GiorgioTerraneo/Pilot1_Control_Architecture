import sys
import os
import asyncio
import uvicorn
import logging
from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles

# --- 1. PATH HACK (CRUCIALE: DEVE ESSERE QUI) ---
# Aggiungiamo la root del progetto al path PRIMA di importare qualsiasi modulo interno
# Altrimenti 'config' e 'src' potrebbero non essere risolti correttamente o puntare a percorsi errati.
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# --- 2. ORA IMPORTIAMO I MODULI DEL PROGETTO ---
# L'ordine ora è sicuro perché sys.path include la root del progetto
from config import settings
from src.server import db_manager 
from src.server.api_server import app
from src.server.opcua_core import OPCUAManager

# Configurazione Logging
logging.basicConfig(level=settings.LOG_LEVEL, format=settings.LOG_FORMAT)
logger = logging.getLogger("MainRunner")

@asynccontextmanager
async def lifespan(fastapi_app):
    """
    Gestisce il ciclo di vita dell'applicazione.
    """
    print(f"\n{settings.Icons.START} SYSTEM STARTUP (LIFESPAN)...")

    # --- 3. RESET DEL DATABASE ---
    # Inizializza se non esiste
    if not os.path.exists(settings.DB_PATH):
        db_manager.init_db()
    
    # Esegue il reset per pulire le vecchie sessioni
    # Ora siamo sicuri che db_manager stia puntando allo stesso file settings.DB_PATH del main
    db_manager.reset_db_state() 
    logger.info(f"{settings.Icons.WARN} Database resettato all'avvio.")

    # --- 4. AVVIO OPC UA ---
    logger.info(f"{settings.Icons.START} Inizializzazione OPC UA Manager su {settings.OPC_SERVER_URL}")
    opc = OPCUAManager(settings.OPC_SERVER_URL)
    
    try:
        await opc.start()
        fastapi_app.state.opcua_manager = opc
        logger.info(f"{settings.Icons.OK} LIFESPAN: OPCUA Manager collegato all'app.")
        yield
    finally:
        logger.info(f"{settings.Icons.END} LIFESPAN: Spegnimento OPCUA Manager...")
        await opc.stop()

# Colleghiamo il lifespan all'app FastAPI
app.router.lifespan_context = lifespan

# Mount UI statica — DEVE essere dopo gli endpoint WebSocket per evitare che
# il catch-all html=True intercetti le route /ws e /ws/ui
_ui_dist = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "src", "ui", "dist")
if os.path.isdir(_ui_dist):
    app.mount("/", StaticFiles(directory=_ui_dist, html=True), name="ui")

if __name__ == "__main__":
    logger.info(f"{settings.Icons.NET} Avvio del server Uvicorn su http://{settings.SERVER_HOST}:{settings.SERVER_PORT}")
    try:
        uvicorn.run(
            app, 
            host=settings.SERVER_HOST,
            port=settings.SERVER_PORT,
            log_level="info"
        )
    except Exception as e:
        logger.critical(f"{settings.Icons.ERR} Errore fatale: {e}")