import asyncio
import sys
import os
import logging

# --- PATH HACK: PRIMA DI IMPORTARE I MODULI DEL PROGETTO ---
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
# -----------------------------------------------------------


from config import settings
from src.agents.base_agent import OPCUAMachineClient

# --- CLASSI ASSI (Invariate nella logica, ma pulite) ---
class AxisElectrical:
    def __init__(self, agent, prefix):
        self.agent = agent
        # Usa nomi variabili coerenti con node_map.py
        self.nodes = {
            "pos_attuale": f"mill_axis_{prefix}_pos_attuale",
            "pos_step": f"mill_axis_{prefix}_pos_step",
            "step_enable": f"mill_axis_{prefix}_step",
            "vel": f"mill_axis_{prefix}_vel",
            "acc": f"mill_axis_{prefix}_acc",
            "dec": f"mill_axis_{prefix}_dec"
        }

    async def set_params(self, vel, acc, dec):
        await self.agent.write_and_verify(self.nodes["vel"], vel)
        await self.agent.write_and_verify(self.nodes["acc"], acc)
        await self.agent.write_and_verify(self.nodes["dec"], dec)

    async def move_to_position(self, target):
        await self.agent.write_and_verify(self.nodes["step_enable"], False)
        await self.agent.write_and_verify(self.nodes["pos_step"], target)
        await self.agent.write_and_verify(self.nodes["step_enable"], True)
        await self.agent.verify_target(self.nodes["pos_attuale"], target)
        await self.agent.write_and_verify(self.nodes["step_enable"], False)

class AxisAir:
    def __init__(self, agent, prefix):
        self.agent = agent
        self.nodes = {
            "pos0_attiva": f"mill_air_{prefix}_pos0_attiva",
            "pos0_step": f"mill_air_{prefix}_pos0_step",
            "pos1_attiva": f"mill_air_{prefix}_pos1_attiva",
            "pos1_step": f"mill_air_{prefix}_pos1_step",
        }

    # Logica ottimizzata: leggo prima, se serve scrivo
    async def activate(self):
        await self.agent.write_and_verify(self.nodes["pos0_step"], False)
        await self.agent.write_and_verify(self.nodes["pos1_step"], True)
        await self.agent.verify_target(self.nodes["pos1_attiva"], True)
        await self.agent.write_and_verify(self.nodes["pos1_step"], False)

    
    
    async def deactivate(self):
        await self.agent.write_and_verify(self.nodes["pos1_step"], False)
        await self.agent.write_and_verify(self.nodes["pos0_step"], True)
        await self.agent.verify_target(self.nodes["pos0_attiva"], True)
        await self.agent.write_and_verify(self.nodes["pos0_step"], False)

class DisassemblyMachineAgent(OPCUAMachineClient):
    def __init__(self, uri):
        super().__init__(uri, name="Disassembly_Machine")
        self.axes = {
            "x": AxisElectrical(self, "x"),
            "y": AxisElectrical(self, "y"),
            "c": AxisElectrical(self, "360"),
            "prs": AxisElectrical(self, "prs"),
            "z": AxisElectrical(self, "z"),
            "avvitatore": AxisAir(self, "avv")
        }

    # --- DEBUG: OVERRIDE TEMPORANEO ---
    async def write_and_verify(self, node_name, target_value):
        # logging.info(f"DEBUG DIRETTO: Scrivo su {node_name} -> {target_value}")
        # Chiamiamo la logica originale (o la copiamo qui se serve)
        await super().write_and_verify(node_name, target_value)

    # --- SERVIZI ESPOSTI (Cercati automaticamente dalla superclasse) ---

    async def service_move(self, axis, target):
        """Questo metodo verrà registrato come 'MOVE'"""
        if axis in self.axes:
            await self.axes[axis].move_to_position(target)
        else:
            msg = f"Asse '{axis}' non trovato. Disponibili: {list(self.axes.keys())}"
            logging.error(f"{settings.Icons.ERR} {msg}")
            # Invia feedback al System Agent per bloccare il piano
            await self._send_feedback("ERROR", msg)
            raise ValueError(msg)

    async def service_set_params(self, axis, vel, acc, dec):
        """Questo metodo verrà registrato come 'SET_PARAMS'"""
        if axis in self.axes:
            await self.axes[axis].set_params(vel, acc, dec)
        else:
            msg = f"Asse '{axis}' non trovato. Disponibili: {list(self.axes.keys())}"
            logging.error(f"{settings.Icons.ERR} {msg}")
            await self._send_feedback("ERROR", msg)
            raise ValueError(msg)

    async def service_activate(self, pneumatic_axis):
        if pneumatic_axis in self.axes:
            await self.axes[pneumatic_axis].activate()
        else:
            msg = f"Asse pneumatico '{pneumatic_axis}' non trovato."
            logging.error(f"{settings.Icons.ERR} {msg}")
            await self._send_feedback("ERROR", msg)
            raise ValueError(msg)

    async def service_deactivate(self, pneumatic_axis):
        if pneumatic_axis in self.axes:
            await self.axes[pneumatic_axis].deactivate()
        else:
            msg = f"Asse pneumatico '{pneumatic_axis}' non trovato."
            logging.error(f"{settings.Icons.ERR} {msg}")
            await self._send_feedback("ERROR", msg)
            raise ValueError(msg)

# --- ESECUZIONE ---
async def main():
    """Funzione principale di avvio."""
    # Recupera l'URI dal file di configurazione centralizzato
    uri = settings.WS_URI
    
    agent = DisassemblyMachineAgent(uri)
    
    # connect() del BaseAgent contiene già il loop infinito per mantenere vivo il processo
    await agent.connect()

if __name__ == "__main__":
    try:
        # Avvia il loop asincrono
        asyncio.run(main())
    except KeyboardInterrupt:
        # Gestisce Ctrl+C senza stampare errori brutti
        print("\nArresto manuale (Ctrl+C).")