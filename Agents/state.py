"""
Agents.state — thin compatibility wrapper.

The real evaluation orchestration lives in services.llm.evaluation_graph.
This module exists only because services/evaluation_service.py invokes
``python3 -m Agents.state`` as a subprocess.
"""
from __future__ import annotations

from services.llm.evaluation_graph import main


if __name__ == "__main__":
    main()