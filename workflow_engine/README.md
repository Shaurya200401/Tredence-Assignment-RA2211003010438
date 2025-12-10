# Minimal Workflow Engine

A lightweight, async python workflow engine built with FastAPI. It supports defining nodes (py functions), connecting them into graphs, managing state, and executing workflows with branching and looping.

## Features

- **Graph Engine**: Define DAGs with nodes and edges.
- **State Management**: Shared dictionary state passed between nodes.
- **Branching**: Nodes can return `{"next": "node_name"}` to dynamically route.
- **Looping**: Nodes can return `{"loop": True}` to repeat execution.
- **Async Execution**: Nodes runs in background (asyncio).
- **Real-time Logs**: Stream execution logs via WebSockets.
- **Simple Tool Registry**: Register python functions as reusable tools.

## Setup & Run

### Prerequisites
- Python 3.8+
- `fastapi`, `uvicorn`, `requests` (optional for verify script)

### Installation
```bash
pip install fastapi uvicorn
```

### Running the Server
```bash
python -m uvicorn app.main:app --reload
```
The API will be available at `http://127.0.0.1:8000/docs#/`.

## API Usage

### Create a Graph
**POST** `/graph/create`
```json
{
  "name": "my_graph",
  "nodes": {
    "extract": {},
    "analyze": {}
  },
  "edges": {
    "extract": "analyze",
    "analyze": "end"
  }
}
```

### Run a Workflow
**POST** `/graph/run`
```json
{
  "graph_id": "<graph_id>",
  "state": { "input": "some data" }
}
```
Returns: `{"run_id": "<run_id>"}`

### Get Status
**GET** `/graph/state/{run_id}`
Returns:
```json
{
  "run_id": "...",
  "finished": true,
  "state": { ... },
  "logs": [ ... ]
}
```

## Real-time Logs (WebSocket)
Connect to `ws://127.0.0.1:8000/ws/logs/{run_id}` to receive real-time updates.

You can use the provided `test_ws.html` client to test this:
1. Start the server.
2. Start a workflow via API (or use the sample).
3. Open `test_ws.html` in your browser.
4. Enter the `run_id` and click Connect.

## Project Structure
- `app/engine.py`: Core graph execution logic.
- `app/main.py`: FastAPI routes and WebSocket handler.
- `app/workflows.py`: Sample workflow node implementations.
- `app/tools.py`: Helper functions (tools) used by nodes.
- `app/models.py`: Pydantic models for API validation.

## Design Decisions
- **Asyncio**: Used for concurrent handling of multiple workflow runs.
- **Memory Store**: Graphs and runs are stored in-memory for simplicity. can be swapped for DB.
- **Listeners**: Implemented a pub/sub pattern in `GraphEngine` to support WebSocket log streaming.
