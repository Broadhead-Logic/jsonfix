"""jsonfix - Parse 'almost JSON' with trailing commas, comments, smart quotes."""

from __future__ import annotations

from .parser import can_parse, get_repairs, load_relaxed, loads_relaxed
from .repairs import Repair, RepairKind

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "Repair",
    "RepairKind",
    "loads_relaxed",
    "load_relaxed",
    "can_parse",
    "get_repairs",
]
