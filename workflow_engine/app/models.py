from typing import Any, Dict, Optional
from pydantic import BaseModel


class NodeSpec(BaseModel):
    name: str


class GraphSpec(BaseModel):
    name: str
    nodes: Dict[str, Any]           # keys = node names
    edges: Optional[Dict[str, str]] = {}

    class Config:
        json_schema_extra = {
            "example": {
                "name": "code_review_v1",
                "nodes": {
                    "extract_functions": {},
                    "check_complexity": {}
                },
                "edges": {
                    "extract_functions": "check_complexity",
                    "check_complexity": "end"
                }
            }
        }


class RunCreate(BaseModel):
    graph_id: str
    state: Dict[str, Any] = {}

    class Config:
        json_schema_extra = {
            "example": {
                "graph_id": "sample",
                "state": {
                    "code": "def hello():\n    print('world')"
                }
            }
        }


class RunStatus(BaseModel):
    run_id: str
    graph_id: str
    state: Dict[str, Any]
    logs: list
    finished: bool
