import os

# --- PATHS ---
# Calcola la root del progetto (due livelli sopra questo file)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "services_database.db")
DATA_LOG_PATH = os.path.join(BASE_DIR, "data_log.db")
PLANS_DIR = os.path.join(BASE_DIR, "plans")

# --- RETE & CONNESSIONI ---
# Configurazione Server API
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 8000
WS_URI = f"ws://localhost:{SERVER_PORT}/ws"

# Configurazione PLC (Target Reale)
OPC_SERVER_URL = "opc.tcp://192.168.0.200:4842"

# --- SYSTEM SETTINGS ---
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s | %(name)s | %(message)s"
DEFAULT_TIMEOUT = 360.0 # Secondi per le verify_target
AGENT_RESPONSE_TIMEOUT = 30.0 # Secondi di attesa massima per il feedback di un resource agent
HEARTBEAT_INTERVAL = 5.0  # Secondi tra un heartbeat e il successivo
HEARTBEAT_TIMEOUT  = 15.0 # Secondi oltre i quali un agente è considerato OFFLINE

# --- ICONE ASCII (Standardizzato) ---
class Icons:
    OK = "✓"        # Successo
    ERR = "✕"       # Errore
    IN = "↓"        # Input / Ricevuto
    START = "▷"     # Avvio
    STEP = ">"      # Step singolo
    END = "■"       # Fine / Stop
    WAIT = ""      # Attesa
    BUSY = "⋯"      # Monitoraggio / Busy
    NET = "<⋯>"       # Connessione / Network
    MSG = "<⋯"       # Messaggio
    LIST = "⋮⋮"      # Lista / Tabella
    SAVE = "↴"      # Salvataggio DB
    FB = "↳"        # Feedback
    DOC = "[⋯]"       # Documento / Masterplan
    LOAD = "↺"      # Caricamento
    ACT = "→"       # Azione diretta
    WARN = "!"      # Warning
    RES = "◇"       # Risorsa generica
    SEARCH = "⋱"    # Ricerca / Introspection


    # ‖⁞››◇⟨◇⟩↳↴↷↓