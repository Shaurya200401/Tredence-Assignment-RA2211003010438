from typing import Callable, Dict, Any

TOOLS: Dict[str, Callable[..., Any]] = {}


def register_tool(name: str):
    def wrapper(func: Callable):
        TOOLS[name] = func
        return func
    return wrapper


@register_tool("detect_smells")
def detect_smells(code: str):
    issues = 0
    if "TODO" in code or "FIXME" in code:
        issues += 1

    # If code is long, count as additional issue
    if len(code.splitlines()) > 200:
        issues += 2

    return {"issues": issues}


@register_tool("complexity_score")
def complexity_score(func_source: str):
    length = len(func_source)

    if length < 200:
        score = 90
    elif length < 500:
        score = 70
    else:
        score = 40

    return {"score": score}
