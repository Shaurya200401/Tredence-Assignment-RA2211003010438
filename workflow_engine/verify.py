import urllib.request
import urllib.error
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def post_json(url, data):
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode('utf-8'))

def get_json(url):
    with urllib.request.urlopen(url) as response:
        return json.loads(response.read().decode('utf-8'))

def test_workflow():
    print("1. Creating a fresh graph...")
    # Defining a graph that uses the same nodes as the sample
    graph_spec = {
        "name": "verification_graph",
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
    
    try:
        create_resp = post_json(f"{BASE_URL}/graph/create", graph_spec)
        graph_id = create_resp["graph_id"]
        print(f"   -> Created Graph ID: {graph_id}")
    except urllib.error.URLError as e:
        print(f"   -> Error: HTTP {e.code} {e.reason}")
        try:
            print(e.read().decode('utf-8'))
        except:
            pass
        return

    print("\n2. Running the graph...")
    payload = {
        "graph_id": graph_id,
        "state": {
            "code": "def hello():\n    print('world')\n\ndef complex_logic():\n    # TODO: implement this\n    pass"
        }
    }
    
    try:
        run_data = post_json(f"{BASE_URL}/graph/run", payload)
        run_id = run_data["run_id"]
        print(f"   -> Started Run ID: {run_id}")
    except urllib.error.URLError as e:
        print(f"   -> Error starting run: {e}")
        return

    print("\n3. Polling for completion...")
    while True:
        try:
            state_data = get_json(f"{BASE_URL}/graph/state/{run_id}")
            
            finished = state_data["finished"]
            logs = state_data.get("logs", [])
            
            print(f"   -> Status: {'Finished' if finished else 'Running'} | Logs: {len(logs)}")
            
            if finished:
                print("\n4. Workflow Finished!")
                print("Final State Keys:", state_data["state"].keys())
                print("Logs:")
                for log in logs:
                    print(f" - {log}")
                break
            
            time.sleep(1)
        except urllib.error.URLError as e:
             print(f"Error polling: {e}")
             break

if __name__ == "__main__":
    test_workflow()
