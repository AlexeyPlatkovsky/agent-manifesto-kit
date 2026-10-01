#!/usr/bin/env python3
"""Record explicit own-call usage events and summarize known values plus coverage.

Never feed parent totals that already contain child calls into this log. Each
event owns a distinct call/work interval. Omitted metrics mean unknown, not zero.
Token categories must be disjoint: input_tokens excludes cache read/write tokens.
Advisory dollars are caller-supplied estimates with a source, never a hard cap.
No network calls, provider inference, pricing tables, or automatic collection.
"""

import argparse
import json
import math
import os
from pathlib import Path
import sys


COUNTERS = ("input_tokens", "output_tokens", "cache_read_tokens", "cache_write_tokens",
            "api_calls", "tool_calls", "render_count")
METRICS = COUNTERS + ("elapsed_seconds", "render_seconds")
RESULTS = ("pass", "fail", "not_tested")


def nonempty(value):
    if not value.strip():
        raise argparse.ArgumentTypeError("value must not be empty")
    return value


def natural(value):
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("expected a nonnegative integer")
    if number < 0 or str(number) != value:
        raise argparse.ArgumentTypeError("expected a nonnegative integer")
    return number


def finite(value):
    try:
        number = float(value)
    except ValueError:
        raise argparse.ArgumentTypeError("expected a finite nonnegative number")
    if not math.isfinite(number) or number < 0:
        raise argparse.ArgumentTypeError("expected a finite nonnegative number")
    return number


def validate(event):
    if (not isinstance(event, dict) or event.get("schema_version") != 1
            or event.get("scope") != "own_call"
            or not isinstance(event.get("event_id"), str) or not event["event_id"].strip()
            or not isinstance(event.get("phase"), str) or not event["phase"].strip()
            or event.get("acceptance") not in (*RESULTS, None)):
        raise ValueError("invalid usage event schema")
    for key in ("provider", "model", "effort", "parent_id"):
        value = event.get(key)
        if value is not None and (not isinstance(value, str) or not value.strip()):
            raise ValueError("invalid " + key)
    if event.get("parent_id") == event["event_id"]:
        raise ValueError("parent_id must differ from event_id")
    metrics = event.get("metrics")
    if not isinstance(metrics, dict) or set(metrics) != set(METRICS):
        raise ValueError("invalid usage metrics")
    for key, value in metrics.items():
        if value is not None and (type(value) not in (int, float) or not math.isfinite(value)
                                  or value < 0 or (key in COUNTERS and type(value) is not int)):
            raise ValueError("invalid metric: " + key)
    advisory = event.get("advisory_cost")
    if advisory is not None:
        if not isinstance(advisory, dict) or set(advisory) != {"dollars", "source"}:
            raise ValueError("invalid advisory cost")
        value = advisory["dollars"]
        if (type(value) not in (int, float) or not math.isfinite(value) or value < 0
                or not isinstance(advisory["source"], str) or not advisory["source"].strip()):
            raise ValueError("invalid advisory cost")


def read_events(path):
    if not path.exists():
        return [], False
    content = path.read_text(encoding="utf-8")
    events = {}
    for line_number, line in enumerate(content.splitlines(), 1):
        if not line.strip():
            raise ValueError("blank usage line: " + str(line_number))
        event = json.loads(line)
        validate(event)
        previous = events.get(event["event_id"])
        if previous is not None and previous != event:
            raise ValueError("conflicting duplicate event_id: " + event["event_id"])
        events[event["event_id"]] = event
    return list(events.values()), bool(content and not content.endswith("\n"))


def summarize(events):
    totals = {}
    for key in METRICS:
        values = [event["metrics"][key] for event in events if event["metrics"][key] is not None]
        known_sum = sum(values) if values else None
        if known_sum is not None and not math.isfinite(known_sum):
            raise ValueError("metric total is not finite: " + key)
        totals[key] = {"known_sum": known_sum, "known_events": len(values),
                       "unknown_events": len(events) - len(values),
                       "complete": bool(events) and len(values) == len(events)}
    advisory = [event["advisory_cost"] for event in events if event.get("advisory_cost") is not None]
    dollars = sum(item["dollars"] for item in advisory) if advisory else None
    if dollars is not None and not math.isfinite(dollars):
        raise ValueError("advisory dollar total is not finite")
    return {"event_count": len(events), "metrics": totals,
            "acceptance": {result: sum(e["acceptance"] == result for e in events) for result in RESULTS},
            "unknown_acceptance": sum(e["acceptance"] is None for e in events),
            "advisory_cost": {"known_dollars": dollars, "known_events": len(advisory),
                              "unknown_events": len(events) - len(advisory),
                              "sources": sorted(set(item["source"] for item in advisory))},
            "hard_money_cap_verified": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    record = commands.add_parser("record", help="append one explicit own-call event, idempotently by ID")
    record.add_argument("--event-id", required=True, type=nonempty)
    record.add_argument("--phase", required=True, type=nonempty)
    for key in ("provider", "model", "effort", "parent_id"):
        record.add_argument("--" + key.replace("_", "-"), type=nonempty)
    for key in METRICS:
        record.add_argument("--" + key.replace("_", "-"), type=natural if key in COUNTERS else finite)
    record.add_argument("--acceptance", choices=RESULTS)
    record.add_argument("--advisory-dollars", type=finite)
    record.add_argument("--advisory-source", type=nonempty)
    summary = commands.add_parser("summary", help="sum known own-call metrics and expose unknown coverage")
    for command in (record, summary):
        command.add_argument("--log", type=Path, required=True)
    args = parser.parse_args()
    try:
        events, needs_newline = read_events(args.log)
        if args.command == "summary":
            report = summarize(events)
            report["phases"] = {phase: summarize([e for e in events if e["phase"] == phase])
                                for phase in sorted(set(e["phase"] for e in events))}
            print(json.dumps(report, allow_nan=False))
            return 0
        if (args.advisory_dollars is None) != (args.advisory_source is None):
            raise ValueError("--advisory-dollars and --advisory-source must be supplied together")
        event = {"schema_version": 1, "scope": "own_call", "event_id": args.event_id,
                 "phase": args.phase, "provider": args.provider, "model": args.model,
                 "effort": args.effort, "parent_id": args.parent_id,
                 "metrics": {key: getattr(args, key) for key in METRICS}, "acceptance": args.acceptance,
                 "advisory_cost": None if args.advisory_dollars is None else
                 {"dollars": args.advisory_dollars, "source": args.advisory_source}}
        validate(event)
        previous = next((e for e in events if e["event_id"] == event["event_id"]), None)
        if previous is not None:
            if previous != event:
                raise ValueError("conflicting duplicate event_id: " + event["event_id"])
            print(json.dumps({"recorded": False, "event_id": event["event_id"]}))
            return 0
        args.log.parent.mkdir(parents=True, exist_ok=True)
        payload = (("\n" if needs_newline else "") + json.dumps(event, allow_nan=False) + "\n").encode("utf-8")
        with args.log.open("ab") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        print(json.dumps({"recorded": True, "event_id": event["event_id"]}))
        return 0
    except (OSError, ValueError, KeyError, TypeError, OverflowError) as error:
        print("record_run: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
