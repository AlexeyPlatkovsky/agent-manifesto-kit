#!/usr/bin/env python3
"""Explicit, consumer-local Blender task state; Python standard library only.

All reference paths are relative to the state file's directory, never the CWD.
Evidence stores SHA-256 of its declared inputs and the acceptance references.
Only changed dependencies invalidate a check. Run --help for the small CLI.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile


PROFILES = {"quick": 1, "standard": 2, "production": 3}
RESULTS = ("pass", "fail", "not_tested")


def natural(value):
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("expected a nonnegative integer")
    if number < 0 or str(number) != value:
        raise argparse.ArgumentTypeError("expected a nonnegative integer")
    return number


def ref(base, value):
    if not value.strip():
        raise ValueError("reference paths must not be empty")
    path = Path(value)
    path = path if path.is_absolute() else base / path
    return os.path.relpath(path.resolve(), base)


def digest(base, value):
    path = base / value
    if not path.is_file():
        return None
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def write_state(path, state, create=False):
    payload = json.dumps(state, indent=2, allow_nan=False) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    if create:
        with path.open("x", encoding="utf-8") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        return
    name = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=".task-state-", delete=False) as stream:
            name = stream.name
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if name and os.path.exists(name):
            os.unlink(name)


def read_state(path):
    state = json.loads(path.read_text(encoding="utf-8"))
    if (not isinstance(state, dict) or state.get("schema_version") != 1
            or state.get("profile") not in PROFILES
            or not isinstance(state.get("evidence"), dict)
            or not isinstance(state.get("handoffs"), dict)
            or not all(isinstance(state.get(key), list)
                       for key in ("artifacts", "acceptance_refs", "required", "repairs"))
            or type(state.get("max_repairs")) is not int or state["max_repairs"] < 0):
        raise ValueError("invalid task state schema")
    return state


def nonempty(value):
    if not value.strip():
        raise argparse.ArgumentTypeError("value must not be empty")
    return value


def status(state, base):
    checks = {}
    for name in sorted(set(state["required"]) | set(state["evidence"])):
        record = state["evidence"].get(name)
        reasons = []
        if record is None:
            result = "not_tested"
            reasons.append("missing evidence")
        else:
            result = record["result"]
            for dependency in record["dependencies"]:
                actual = digest(base, dependency["path"])
                if actual is None:
                    reasons.append("missing: " + dependency["path"])
                elif actual != dependency["sha256"]:
                    reasons.append("changed: " + dependency["path"])
        checks[name] = {"result": result, "valid": not reasons, "reasons": reasons,
                        "required": name in state["required"]}
    missing_refs = [value for value in state["artifacts"] + state["acceptance_refs"]
                    if digest(base, value) is None]
    considered = state["required"]
    accepted = bool(considered) and not missing_refs and all(
        checks[name]["valid"] and checks[name]["result"] == "pass" for name in considered)
    failed = any(checks[name]["result"] == "fail" for name in considered)
    return {"profile": state["profile"], "acceptance": "pass" if accepted else
            ("fail" if failed else "not_tested"), "checks": checks,
            "missing_refs": missing_refs, "repairs_used": len(state["repairs"]),
            "max_repairs": state["max_repairs"],
            "repairs_remaining": max(0, state["max_repairs"] - len(state["repairs"])),
            "handoffs": state["handoffs"]}, accepted


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init", help="create state; refuses an existing file")
    init.add_argument("--profile", choices=PROFILES, default="standard")
    init.add_argument("--artifact", action="append", default=[])
    init.add_argument("--acceptance", action="append", default=[])
    init.add_argument("--require", action="append", type=nonempty, default=[])
    init.add_argument("--max-repairs", type=natural)
    evidence = commands.add_parser("evidence", help="record a check and its content dependencies")
    evidence.add_argument("--name", required=True, type=nonempty)
    evidence.add_argument("--result", required=True, choices=RESULTS)
    evidence.add_argument("--depends", action="append", default=[])
    evidence.add_argument("--report")
    evidence.add_argument("--note", default="")
    inspect = commands.add_parser("status", help="diagnostic JSON status")
    inspect.add_argument("--strict", action="store_true", help="exit 1 unless required checks pass; optional checks never block")
    repair = commands.add_parser("repair", help="consume one repair round before doing the work")
    repair.add_argument("--reason", required=True, type=nonempty)
    handoff = commands.add_parser("handoff", help="persist separate compact build/fix handoffs")
    handoff.add_argument("--phase", required=True, choices=("build", "fix"))
    handoff.add_argument("--summary", required=True, type=nonempty)
    handoff.add_argument("--next", action="append", type=nonempty, default=[])
    handoff.add_argument("--ref", action="append", default=[])
    for command in (init, evidence, inspect, repair, handoff):
        command.add_argument("--state", type=Path, required=True)
    args = parser.parse_args()
    path = args.state.resolve()
    base = path.parent
    try:
        if args.command == "init":
            state = {"schema_version": 1, "profile": args.profile,
                     "artifacts": list(dict.fromkeys(ref(base, p) for p in args.artifact)),
                     "acceptance_refs": list(dict.fromkeys(ref(base, p) for p in args.acceptance)),
                     "required": list(dict.fromkeys(args.require)), "evidence": {},
                     "max_repairs": args.max_repairs if args.max_repairs is not None
                     else PROFILES[args.profile], "repairs": [],
                     "handoffs": {"build": None, "fix": None}}
            write_state(path, state, create=True)
        else:
            state = read_state(path)
            if args.command == "status":
                report, accepted = status(state, base)
                print(json.dumps(report, allow_nan=False))
                return 1 if args.strict and not accepted else 0
            if args.command == "evidence":
                paths = [ref(base, p) for p in args.depends] + state["acceptance_refs"]
                if args.report:
                    paths.append(ref(base, args.report))
                paths = list(dict.fromkeys(paths))
                if args.result != "not_tested" and not paths:
                    raise ValueError("pass/fail evidence needs at least one --depends, --report, or acceptance reference")
                dependencies = [{"path": p, "sha256": digest(base, p)} for p in paths]
                if args.result != "not_tested" and any(d["sha256"] is None for d in dependencies):
                    raise ValueError("pass/fail evidence dependencies must be existing regular files")
                state["evidence"][args.name] = {"result": args.result, "dependencies": dependencies,
                                                "report": ref(base, args.report) if args.report else None,
                                                "note": args.note}
            elif args.command == "repair":
                if len(state["repairs"]) >= state["max_repairs"]:
                    raise ValueError("repair limit reached; stop and report the remaining failure")
                state["repairs"].append({"round": len(state["repairs"]) + 1, "reason": args.reason})
            elif args.command == "handoff":
                state["handoffs"][args.phase] = {"summary": args.summary, "next": args.next,
                                                "refs": [ref(base, p) for p in args.ref]}
            write_state(path, state)
        print(json.dumps(state, allow_nan=False))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        print("task_state: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
