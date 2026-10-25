import asyncio
import sys
import os

# --- PATH HACK ---
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
# -----------------------------------

from config import settings
from src.agents.base_observer import BaseObserver, main


class DisassemblyObserver(BaseObserver):

    NAME = "DisassemblyObserver"

    NODES = [
        "mill_axis_prs_pos_attuale",
        "mill_carico",
    ]

    def __init__(self, uri: str):
        super().__init__(uri, self.NAME, self.NODES)

    def get_dashboard_config(self) -> dict:
        return {
            "window": 500,
            "charts": [
                {
                    "id": "prs_carico",
                    "title": "Carico vs PRS",
                    "type": "scatter",
                    "x_node": {"name": "mill_axis_prs_pos_attuale", "label": "PRS (mm)"},
                    "y_node": {"name": "mill_carico", "label": "Carico (kg)", "color": "#67e8f9"},
                },
            ]
        }


if __name__ == "__main__":
    observer = DisassemblyObserver(settings.WS_URI)
    try:
        asyncio.run(main(observer))
    except KeyboardInterrupt:
        print("\nArresto manuale (Ctrl+C).")
