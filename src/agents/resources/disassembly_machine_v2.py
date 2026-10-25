import asyncio
import sys
import os
import logging

# --- PATH HACK ---
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from config import settings
from src.agents.base_agent import OPCUAMachineClient

# -----------------------------------------------------------
# CLASSI ASSI CON rangeI FISICI (RANGES)
# -----------------------------------------------------------
class AxisElectrical:
    def __init__(self, agent, prefix, ranges):
        self.agent = agent
        self.ranges = ranges  
        
        self.nodes = {
            "pos_attuale": f"mill_axis_{prefix}_pos_attuale",
            "pos_step": f"mill_axis_{prefix}_pos_step",
            "step_enable": f"mill_axis_{prefix}_step",
            "vel": f"mill_axis_{prefix}_vel",
            "acc": f"mill_axis_{prefix}_acc",
            "dec": f"mill_axis_{prefix}_dec"
        }

    async def set_params(self, vel, acc, dec):
        """Imposta velocità, accelerazione e decelerazione dell'asse. Valida i range prima di scrivere sul PLC (safety net agent-side)."""
        for nome, val, chiave in [("vel", vel, "vel"), ("acc", acc, "acc"), ("dec", dec, "dec")]:
            r = self.ranges[chiave]
            if not (r["min"] <= float(val) <= r["max"]):
                raise ValueError(f"range check agent-side: {nome}={val} fuori range [{r['min']}, {r['max']}]")
        await self.agent.write_and_verify(self.nodes["vel"], float(vel))
        await self.agent.write_and_verify(self.nodes["acc"], float(acc))
        await self.agent.write_and_verify(self.nodes["dec"], float(dec))

    async def move_to_position(self, target):
        """Muove l'asse alla posizione target. Valida il range prima di scrivere sul PLC (safety net agent-side)."""
        r = self.ranges["target"]
        if not (r["min"] <= float(target) <= r["max"]):
            raise ValueError(f"range check agent-side: target={target} fuori range [{r['min']}, {r['max']}] ({r.get('unit', '')})")
        await self.agent.write_and_verify(self.nodes["step_enable"], False)
        await self.agent.write_and_verify(self.nodes["pos_step"], float(target))
        await self.agent.write_and_verify(self.nodes["step_enable"], True)
        await self.agent.verify_target(self.nodes["pos_attuale"], float(target), tolerance=0.5)
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

# -----------------------------------------------------------
# 2. AGENTE CHE DEFINISCE LA STRUTTURA
# -----------------------------------------------------------
class DisassemblyMachineAgent(OPCUAMachineClient):
    def __init__(self, uri):
        super().__init__(uri, name="Disassembly_Machine")
        
        # DEFINIZIONE DEL GRAFO: Resource -> Components -> Ranges
        self.axes = {
            "x": AxisElectrical(self, "x", ranges={
                "target": {"min": 0, "max": 2000, "unit": "mm"},
                "vel": {"min": 1, "max": 100},
                "acc": {"min": 1, "max": 100},
                "dec": {"min": 1, "max": 100}
            }),
            "y": AxisElectrical(self, "y", ranges={
                "target": {"min": 0, "max": 540, "unit": "mm"},
                "vel": {"min": 1, "max": 100},
                "acc": {"min": 1, "max": 100},
                "dec": {"min": 1, "max": 100}
            }),
            "c": AxisElectrical(self, "360", ranges={
                "target": {"min": 0, "max": 720, "unit": "deg"},
                "vel": {"min": 1, "max": 100},
                "acc": {"min": 1, "max": 100},
                "dec": {"min": 1, "max": 100}
            }),
            "prs": AxisElectrical(self, "prs", ranges={
                "target": {"min": 0, "max": 1000, "unit": "mm"},
                "vel": {"min": 1, "max": 1000},
                "acc": {"min": 1, "max": 100},
                "dec": {"min": 1, "max": 100}
            }),
            "z": AxisElectrical(self, "z", ranges={
                "target": {"min": 0, "max": 270, "unit": "mm"},
                "vel": {"min": 1, "max": 100},
                "acc": {"min": 1, "max": 100},
                "dec": {"min": 1, "max": 100}
            }),
            "avvitatore": AxisAir(self, "avv") # Nessun range numerico, solo ON/OFF
        }

    async def _send_error(self, msg):
        """Logga l'errore e solleva eccezione. Il feedback ERROR viene inviato da execute_sequence()."""
        logging.error(f"{settings.Icons.ERR} {msg}")
        raise ValueError(msg)

    # --- METODO PER ESTRARRE I VINCOLI PER IL DB ---
    # Questo è l'unico metodo che serve per far funzionare la logica del BaseAgent
    def get_components_for_param(self, param_name):
        if param_name == "axis":
            # Per 'axis', valgono tutti gli assi elettrici e aria (se supportati)
            # O meglio: restituiamo self.axes e lasciamo che service_move filtri
            return self.axes
        elif param_name == "pneumatic_axis":
            # Per 'pneumatic_axis', restituiamo solo quelli di tipo AxisAir
            return {k: v for k, v in self.axes.items() if isinstance(v, AxisAir)}
        return {}
    
    # --- SERVIZI ESPOSTI (GENERICI E PULITI) ---

    async def service_move(self, axis, target):
        if axis in self.axes:
            # Controllo tipo: MOVE supporta solo AxisElectrical
            if isinstance(self.axes[axis], AxisElectrical):
                await self.axes[axis].move_to_position(target)
            else:
                await self._send_error(f"Asse '{axis}' non supporta MOVE (è pneumatico?)")
        else:
            await self._send_error(f"Asse '{axis}' non trovato.")

    async def service_set_params(self, axis, vel, acc, dec):
        if axis in self.axes and isinstance(self.axes[axis], AxisElectrical):
            await self.axes[axis].set_params(vel, acc, dec)
        else:
            await self._send_error(f"Asse '{axis}' invalido per SET_PARAMS")

    async def service_activate(self, pneumatic_axis):
        if pneumatic_axis in self.axes and isinstance(self.axes[pneumatic_axis], AxisAir):
            await self.axes[pneumatic_axis].activate()
        else:
            await self._send_error(f"Asse '{pneumatic_axis}' invalido per ACTIVATE")

    async def service_deactivate(self, pneumatic_axis):
        if pneumatic_axis in self.axes and isinstance(self.axes[pneumatic_axis], AxisAir):
            await self.axes[pneumatic_axis].deactivate()
        else:
            await self._send_error(f"Asse '{pneumatic_axis}' invalido per DEACTIVATE")

# --- ESECUZIONE ---
async def main():
    uri = settings.WS_URI
    agent = DisassemblyMachineAgent(uri)
    await agent.connect()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nArresto manuale (Ctrl+C).")