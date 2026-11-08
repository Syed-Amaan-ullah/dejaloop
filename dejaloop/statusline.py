"""Claude Code status line: shows DejaLoop health at the bottom of the terminal.

Claude Code pipes session JSON (incl. cost.total_cost_usd) on stdin and
displays whatever this prints. Runs locally, uses no model tokens.
"""
from __future__ import annotations

import glob
import json
import os
import sys

from .core import home_dir, read_totals


def render(stdin_text: str) -> str:
    try:
        data = json.loads(stdin_text or "{}")
    except Exception:
        data = {}
    cost = (data.get("cost") or {}).get("total_cost_usd", 0.0) or 0.0

    files = sorted(glob.glob(os.path.join(home_dir(), "sessions", "*.json")),
                   key=lambda p: os.path.getmtime(p) if os.path.exists(p) else 0)
    health, interventions, checks = "● healthy", 0, 0
    if files:
        try:
            with open(files[-1]) as f:
                st = json.load(f)
            interventions = len(st.get("interventions", []))
            checks = len(st.get("calls", []))
            if any(i.get("action") in ("deny", "halt", "replan") for i in st.get("interventions", [])):
                health = "⛔ intervened"
            elif interventions:
                health = "⚠ warned"
        except Exception:
            pass
    saved = read_totals().get("est_saved_usd", 0.0)
    saved_part = f" | saved ~${saved:.2f}" if saved > 0 else ""
    return (f"DejaLoop {health} | session ${cost:.2f} | "
            f"checks {checks} | interventions {interventions}{saved_part}")


def main():
    print(render(sys.stdin.read()))


if __name__ == "__main__":
    main()
