import sqlite3
import json
import logging
import os
from config import settings

# Configurazione Logger
logging.basicConfig(level=settings.LOG_LEVEL, format=settings.LOG_FORMAT)
logger = logging.getLogger("DBManager")

# --- DEBUG PATH ---
# Stampiamo subito dove questo modulo pensa che sia il DB quando viene importato
# print(f"\n[DB_MANAGER IMPORT] DB_PATH calcolato: {settings.DB_PATH}")
# print(f"[DB_MANAGER IMPORT] File esistente? {os.path.exists(settings.DB_PATH)}\n")
# ------------------

def get_connection():
    """
    Helper centrale per connettersi. 
    Serve a vedere ESATTAMENTE quale file stiamo aprendo ogni volta.
    """
    # Stampa di debug per vedere il path in tempo reale
    # print(f"DEBUG SQLITE: Apertura connessione su -> {settings.DB_PATH}")
    return sqlite3.connect(settings.DB_PATH)

def init_db():
    """Inizializza il database con le tabelle necessarie se non esistono."""
    conn = get_connection()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS resources
                 (name TEXT PRIMARY KEY, status TEXT, last_seen TIMESTAMP)''')

    c.execute('''CREATE TABLE IF NOT EXISTS services
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  resource_name TEXT,
                  service_name TEXT,
                  params_json TEXT,
                  ranges_json TEXT,
                  FOREIGN KEY(resource_name) REFERENCES resources(name))''')

    c.execute('''CREATE TABLE IF NOT EXISTS observer_dashboards
                 (name TEXT PRIMARY KEY,
                  dashboard_config TEXT)''')

    conn.commit()
    conn.close()
    logger.info(f"{settings.Icons.SAVE} DB Init su: {settings.DB_PATH}")

def reset_db_state():
    """Reset completo all'avvio."""
    if not os.path.exists(settings.DB_PATH):
        return

    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("DELETE FROM observer_dashboards")
        c.execute("DELETE FROM services")
        c.execute("DELETE FROM resources")
        c.execute("DELETE FROM sqlite_sequence WHERE name='services'")
        conn.commit()
        logger.info(f"{settings.Icons.WARN} DB RESET ESEGUITO SU: {settings.DB_PATH}")
    except Exception as e:
        logger.error(f"Errore reset DB: {e}")
    finally:
        conn.close()

def register_resource(name, services_dict):
    conn = get_connection()
    c = conn.cursor()
    try:
        # Debug spinto: vediamo cosa stiamo scrivendo
        logger.info(f"Tentativo scrittura servizi per {name} su {settings.DB_PATH}...")
        
        c.execute("INSERT OR REPLACE INTO resources (name, status, last_seen) VALUES (?, ?, datetime('now'))", 
                  (name, "ONLINE"))
        
        c.execute("DELETE FROM services WHERE resource_name = ?", (name,))
        
        for srv_name, data_obj in services_dict.items():
            params_list = data_obj.get("params", [])
            contraints_data = data_obj.get("ranges", {})

            params_str = json.dumps(params_list)
            ranges_str = json.dumps(contraints_data)
            c.execute("INSERT INTO services (resource_name, service_name, params_json, ranges_json) VALUES (?, ?, ?, ?)",
                      (name, srv_name, params_str, ranges_str))
            
        conn.commit()
        
        # VERIFICA IMMEDIATA DI SCRITTURA
        c.execute("SELECT count(*) FROM services WHERE resource_name = ?", (name,))
        count = c.fetchone()[0]
        logger.info(f"{settings.Icons.SAVE} Successo! Servizi scritti nel DB per '{name}': {count}")
        
    except Exception as e:
        logger.error(f"{settings.Icons.ERR} Errore DB: {e}")
    finally:
        conn.close()

def update_heartbeat(name: str):
    """Aggiorna last_seen dell'agente al timestamp corrente. Chiamata ad ogni heartbeat ricevuto."""
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("UPDATE resources SET last_seen = datetime('now') WHERE name = ?", (name,))
        conn.commit()
    except Exception as e:
        logger.error(f"{settings.Icons.ERR} Errore aggiornamento heartbeat per '{name}': {e}")
    finally:
        conn.close()

def register_observer(name: str, dashboard_config: dict):
    """Registra un observer: entra in resources per il tracking heartbeat + observer_dashboards per la config UI."""
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("INSERT OR REPLACE INTO resources (name, status, last_seen) VALUES (?, ?, datetime('now'))",
                  (name, "ONLINE"))
        c.execute("INSERT OR REPLACE INTO observer_dashboards (name, dashboard_config) VALUES (?, ?)",
                  (name, json.dumps(dashboard_config)))
        conn.commit()
        logger.info(f"{settings.Icons.SAVE} Observer '{name}' registrato con dashboard config.")
    except Exception as e:
        logger.error(f"{settings.Icons.ERR} Errore registrazione observer: {e}")
    finally:
        conn.close()


def get_all_observers():
    """Restituisce { name: { last_seen, dashboard_config } } per tutti gli observer registrati."""
    if not os.path.exists(settings.DB_PATH):
        return {}
    conn = get_connection()
    c = conn.cursor()
    result = {}
    try:
        c.execute("""
            SELECT r.name, r.last_seen, o.dashboard_config
            FROM resources r
            JOIN observer_dashboards o ON r.name = o.name
        """)
        for name, last_seen, config_json in c.fetchall():
            result[name] = {
                "last_seen": last_seen,
                "dashboard_config": json.loads(config_json) if config_json else {}
            }
    except Exception as e:
        logger.error(f"{settings.Icons.ERR} Errore lettura observers: {e}")
    finally:
        conn.close()
    return result


def unregister_resource(name):
    if not name: return
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("DELETE FROM observer_dashboards WHERE name = ?", (name,))
        c.execute("DELETE FROM services WHERE resource_name = ?", (name,))
        c.execute("DELETE FROM resources WHERE name = ?", (name,))
        conn.commit()
        logger.info(f"{settings.Icons.WARN} Unregister '{name}' su {settings.DB_PATH}")
    except Exception as e:
        logger.error(f"Errore unregister: {e}")
    finally:
        conn.close()

def get_service_schema(resource_name, service_name):
    """
    Recupera i parametri richiesti per un servizio specifico di una risorsa.
    Utilizzato dal parser per validare i masterplan.
    """
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("SELECT params_json FROM services WHERE resource_name = ? AND service_name = ?", 
                  (resource_name, service_name))
        row = c.fetchone()
        if row:
            # Ritorna la lista dei parametri (es: ["axis", "target"])
            return json.loads(row[0])
        else:
            return None
    except Exception as e:
        logger.error(f"{settings.Icons.ERR} Errore lettura schema servizio '{service_name}': {e}")
        return None
    finally:
        conn.close()

# --- FUNZIONI DI LETTURA (Usate dal Parser / System Agent) ---

def get_all_resources_schemas():
    """
    Restituisce lo schema completo di tutte le risorse registrate.
    Struttura: { nome: { "last_seen": str, "services": { SERVIZIO: [params] } } }
    La UI usa last_seen per calcolare lo stato ONLINE/OFFLINE confrontandolo con now.
    """
    if not os.path.exists(settings.DB_PATH):
        return {}

    conn = get_connection()
    c = conn.cursor()
    schemas = {}
    try:
        c.execute("SELECT name, last_seen FROM resources")
        resources = c.fetchall()
        for res_name, last_seen in resources:
            schemas[res_name] = {"last_seen": last_seen, "services": {}}
            c.execute("SELECT service_name, params_json FROM services WHERE resource_name = ?", (res_name,))
            for srv_name, params_str in c.fetchall():
                schemas[res_name]["services"][srv_name] = json.loads(params_str)
    except Exception:
        pass
    finally:
        conn.close()
    return schemas

# Init automatico
if not os.path.exists(settings.DB_PATH):
    init_db()