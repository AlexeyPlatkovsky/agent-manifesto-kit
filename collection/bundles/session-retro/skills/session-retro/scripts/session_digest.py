"""Summarize a Claude Code or Codex session log into a compact digest for a retro.

  python3 session_digest.py --latest [--provider claude|codex] [--cwd DIR] [--json] [--out FILE]
  python3 session_digest.py --transcript PATH [--provider claude|codex] [--json] [--out FILE]

The digest keeps what a retro needs and drops the rest: requests and how long each took,
failed commands grouped by signature, commands and inline scripts repeated across the session
(candidates for a reusable script), files edited many times, likely user corrections, skills
and agents used, models, tokens and duration. Raw logs run to tens of megabytes; the digest stays
a few kilobytes. Standard library only.

Log locations (override the roots with CLAUDE_CONFIG_DIR and CODEX_HOME):
  Claude Code: ~/.claude/projects/<cwd with non-alphanumerics as '-'>/<session-id>.jsonl
  Codex:       ~/.codex/sessions/YYYY/MM/DD/rollout-<time>-<session-id>.jsonl
"""
import argparse
import glob
import json
import os
import re
import shlex
import sys
from collections import Counter

LIMITS = {"requests": 40, "failures": 40, "inline": 30, "text": 400, "error": 300}
# Phrases that correct the agent, not ordinary sentences that happen to start with "no" or "not".
CORRECTION = re.compile(
    r"^\s*(no[,.!]|nope\b|wrong\b|that'?s (not|wrong)\b|not what i\b|don'?t do\b|stop (doing|that)\b|"
    r"revert\b|undo\b|why did you\b|i (said|told you|asked)\b|"
    r"нет[,.!]|не так\b|неправильно|я же (сказал|просил)|зачем ты\b|верни\b)", re.I)
SETUP_WORDS = {"cd", "export", "set", "mkdir", "echo", "source", "true", "clear", "sleep", "pwd"}
RUNNERS = {"python", "python3", "node", "bash", "sh", "zsh", "npx", "uv", "deno", "ruby", "tsx", "ts-node"}
SCRIPT_EXT = (".py", ".js", ".mjs", ".ts", ".sh", ".gd", ".rb")
HEREDOC = re.compile(r"<<-?\s*['\"]?(\w+)['\"]?[^\n]*\n(.*?)\n\s*\1\b", re.S)


# ── command classification ──────────────────────────────────────────────────

def _segments(cmd):
    body = HEREDOC.sub(" ", cmd)
    return [s.strip() for s in re.split(r"&&|\|\||;|\n|\|", body) if s.strip()]


def signature(cmd):
    """A short stable label for a shell command: program plus script or subcommand."""
    for seg in _segments(cmd):
        try:
            tokens = shlex.split(seg)
        except ValueError:
            tokens = seg.split()
        while tokens and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tokens[0]):
            tokens = tokens[1:]
        if not tokens or tokens[0] in SETUP_WORDS:
            continue
        prog = os.path.basename(tokens[0])
        rest = tokens[1:]
        if "--python" in rest:
            i = rest.index("--python")
            if i + 1 < len(rest):
                return f"{prog} --python {os.path.basename(rest[i + 1])}"
        if prog in RUNNERS or prog.lower().startswith("python"):
            for t in rest:
                if t in ("-", "-c", "-e"):
                    return f"{prog} {t} (inline)"
                if t.endswith(SCRIPT_EXT):
                    return f"{prog} {os.path.basename(t)}"
                if not t.startswith("-"):
                    return f"{prog} {t}"
            return prog
        sub = next((t for t in rest if not t.startswith("-") and "/" not in t and len(t) < 30), "")
        return f"{prog} {sub}".strip()
    return "(setup command)"


INLINE = re.compile(r"\b(python\d?(?:\.\d+)?|node|ruby|bash|sh)\s+(-\s*<<|-c\s|-e\s|-\s*$|<<)|\bcat\s*>\s*\S+\.(py|js|ts|sh|gd)\s*<<", re.M)
WRITES = re.compile(r"open\(\s*(?:['\"]([^'\"]+)['\"]|(\w+))\s*,\s*['\"][wa]")
ASSIGN = re.compile(r"\b(\w+)\s*=\s*['\"]([^'\"\s]+\.\w{1,5})['\"]")
SED = re.compile(r"\bsed\s+-i(?:\s+''|\s+\"\")?\s+.*?\s(\S+\.\w{1,5})\s*(?:$|&&|;|\|)", re.M)


def inline_script(cmd):
    """Label of an inline script (heredoc or -c/-e body), or None."""
    m = INLINE.search(cmd)
    if not m:
        return None
    here = HEREDOC.search(cmd, m.start())
    body = here.group(2) if here else cmd[m.end():].strip().strip("'\"")
    for line in body.splitlines():
        line = line.strip()
        if line and not re.match(r"^(import |from |#|\"\"\"|\'\'\'|const |require\()", line):
            return line[:60]
    first = body.strip().splitlines()
    return first[0][:60] if first else "(empty)"


def written_files(cmd):
    """Files a command edits in place: open(..., 'w') in inline scripts, or sed -i."""
    names = dict(ASSIGN.findall(cmd))
    out = []
    for literal, var in WRITES.findall(cmd):
        path = literal or names.get(var)
        if path:
            out.append(path)
    out += SED.findall(cmd)
    return out


def command_signals(cmd):
    """Metadata needed across a hook boundary, without the command or inline-script body."""
    return {"signature": signature(cmd), "inline": bool(inline_script(cmd)),
            "edits": written_files(cmd), "skills": re.findall(r"([\w.-]+)/SKILL\.md", cmd)}


def _clip(text, n):
    text = " ".join(str(text).split())
    return text if len(text) <= n else text[: n - 1] + "…"


# ── digest ──────────────────────────────────────────────────────────────────

class Digest:
    def __init__(self, provider):
        self.provider = provider
        self.session_id = None
        self.cwd = None
        self.start = None
        self.end = None
        self.models = Counter()
        self.output_tokens = 0
        self.tools = Counter()
        self.cmd_sig = Counter()
        self.cmd_fail = Counter()
        self.tool_fail = Counter()
        self.failures = []
        self.inline = []
        self.inline_count = 0
        self.edits = Counter()
        self.requests = []
        self.request_count = 0
        self.corrections = 0
        self.seen_messages = []
        self.skills = Counter()
        self.agents = Counter()
        self.pending = {}

    # state round trip for the incremental hook
    def to_state(self):
        return {k: (dict(v) if isinstance(v, Counter) else v) for k, v in self.__dict__.items()}

    def slim_state(self):
        """Counters only, for the hook's cache: no request text, excerpts or labels."""
        keep = {"provider", "session_id", "tools", "cmd_fail", "tool_fail", "inline_count", "edits",
                "request_count", "corrections", "seen_messages"}
        state = {k: v for k, v in self.to_state().items() if k in keep}
        state["pending"] = {
            k: [v[0], command_signals(v[1]) if isinstance(v[1], str) else v[1], None]
            if v[0] == "Bash" else [v[0], "", None] for k, v in self.pending.items()
        }
        return state

    @classmethod
    def from_state(cls, state):
        d = cls(state["provider"])
        for k, v in state.items():
            setattr(d, k, Counter(v) if isinstance(getattr(d, k, None), Counter) else v)
        return d

    def _time(self, ts):
        if ts:
            self.start = self.start or ts
            self.end = ts

    def _command(self, cmd, ok, error, ts):
        metadata = cmd if isinstance(cmd, dict) else command_signals(cmd)
        sig = metadata["signature"]
        self.cmd_sig[sig] += 1
        if metadata["inline"]:
            self.inline_count += 1
            if isinstance(cmd, str) and len(self.inline) < LIMITS["inline"]:
                self.inline.append({"label": inline_script(cmd), "time": ts})
        for m in metadata["skills"]:
            self.skills[m] += 1
        for path in metadata["edits"]:
            self.edits[path] += 1
        if not ok:
            self.cmd_fail[sig] += 1
            self._failure(sig, sig if isinstance(cmd, dict) else cmd, error, ts)

    def _failure(self, sig, what, error, ts):
        if len(self.failures) < LIMITS["failures"]:
            self.failures.append({"signature": sig, "command": _clip(what, 200),
                                  "error": _clip(error or "", LIMITS["error"]), "time": ts})

    def _request(self, text, ts):
        text = text.strip()
        if not text or text.startswith("<") or text.startswith("[Request interrupted"):
            return
        if self.request_count and CORRECTION.search(text):
            self.corrections += 1
        self.request_count += 1
        if len(self.requests) < LIMITS["requests"]:
            self.requests.append({"time": ts, "text": _clip(text, LIMITS["text"])})

    # Claude Code: {"type": "user"|"assistant", "message": {...}, "timestamp": ...}
    def feed_claude(self, o):
        ts = o.get("timestamp")
        self._time(ts)
        self.session_id = self.session_id or o.get("sessionId")
        self.cwd = self.cwd or o.get("cwd")
        m = o.get("message") or {}
        content = m.get("content")
        if o.get("type") == "assistant":
            # one log line per content block repeats the message's model and usage: count each message once
            mid = m.get("id")
            if not mid or mid not in self.seen_messages:
                if mid:
                    self.seen_messages = (self.seen_messages + [mid])[-50:]
                if m.get("model"):
                    self.models[m["model"]] += 1
                self.output_tokens += (m.get("usage") or {}).get("output_tokens", 0) or 0
            for b in content if isinstance(content, list) else []:
                if b.get("type") != "tool_use":
                    continue
                name, inp = b.get("name", "?"), b.get("input") or {}
                self.tools[name] += 1
                if name == "Skill" and inp.get("skill"):
                    self.skills[inp["skill"]] += 1
                if name in ("Agent", "Task"):
                    self.agents[inp.get("subagent_type") or "general-purpose"] += 1
                path = inp.get("file_path") or inp.get("notebook_path")
                if name in ("Edit", "Write", "MultiEdit", "NotebookEdit") and path:
                    self.edits[path] += 1
                if name == "Read" and str(path or "").endswith("SKILL.md"):
                    self.skills[os.path.basename(os.path.dirname(path))] += 1
                what = inp.get("command") if name == "Bash" else (path or inp.get("description") or name)
                self.pending[b.get("id")] = [name, what or name, ts]
        elif o.get("type") == "user" and not o.get("isMeta"):
            if isinstance(content, str):
                self._request(content, ts)
                return
            for b in content if isinstance(content, list) else []:
                if b.get("type") == "text":
                    self._request(b.get("text", ""), ts)
                elif b.get("type") == "tool_result":
                    name, what, t0 = self.pending.pop(b.get("tool_use_id"), ["?", "?", ts])
                    err = b.get("is_error") is True
                    out = b.get("content")
                    text = out if isinstance(out, str) else " ".join(x.get("text", "") for x in out or [] if isinstance(x, dict))
                    if name == "Bash":
                        self._command(what, not err, text, t0)
                    elif err:
                        self.tool_fail[name] += 1
                        self._failure(name, what, text, t0)

    # Codex: {"type": "session_meta"|"event_msg"|"response_item"|..., "payload": {...}}
    def feed_codex(self, o):
        ts = o.get("timestamp")
        self._time(ts)
        p = o.get("payload") or {}
        t = o.get("type")
        if t == "session_meta":
            self.session_id = self.session_id or p.get("session_id") or p.get("id")
            self.cwd = self.cwd or p.get("cwd")
        elif t == "event_msg" and p.get("type") == "thread_settings_applied":
            model = (p.get("thread_settings") or {}).get("model")
            if model:
                self.models[model] += 1
        elif t == "event_msg" and p.get("type") == "token_count":
            usage = ((p.get("info") or {}).get("total_token_usage") or {})
            self.output_tokens = max(self.output_tokens, usage.get("output_tokens", 0) or 0)
        elif t == "event_msg" and p.get("type") == "item_completed":
            it = p.get("item") or {}
            kind = it.get("type")
            if kind == "UserMessage":
                for c in it.get("content") or []:
                    if c.get("type") == "text":
                        self._request(c.get("text", ""), ts)
                return
            if kind in (None, "Reasoning", "AgentMessage", "ContextCompaction"):
                return
            self.tools[kind] += 1
            if kind == "CommandExecution":
                cmd = it.get("command")
                cmd = cmd[-1] if isinstance(cmd, list) and cmd else str(cmd or "")
                ok = it.get("status") != "failed" and it.get("exit_code") in (0, None)
                self._command(cmd, ok, it.get("stderr") or it.get("stdout") or "", ts)
            elif kind == "FileChange":
                for path in (it.get("changes") or {}):
                    self.edits[path] += 1
        elif t == "response_item" and p.get("type") == "function_call" and p.get("name") == "spawn_agent":
            try:
                self.agents[json.loads(p.get("arguments") or "{}").get("agent_type") or "default"] += 1
            except ValueError:
                self.agents["default"] += 1

    def feed(self, o):
        (self.feed_claude if self.provider == "claude" else self.feed_codex)(o)

    # signals the hook thresholds and the analyst both use
    def signals(self):
        repeated_fail = self.cmd_fail.most_common(1)
        churn = self.edits.most_common(1)
        return {
            "tool_calls": sum(self.tools.values()),
            "failed": sum(self.cmd_fail.values()) + sum(self.tool_fail.values()),
            "repeat_fail": repeated_fail[0] if repeated_fail else ["", 0],
            "inline_scripts": self.inline_count,
            "churn": churn[0] if churn else ["", 0],
            "corrections": self.corrections,
        }

    def to_json(self):
        s = self.to_state()
        s.pop("pending", None)
        s.pop("seen_messages", None)
        for key, value in self.__dict__.items():
            if isinstance(value, Counter):
                s[key] = dict(value.most_common(40))
        s["signals"] = self.signals()
        s["repeated_commands"] = [[k, v] for k, v in self.cmd_sig.most_common(15) if v >= 3]
        return s

    def markdown(self):
        s = self.signals()
        out = [f"# Session digest ({self.provider})", "",
               f"- session: `{self.session_id}`  cwd: `{self.cwd}`",
               f"- time: {self.start} → {self.end}",
               f"- models: {', '.join(f'{k} ×{v}' for k, v in self.models.most_common()) or 'unknown'}"
               f"; output tokens: {self.output_tokens}",
               f"- tool calls: {s['tool_calls']} ({', '.join(f'{k} {v}' for k, v in self.tools.most_common(8))})",
               f"- signals: failed {s['failed']}, inline scripts {s['inline_scripts']}, "
               f"top repeated failure `{s['repeat_fail'][0]}` ×{s['repeat_fail'][1]}, "
               f"most edited `{s['churn'][0]}` ×{s['churn'][1]}, likely corrections {s['corrections']}", ""]
        out += ["## Requests", ""] + [f"- {r['time']}: {r['text']}" for r in self.requests] + [""]
        if self.failures:
            out += ["## Failures (by signature)", ""]
            groups = {}
            for f in self.failures:
                groups.setdefault(f["signature"], []).append(f)
            total = Counter(self.cmd_fail) + Counter(self.tool_fail)
            for sig, items in sorted(groups.items(), key=lambda kv: -total.get(kv[0], len(kv[1]))):
                out.append(f"- `{sig}` ×{total.get(sig, len(items))}")
                for f in items[:2]:
                    out.append(f"  - {f['time']}: `{f['command']}` → {f['error']}")
            out.append("")
        rep = [(k, v) for k, v in self.cmd_sig.most_common(15) if v >= 3]
        if rep:
            out += ["## Repeated commands", ""] + [f"- `{k}` ×{v}" for k, v in rep] + [""]
        if self.inline:
            out += [f"## Inline scripts ({self.inline_count})", ""] + [f"- {i['time']}: {i['label']}" for i in self.inline] + [""]
        churn = [(k, v) for k, v in self.edits.most_common(10) if v >= 3]
        if churn:
            out += ["## Files edited 3+ times", ""] + [f"- `{k}` ×{v}" for k, v in churn] + [""]
        if self.skills or self.agents:
            out += ["## Skills and agents used", ""]
            out += [f"- skill `{k}` ×{v}" for k, v in self.skills.most_common(40)]
            out += [f"- agent `{k}` ×{v}" for k, v in self.agents.most_common(40)] + [""]
        return "\n".join(out)


# ── reading and locating logs ───────────────────────────────────────────────

def detect_provider(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                o = json.loads(line)
            except ValueError:
                continue
            return "codex" if "payload" in o else "claude"
    return "claude"


def read_from(path, digest, offset=0):
    """Feed complete lines after offset; return the new offset (a trailing partial line is left)."""
    size = os.path.getsize(path)
    if offset > size:
        offset = 0
    with open(path, "rb") as f:
        f.seek(offset)
        for raw in f:
            if not raw.endswith(b"\n"):
                break
            offset += len(raw)
            try:
                digest.feed(json.loads(raw))
            except (ValueError, AttributeError, TypeError):
                continue
    return offset


def claude_root():
    return os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude")


def codex_root():
    return os.environ.get("CODEX_HOME") or os.path.expanduser("~/.codex")


def locate(provider, cwd=None, session_id=None):
    """Newest log for a session id, or for a project directory."""
    if provider == "claude":
        if session_id:
            hits = glob.glob(os.path.join(claude_root(), "projects", "*", f"{session_id}.jsonl"))
        else:
            folder = re.sub(r"[^A-Za-z0-9]", "-", os.path.abspath(cwd or os.getcwd()))
            hits = glob.glob(os.path.join(claude_root(), "projects", folder, "*.jsonl"))
        return max(hits, key=os.path.getmtime) if hits else None
    pattern = f"*{session_id}.jsonl" if session_id else "rollout-*.jsonl"
    hits = sorted(glob.glob(os.path.join(codex_root(), "sessions", "**", pattern), recursive=True),
                  key=os.path.getmtime, reverse=True)
    if session_id:
        return hits[0] if hits else None
    want = os.path.abspath(cwd or os.getcwd())
    for path in hits[:300]:
        try:
            with open(path, encoding="utf-8") as f:
                meta = json.loads(f.readline()).get("payload") or {}
        except (ValueError, OSError):
            continue
        if os.path.abspath(meta.get("cwd") or "") == want:
            return path
    return None


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--transcript")
    p.add_argument("--latest", action="store_true", help="newest session for --cwd (default: current directory)")
    p.add_argument("--session-id")
    p.add_argument("--provider", choices=["claude", "codex"])
    p.add_argument("--cwd")
    p.add_argument("--json", action="store_true")
    p.add_argument("--out")
    args = p.parse_args()
    path = args.transcript
    if not path:
        if not (args.latest or args.session_id):
            p.error("pass --transcript, --latest or --session-id")
        providers = [args.provider] if args.provider else ["claude", "codex"]
        found = [x for x in (locate(pr, args.cwd, args.session_id) for pr in providers) if x]
        if not found:
            raise SystemExit("no session log found; pass --transcript")
        path = max(found, key=os.path.getmtime)
    digest = Digest(args.provider or detect_provider(path))
    read_from(path, digest)
    text = json.dumps(digest.to_json(), indent=2) if args.json else digest.markdown()
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print(f"digest of {path} -> {args.out}")
    else:
        print(text)


if __name__ == "__main__":
    sys.exit(main())
