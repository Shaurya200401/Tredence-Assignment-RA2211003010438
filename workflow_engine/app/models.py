from typing import Any, Dict, Optional
from pydantic import BaseModel


class NodeSpec(BaseModel):
    name: str


class GraphSpec(BaseModel):
    name: str
    nodes: Dict[str, Any]           # keys = node names
    edges: Optional[Dict[str, str]] = {}


class RunCreate(BaseModel):
    graph_id: str
    state: Dict[str, Any] = {}


class RunStatus(BaseModel):
    run_id: str
    graph_id: str
    state: Dict[str, Any]
    logs: list
    finished: bool
