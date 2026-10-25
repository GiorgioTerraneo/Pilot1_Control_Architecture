import asyncio
from asyncua import Client

class OPCUAClient:
    """
    Wrapper attorno alla libreria asyncua per fornire un'interfaccia 
    semplificata e asincrona al Manager.
    """
    def __init__(self, url):
        self.url = url
        self.client = Client(url)
        self.sub = None

    async def connect(self):
        await self.client.connect()
        # Non stampiamo nulla qui, lasciamo gestire i log al Manager
        
    async def disconnect(self):
        if self.sub:
            await self.sub.delete()
        await self.client.disconnect()

    async def get_node_by_id(self, node_id_string):
        """Restituisce l'oggetto Node per una stringa ID/path UA."""
        return self.client.get_node(node_id_string)

    async def read(self, node):
        """Read the current value of a node. 'node' MUST be an asyncua.Node object."""
        return await node.read_value()

    async def write(self, node, value):
        """Write a value to a node. 'node' MUST be an asyncua.Node object."""
        await node.write_value(value)
        return True

    async def create_subscription(self, interval, handler):
        self.sub = await self.client.create_subscription(interval, handler)
        return self.sub