"""Stop hook for Claude Code and Codex: suggest a retro when a session shows improvement signals.

Registered by install_hooks.py as:  python3 <this file> --provider claude|codex

Both tools send the same JSON on stdin (session_id, transcript_path, cwd, stop_hook_active) and
accept {"systemMessage": ...} as a non-blocking notice to the user. The hook:
- never blocks the agent and never runs a model; every failure, including bad flags, exits 0
- caches only counters (no prompt text) with owner-only permissions
- reads only the log lines added since its last call (state in the user cache directory)
- stays quiet until the session is significant (--min-tool-calls), then nudges at most once per
  session when a threshold is crossed

Thresholds are flags so a project can tune them in its hook command. Stop fires after every
agent turn, which is why the state and the once-per-session rule matter.
"""
import argparse
import contextlib
import io
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from session_digest import Digest, locate, read_from  # noqa: E402


def state_dir():
    base = os.environ.get("XDG_CACHE_HOME") or os.path.expanduser("~/.cache")
    return os.path.join(base, "agentkit-retro")


def prune(folder, days=14):
    """Drop state for sessions untouched for two weeks; one small file per session otherwise piles up."""
    cutoff = time.time() - days * 86400
    for name in os.listdir(folder):
        path = os.path.join(folder, name)
        if name.endswith(".json") and os.path.getmtime(path) < cutoff:
            os.remove(path)


def crossed(sig, args):
    reasons = []
    if sig["failed"] >= args.failed:
        reasons.append(f"{sig['failed']} failed commands or tool calls")
    if sig["repeat_fail"][1] >= args.repeat_fail:
        reasons.append(f"`{sig['repeat_fail'][0]}` failed {sig['repeat_fail'][1]} times")
    if sig["inline_scripts"] >= args.inline:
        reasons.append(f"{sig['inline_scripts']} ad-hoc inline scripts")
    if sig["churn"][1] >= args.churn:
        reasons.append(f"`{os.path.basename(sig['churn'][0])}` edited {sig['churn'][1]} times")
    if sig["corrections"] >= args.corrections:
        reasons.append(f"{sig['corrections']} likely corrections from you")
    return reasons


def run(args, payload):
    session = payload.get("session_id")
    if payload.get("stop_hook_active") or not session:
        return None
    os.makedirs(state_dir(), mode=0o700, exist_ok=True)
    prune(state_dir())
    state_file = os.path.join(state_dir(), f"{args.provider}-{session}.json")
    state = {}
    if os.path.exists(state_file):
        with open(state_file, encoding="utf-8") as f:
            state = json.load(f)
    if state.get("nudged"):
        return None
    path = payload.get("transcript_path") or state.get("transcript") or locate(args.provider, payload.get("cwd"), session)
    if not path or not os.path.exists(path):
        return None
    reset = state.get("transcript") != path or os.path.getsize(path) < state.get("offset", 0)
    digest = Digest.from_state(state["digest"]) if state.get("digest") and not reset else Digest(args.provider)
    offset = read_from(path, digest, 0 if reset else state.get("offset", 0))
    sig = digest.signals()
    reasons = crossed(sig, args) if sig["tool_calls"] >= args.min_tool_calls else []
    state = {"transcript": path, "offset": offset, "digest": digest.slim_state(), "nudged": bool(reasons),
             "updated": time.time()}
    tmp = state_file + ".tmp"
    with os.fdopen(os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600), "w", encoding="utf-8") as f:
        json.dump(state, f)
    os.replace(tmp, state_file)
    if not reasons:
        return None
    return ("Retro suggested for this session: " + "; ".join(reasons) +
            '. When the task is done, ask for a retro (session-retro skill) to turn this into scripts or skill fixes.')


def build_parser():
    p = argparse.ArgumentParser(prog="retro_hook.py", allow_abbrev=False)
    p.add_argument("--provider", choices=["claude", "codex"], required=True)
    p.add_argument("--min-tool-calls", type=int, default=40)
    p.add_argument("--failed", type=int, default=10)
    p.add_argument("--repeat-fail", type=int, default=4)
    p.add_argument("--inline", type=int, default=8)
    p.add_argument("--churn", type=int, default=8)
    p.add_argument("--corrections", type=int, default=2)
    return p


def main():
    # Exit 2 from a Stop hook means "block and continue" in both tools, so no path may exit non-zero:
    # bad flags, bad input and internal errors all end silently with 0.
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            args = build_parser().parse_args()
        message = run(args, json.load(sys.stdin))
    except BaseException:
        return 0
    if message:
        print(json.dumps({"systemMessage": message}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
