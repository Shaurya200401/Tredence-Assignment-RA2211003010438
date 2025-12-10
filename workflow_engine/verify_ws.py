import asyncio
import json
import urllib.request
import sys

# Try to import websockets, if not present gracefully exit
try:
    import websockets
except ImportError:
    print("The 'websockets' library is not installed. Please install it (pip install websockets) to run this test.")
    print("Alternatively, use the provided HTML client.")
    sys.exit(0)

BASE_URL = "http://127.0.0.1:8000"
WS_URL = "ws://127.0.0.1:8000"

def create_and_run_graph():
    # 1. Create Graph
    graph_spec = {
        "name": "ws_test_graph",
        "nodes": {
            "extract_functions": {},
            "check_complexity": {},
            "detect_issues": {},
            "suggest_improvements": {}
        },
        "edges": {
            "extract_functions": "check_complexity",
            "check_complexity": "detect_issues",
            "detect_issues": "suggest_improvements",
            "suggest_improvements": "end"
        }
    }
    
    req = urllib.request.Request(
        f"{BASE_URL}/graph/create",
        data=json.dumps(graph_spec).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req) as resp:
        graph_id = json.loads(resp.read().decode())["graph_id"]
        
    print(f"Graph created: {graph_id}")

    # 2. Run Graph
    payload = {
        "graph_id": graph_id,
        "state": {"code": "def foo(): pass\n" * 10} # Some code to trigger steps
    }
    
    req = urllib.request.Request(
        f"{BASE_URL}/graph/run",
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req) as resp:
        run_id = json.loads(resp.read().decode())["run_id"]
        
    print(f"Run started: {run_id}")
    return run_id

async def listen_to_logs(run_id):
    uri = f"{WS_URL}/ws/logs/{run_id}"
    print(f"Connecting to {uri}...")
    
    async with websockets.connect(uri) as websocket:
        print("Connected! Waiting for logs...")
        while True:
            try:
                message = await websocket.recv()
                print(f"[WS Log] {message}")
                if "Reached end." in message:
                    print("Workflow finished (detected via log).")
                    break
            except websockets.exceptions.ConnectionClosed:
                print("Connection closed.")
                break

if __name__ == "__main__":
    run_id = create_and_run_graph()
    try:
        asyncio.run(listen_to_logs(run_id))
    except KeyboardInterrupt:
        pass
