from fastapi import FastAPI, HTTPException, WebSocket
from app.models import GraphSpec, RunCreate, RunStatus
from app.engine import engine
from app import workflows
from app import tools
from typing import Dict
import asyncio

app = FastAPI(title="Minimal Workflow Engine")


# ---------------------------
# Register a sample graph on startup
# ---------------------------
@app.on_event("startup")
async def startup_event():
    # Nodes come from the workflows module
    nodes = {
        "extract_functions": workflows.extract_functions,
        "check_complexity": workflows.check_complexity,
        "detect_issues": workflows.detect_issues,
        "suggest_improvements": workflows.suggest_improvements,
    }

    # Edges when a node does not return 'next'
    edges = {
        "extract_functions": "check_complexity",
        "check_complexity": "detect_issues",
        "detect_issues": "suggest_improvements",
        "suggest_improvements": "end",
    }

    # Create the graph
    sample_id = engine.create_graph("code_review_sample", nodes, edges)
    app.state.sample_graph_id = sample_id


# ---------------------------
# Create a new graph
# ---------------------------
@app.post("/graph/create")
def create_graph(spec: GraphSpec):
    nodes: Dict[str, any] = {}

    # Only allow selecting nodes that already exist in workflows.py
    for name in spec.nodes.keys():
        if hasattr(workflows, name):
            nodes[name] = getattr(workflows, name)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown node '{name}'")

    graph_id = engine.create_graph(spec.name, nodes, spec.edges)
    return {"graph_id": graph_id}


# ---------------------------
# Run a graph
# ---------------------------
@app.post("/graph/run")
async def run_graph(payload: RunCreate):
    graph_id = (
        app.state.sample_graph_id
        if payload.graph_id == "sample"
        else payload.graph_id
    )

    if graph_id not in engine.graphs:
        raise HTTPException(status_code=404, detail="Graph not found")

    run_id = engine.run_graph(graph_id, payload.state)
    return {"run_id": run_id}


# ---------------------------
# Get state of a run
# ---------------------------
@app.get("/graph/state/{run_id}")
def get_state(run_id: str):
    if run_id not in engine.runs:
        raise HTTPException(status_code=404, detail="Run not found")

    run = engine.get_run(run_id)

    return {
        "run_id": run.run_id,
        "graph_id": run.graph_id,
        "state": run.state,
        "logs": run.logs,
        "finished": run.finished,
    }


# ---------------------------
# WebSocket for Real-time Logs
# ---------------------------
@app.websocket("/ws/logs/{run_id}")
async def websocket_endpoint(websocket: WebSocket, run_id: str):
    await websocket.accept()

    if run_id not in engine.runs:
        print(f"[WS ERROR] Run ID '{run_id}' not found. Available runs: {list(engine.runs.keys())}")
        await websocket.close(code=1008, reason="Run invalid")
        return

    print(f"[WS SUCCESS] Client connected to run '{run_id}'")
    # Create a dedicated queue for this connection
    queue = asyncio.Queue()
    engine.listeners.setdefault(run_id, []).append(queue)

    try:
        # 1. Send all existing logs first
        # This ensures the client catches up on what happened before connecting
        current_logs = list(engine.get_run(run_id).logs)
        for log in current_logs:
            await websocket.send_text(log)

        # 2. Stream new logs as they arrive
        while True:
            # Wait for next log message
            message = await queue.get()
            await websocket.send_text(message)

    except Exception:
        # Handle disconnects cleanly
        pass
    finally:
        # Cleanup listener
        if run_id in engine.listeners:
            try:
                engine.listeners[run_id].remove(queue)
            except ValueError:
                pass
