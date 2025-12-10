import asyncio
import uuid
from typing import Callable, Dict, Any, Optional
from pydantic import BaseModel


class Graph:
    def __init__(self, graph_id: str, nodes: Dict[str, Callable], edges: Optional[Dict[str, str]] = None):
        self.graph_id = graph_id
        self.nodes = nodes
        self.edges = edges or {}


class RunRecord(BaseModel):
    run_id: str
    graph_id: str
    state: Dict[str, Any]
    logs: list
    finished: bool = False


class GraphEngine:
    def __init__(self):
        self.graphs: Dict[str, Graph] = {}
        self.runs: Dict[str, RunRecord] = {}
        self.listeners: Dict[str, list] = {}  # run_id -> list of asyncio.Queue

    def create_graph(self, name: str, nodes: Dict[str, Callable], edges: Optional[Dict[str, str]] = None) -> str:
        graph_id = str(uuid.uuid4())
        self.graphs[graph_id] = Graph(graph_id, nodes, edges)
        return graph_id

    def get_graph(self, graph_id: str) -> Graph:
        return self.graphs[graph_id]

    async def _execute_node(self, node_callable: Callable, state: Dict[str, Any]) -> Dict[str, Any]:
        # Supports async or sync functions
        if asyncio.iscoroutinefunction(node_callable):
            return await node_callable(state)
        else:
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, node_callable, state)

    def _emit_log(self, run_id: str, message: str):
        if run_id in self.runs:
            self.runs[run_id].logs.append(message)
        
        if run_id in self.listeners:
            for queue in self.listeners[run_id]:
                queue.put_nowait(message)

    async def _run_background(self, run_id: str):
        record = self.runs[run_id]
        graph = self.graphs[record.graph_id]

        # Default start node = "start" or first node in dict
        current = "start" if "start" in graph.nodes else next(iter(graph.nodes))

        while True:
            node_fn = graph.nodes.get(current)
            if node_fn is None:
                self._emit_log(run_id, f"Node '{current}' does not exist. Stopping.")
                break

            self._emit_log(run_id, f"Running: {current}")

            try:
                control = await self._execute_node(node_fn, record.state) or {}
            except Exception as e:
                self._emit_log(run_id, f"Error in '{current}': {e}")
                record.finished = True
                break

            # Looping
            if control.get("loop"):
                self._emit_log(run_id, f"Looping on: {current}")
                continue

            # Branching
            next_node = control.get("next")

            # Use fallback edges if next not provided
            if not next_node:
                next_node = graph.edges.get(current)

            if not next_node:
                self._emit_log(run_id, f"No next node after {current}. Finishing.")
                break

            if next_node == "end":
                self._emit_log(run_id, "Reached end.")
                record.finished = True # Ensure explicitly marked finished here too if breaking
                break

            current = next_node

        record.finished = True
        # Notify listeners that run is finished (optional, maybe send a special message?)
        # For now, just let the loop finish. Clients can check status.

    def run_graph(self, graph_id: str, initial_state: Dict[str, Any]) -> str:
        run_id = str(uuid.uuid4())

        record = RunRecord(
            run_id=run_id,
            graph_id=graph_id,
            state=initial_state,
            logs=[],
            finished=False,
        )
        self.runs[run_id] = record

        asyncio.create_task(self._run_background(run_id))
        return run_id

    def get_run(self, run_id: str) -> RunRecord:
        return self.runs[run_id]


# Global engine instance
engine = GraphEngine()
