from typing import Dict, Any
from app.tools import TOOLS
import asyncio


# -------------------------
# Extract functions from code
# -------------------------
async def extract_functions(state: Dict[str, Any]) -> Dict[str, Any]:
    code = state.get("code", "")
    parts = code.split("def ")
    functions = []

    for p in parts[1:]:
        functions.append("def " + p.strip())

    state["functions"] = functions
    state.setdefault("log", []).append(f"Extracted {len(functions)} functions")

    await asyncio.sleep(0)
    return {}


# -------------------------
# Check complexity of extracted functions
# -------------------------
async def check_complexity(state: Dict[str, Any]) -> Dict[str, Any]:
    funcs = state.get("functions", [])
    scores = []

    for f in funcs:
        res = TOOLS["complexity_score"](f)
        scores.append(res["score"])

    avg = sum(scores) / len(scores) if scores else 100

    state["complexity_score"] = avg
    state.setdefault("log", []).append(f"Avg complexity score: {avg}")

    await asyncio.sleep(0)

    # Branch: if complexity too low → jump to suggestions
    if avg < state.get("complexity_threshold", 80):
        return {"next": "suggest_improvements"}

    return {}


# -------------------------
# Detect issues in full code
# -------------------------
async def detect_issues(state: Dict[str, Any]) -> Dict[str, Any]:
    code = state.get("code", "")
    res = TOOLS["detect_smells"](code)

    state["issues"] = res["issues"]
    state.setdefault("log", []).append(f"Detected {res['issues']} issues")

    await asyncio.sleep(0)
    return {}


# -------------------------
# Suggest improvements until quality threshold reached
# -------------------------
async def suggest_improvements(state: Dict[str, Any]) -> Dict[str, Any]:
    issues = state.get("issues", 0)
    suggestions = []

    if issues > 0:
        suggestions.append("Remove TODO/FIXME and split large functions.")
    if state.get("complexity_score", 100) < 80:
        suggestions.append("Refactor long functions into smaller ones.")

    state.setdefault("suggestions", []).extend(suggestions)

    # Improve quality score gradually
    state["quality_score"] = min(100, state.get("quality_score", 50) + 15)

    state.setdefault("log", []).append(
        f"Suggested {len(suggestions)} improvements → quality={state['quality_score']}"
    )

    await asyncio.sleep(0)

    # Loop: keep improving until threshold met
    if state["quality_score"] < state.get("quality_threshold", 85):
        return {"next": "check_complexity"}

    return {}
