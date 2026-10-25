
import asyncio
import logging
import typing as t
import contextlib 
from config import settings
from config.node_map import NODES 
from src.server.opcua_client import OPCUAClient 
from asyncua import Client, ua

logger = logging.getLogger("OPCUAManager")
logger.setLevel(settings.LOG_LEVEL)

Callback = t.Callable[[str, t.Any], t.Union[None, t.Awaitable[None]]]

class OPCUAManager:
    def __init__(self, url: str):
        self.url = url
        self.client = OPCUAClient(url)
        self.lock = asyncio.Lock()
        self.cache: t.Dict[str, t.Any] = {}
        self.subscribers: t.Dict[str, t.Set[Callback]] = {} 
        self._running = False
        self._reconnect_task: t.Optional[asyncio.Task] = None
        
        # Mappa per memorizzare gli OGGETTI NODE risolti (Stringa ID -> Oggetto Node)
        self.resolved_nodes: t.Dict[str, t.Any] = {}
        # Mappa del tipo OPC UA effettivo per ogni nodo (letto dal PLC all'avvio)
        self.node_variant_types: t.Dict[str, ua.VariantType] = {}
        self._system_node_id = "i=2255" # NodeId di Root per la verifica della connessione

    async def _resolve_nodes(self):
        """Traduce le stringhe di Node ID definite in node_map.py in oggetti Node reali e ne legge il tipo."""
        self.resolved_nodes.clear()
        self.node_variant_types.clear()

        # Iteriamo su TUTTI i nodi definiti in node_map.py (il dizionario NODES)
        for name, node_id_string in NODES.items():
            try:
                # 1. Usa la funzione del client per ottenere l'oggetto Node
                node_obj = await self.client.get_node_by_id(node_id_string)

                # 2. Memorizza l'oggetto Node usando la STRINGA ID come chiave
                self.resolved_nodes[node_id_string] = node_obj

                # 3. Leggi il tipo OPC UA effettivo dal PLC e cachelo
                try:
                    dv = await node_obj.read_data_value()
                    self.node_variant_types[node_id_string] = dv.Value.VariantType
                    logger.debug(f"Resolved node '{name}' type={dv.Value.VariantType.name}")
                except Exception:
                    logger.debug(f"Resolved node '{name}' (tipo non leggibile)")

            except Exception:
                logger.error(f"{settings.Icons.ERR} FATAL: Impossibile risolvere nodo: {node_id_string}")
                raise

    # async def _is_connected(self) -> bool:
    #     """Verifica se la connessione è attiva."""
    #     try:
    #          # Ottiene il nodo Root direttamente dal client asyncua e tenta la lettura
    #          root_node = self.client.client.get_node(self._system_node_id)
    #          await root_node.read_value() 
    #          return True
    #     except Exception:
    #          return False

    async def start(self):
        logger.info(f"{settings.Icons.START} Avvio OPCUAManager...")
        await self.client.connect()
        # RISOLUZIONE DEI NODI DOPO LA CONNESSIONE
        await self._resolve_nodes() 
        
        self._running = True
        self._reconnect_task = asyncio.create_task(self._monitor_connection())
        self._poller_task = asyncio.create_task(self._data_poller())
        logger.info(f"{settings.Icons.OK} OPCUAManager operativo.")
    
    async def stop(self):
        self._running = False
        if hasattr(self, '_poller_task'): self._poller_task.cancel()
        if self._reconnect_task: self._reconnect_task.cancel()
        await self.client.disconnect()
        logger.info(f"{settings.Icons.END} OPCUAManager fermato.")
    
    async def _data_poller(self):
        logger.info("Data Poller avviato.")
        while self._running:
            try:
                # Copia dei sottoscrittori per evitare errori di runtime
                current_subs = list(self.subscribers.items())
                
                for node_id_string, callbacks in current_subs:
                    if not callbacks:
                        continue
                        
                    # 1. Recuperiamo il valore VECCHIO dalla cache
                    old_value = self.cache.get(node_id_string)
                    
                    # 2. Leggiamo il valore NUOVO direttamente dal client
                    # Usiamo il metodo del client per evitare di aggiornare la cache del manager prematuramente
                    node_obj = self.resolved_nodes.get(node_id_string)
                    if node_obj:
                        async with self.lock:
                            new_value = await self.client.read(node_obj)
                        
                        # 3. CONFRONTO
                        # Rimuoviamo 'old_value is not None' per gestire il primo cambio da None a valore
                        if new_value != old_value:
                            # NOTA: Qui usiamo DEBUG per non spammare il terminale principale
                            # L'aggiornamento verrà inviato via WS agli agenti che lo stamperanno
                            logger.debug(f"Cambio: {node_id_string} | {old_value} -> {new_value}")
							
                            
                            # Aggiorniamo la cache DOPO il confronto
                            self.cache[node_id_string] = new_value
                            
                            # Notifichiamo i client
                            await self._notify_subscribers(node_id_string, new_value)
                        else:
                            # Se non è cambiato, aggiorniamo comunque la cache per sicurezza
                            self.cache[node_id_string] = new_value
                
                await asyncio.sleep(0.1) # 100ms per alta reattività
                
            except Exception as e:
                logger.error(f"Errore nel Data Poller: {e}")
                await asyncio.sleep(1)
        
    async def _notify_subscribers(self, node_id_string: str, value: t.Any):
        # ... (logica invariata) ...
        for cb in list(self.subscribers.get(node_id_string, [])):
            try:
                if asyncio.iscoroutinefunction(cb):
                    asyncio.create_task(cb(node_id_string, value))
                else:
                    cb(node_id_string, value)
            except Exception:
                pass
                # logger.exception("Subscriber callback failed for node %s", node_id_string)


    # Metodi pubblici read/write/subscribe (logica invariata ma con lock)

    async def read(self, node_id_string: str):
        """Legge un valore usando la stringa ID come lookup key."""
        node_obj = self.resolved_nodes.get(node_id_string)
        if not node_obj:
            return self.cache.get(node_id_string)
            
        async with self.lock:
            #try:
                # Chiama il metodo read del tuo OPCUAClient usando l'OGGETTO Node
                val = await self.client.read(node_obj) 
                self.cache[node_id_string] = val
                return val
            # except Exception as e:
            #     logger.error("Read failed for %s: %s", node_id_string, e)
            #     return self.cache.get(node_id_string)

    async def write(self, node_id_string: str, value: t.Any):
        """Scrive un valore usando la stringa ID come lookup key."""
        node_obj = self.resolved_nodes.get(node_id_string)
        if not node_obj:
            # Fallback: prova a recuperarlo al volo se non e' in cache
            try:
                node_obj = self.client.get_node(node_id_string)
            except Exception:
                logger.error(f"Write failed: NodeID nullo o non risolvibile: {node_id_string}")
                return False
            
        async with self.lock:
            
            try:
                # TYPE CASTING: usa il tipo OPC UA reale letto dal PLC all'avvio.
                # Fallback basato su tipo Python se il nodo non era leggibile.
                cached_type = self.node_variant_types.get(node_id_string)

                if cached_type is not None:
                    # Convertiamo il valore Python al tipo atteso dal PLC
                    if cached_type in (ua.VariantType.Float,):
                        ua_variant = ua.Variant(float(value), cached_type)
                    elif cached_type in (ua.VariantType.Double,):
                        ua_variant = ua.Variant(float(value), cached_type)
                    elif cached_type in (ua.VariantType.Int16, ua.VariantType.Int32,
                                         ua.VariantType.Int64, ua.VariantType.UInt16,
                                         ua.VariantType.UInt32, ua.VariantType.UInt64):
                        ua_variant = ua.Variant(int(value), cached_type)
                    elif cached_type == ua.VariantType.Boolean:
                        ua_variant = ua.Variant(bool(value), cached_type)
                    else:
                        ua_variant = ua.Variant(value, cached_type)
                elif isinstance(value, bool):
                    ua_variant = ua.Variant(value, ua.VariantType.Boolean)
                elif isinstance(value, float):
                    ua_variant = ua.Variant(value, ua.VariantType.Float)
                elif isinstance(value, int):
                    ua_variant = ua.Variant(value, ua.VariantType.Int32)
                else:
                    ua_variant = ua.Variant(value)

                # 3. Scrittura con Variant esplicito
                # Usiamo write_value specificando il DataValue che contiene il Variant tipizzato
                data_value = ua.DataValue(ua_variant)
                await self.client.write(node_obj, data_value)
                
                # 4. Aggiorna Cache e Notifica
                self.cache[node_id_string] = value
                await self._notify_subscribers(node_id_string, value)
                return True
                
            except Exception as e:
                # Se fallisce ancora, logghiamo l'errore specifico (es. BadTypeMismatch)
                logger.error(f"Errore Scrittura OPC UA su {node_id_string}: {e}")
                return False

    def subscribe(self, node_id_string: str, callback: Callback):
        # ... (logica invariata) ...
        self.subscribers.setdefault(node_id_string, set()).add(callback)

    def unsubscribe(self, node_id_string: str, callback: Callback):
        # ... (logica invariata) ...
        if node_id_string in self.subscribers:
            self.subscribers[node_id_string].discard(callback)

    async def _monitor_connection(self):
        """Monitoraggio semplice."""
        while self._running:
            # Implementare qui logica di check se serve
            await asyncio.sleep(5)