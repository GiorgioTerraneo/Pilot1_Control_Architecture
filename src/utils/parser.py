import logging
import os
import sys

# --- PATH HACK ---
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
# -----------------------------------

from config import settings
from src.server import db_manager

# Configurazione logger standard
logging.basicConfig(level=settings.LOG_LEVEL, format=settings.LOG_FORMAT)
logger = logging.getLogger("Parser")

def try_parse_number(value):
    """Converte stringhe in numeri se possibile."""
    try:
        if "." in value: return float(value)
        return int(value)
    except ValueError: return value

def parse_line_with_schema(line, resource_name):
    """
    Parsa una singola riga di comando (es: 'MOVE | x | 100')
    verificandola contro lo schema nel DB.
    """
    line = line.strip()
    if not line or line.startswith("#"): return None

    parts = [p.strip() for p in line.split('|')]
    action = parts[0].upper() # Es. MOVE

    # 1. Recupera lo schema dal DB
    param_names = db_manager.get_service_schema(resource_name, action)
    
    if not param_names:
        logger.error(f"{settings.Icons.ERR} Servizio '{action}' non trovato nel DB per '{resource_name}'")
        return None

    # 2. Gestione argomenti
    # Se il comando non ha argomenti nel file, ma lo schema ne vuole 0 -> ok
    if len(parts) == 1:
        values = []
    else:
        # Se c'è una parte argomenti, splittala per virgola
        # Es: "100.0, 50.0" -> ["100.0", "50.0"]
        raw_args = parts[1]
        values = [v.strip() for v in raw_args.split(',')]

    # 3. Validazione numero parametri
    if len(values) != len(param_names):
        logger.error(f"{settings.Icons.ERR} Errore '{action}': attesi {len(param_names)} params ({param_names}), trovati {len(values)}.")
        return None

    # 4. Creazione dizionario
    params_dict = {k: try_parse_number(v) for k, v in zip(param_names, values)}
    
    return {
        "type": action.lower(), # Es. 'move'
        "params": params_dict
    }

def parse_subplan_file(file_path, resource_name):
    """Legge un intero file di subplan e ritorna la lista di steps."""
    steps = []
    if not os.path.exists(file_path):
        logger.error(f"File subplan non trovato: {file_path}")
        return None

    try:
        with open(file_path, 'r') as f:
            for line in f:
                step = parse_line_with_schema(line, resource_name)
                if step:
                    steps.append(step)
        return steps
    except Exception as e:
        logger.error(f"{settings.Icons.ERR} Errore lettura subplan {file_path}: {e}")
        return None

def parse_master_line(line):
    """
    Analizza una riga del MASTERPLAN.
    Formato: RESOURCE | ACTION | [ARGS]
    """
    line = line.strip()
    if not line or line.startswith("#"): return None

    parts = [p.strip() for p in line.split('|')]
    if len(parts) < 2: 
        logger.warning(f"{settings.Icons.WARN} Riga malformata: {line}")
        return None

    resource_name = parts[0]
    command = parts[1].upper()

    # CASO A: Esecuzione File (RUN_FILE)
    if command == "RUN_FILE":
        if len(parts) < 3:
            logger.error(f"{settings.Icons.ERR} RUN_FILE richiede nome file.")
            return None
        
        file_name = parts[2]
        return {
            "type": "subplan_call",
            "target": resource_name,
            "file": file_name
        }

    # CASO B: Comando Diretto (es. PICK, MOVE)
    else:
        # Comando diretto (es. PICK | TOOL1)
        # Ricostruiamo la riga come se fosse dentro un subplan (ACTION | ARGS)
        # Es: "Doosan | PICK | TOOL1" -> passiamo "PICK | TOOL1" al parser di linea
        sub_line = "|".join(parts[1:]) 
        step = parse_line_with_schema(sub_line, resource_name)
        
        if step:
            return {
                "type": "direct_command",
                "target": resource_name,
                "step": step
            }
    
    return None