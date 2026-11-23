"""Compile a JSON IR request to a fully bound C1 research artifact."""
import argparse
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
import c1_compiler as compiler


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate request field: " + key)
        result[key] = value
    return result


def select_layout(request):
    limits = request["layout_limits"]
    fields = set(compiler.default_budget()) - {"a_rows", "a_cols"}
    if type(limits) is not dict or set(limits) != fields:
        raise ValueError("layout_limits must specify the six non-shape budget fields")
    shapes = sorted(((m, c) for m in (1, 2) for c in (1, 2)),
                    key=lambda shape: ((2 + shape[0]) * (3 + shape[1]), *shape))
    reasons = []
    for rows, columns in shapes:
        concrete = {**limits, "a_rows": rows, "a_cols": columns}
        try:
            artifact = compiler.compile_program(request["source"], concrete, request["fmt"],
                response_request=request.get("response_request"), mode=request.get("mode", "structural"))
        except compiler.CompileRefused as exc:
            reasons.append(f"{rows}x{columns}: {exc}")
            continue
        return artifact
    raise compiler.CompileRefused("All four layouts refused. " + " | ".join(reasons))


def compile_request(request):
    if type(request) is not dict or ("budget" in request) == ("layout_limits" in request):
        raise ValueError("Supply either a concrete budget or automatic layout_limits")
    budget_key = "budget" if "budget" in request else "layout_limits"
    required = {"source", budget_key, "fmt"}
    allowed = required | {"response_request", "mode"}
    if not required <= set(request) <= allowed:
        raise ValueError("Missing or unsupported compile request fields")
    artifact = compiler.compile_program(**request) if budget_key == "budget" else select_layout(request)
    compiler.check_artifact(artifact, request["source"], artifact["budget"], request["fmt"],
                            request.get("response_request"), request.get("mode", "structural"))
    return artifact


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        request = json.loads(args.request.read_text(), object_pairs_hook=unique_object)
        artifact = compile_request(request)
        serialized = json.dumps(artifact, indent=2, allow_nan=False) + "\n"
        with args.output.open("x") as output:
            output.write(serialized)
    except (OSError, ValueError, TypeError, RecursionError) as exc:
        parser.exit(1, f"Compilation refused: {exc}\n")
    print(f"{args.output}: {len(artifact['graph']['D_calls'])} D sites, "
          f"{artifact['capacity']['structural_update_dimension']} editable cells")


if __name__ == "__main__":
    main()
