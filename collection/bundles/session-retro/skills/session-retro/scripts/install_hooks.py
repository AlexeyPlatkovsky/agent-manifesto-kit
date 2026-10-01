"""Register (or remove) the retro Stop hook for Claude Code and Codex in one project.

  python3 install_hooks.py [--dest PROJECT] [--provider claude,codex] [--shared] [--remove] [--dry-run] [-- HOOK FLAGS]

Targets (project level):
  Claude Code: PROJECT/.claude/settings.local.json (personal, not committed); --shared writes the
               committed PROJECT/.claude/settings.json instead
  Codex:       PROJECT/.codex/hooks.json; the command resolves the script from the git root, so the
               file holds no machine-specific path. Each person still reviews it with /hooks.
Existing settings and other hooks are preserved; running it again replaces only the retro entry.
Anything after "--" is passed to the hook (for example: -- --min-tool-calls 60) and is validated
first. A provider whose synced script is missing is skipped. The registered command checks that the
script exists and always exits 0, because an exit code of 2 from a Stop hook would make the agent
continue instead of stopping. Remove the hook (--remove) before removing the bundle.
"""
import argparse
import json
import os
import shlex
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from retro_hook import build_parser  # noqa: E402

MARKER = "/skills/session-retro/scripts/retro_hook.py"
SCRIPT = {"claude": ".claude/skills/session-retro/scripts/retro_hook.py",
          "codex": ".agents/skills/session-retro/scripts/retro_hook.py"}


def config_path(provider, shared):
    if provider == "claude":
        return ".claude/settings.json" if shared else ".claude/settings.local.json"
    return ".codex/hooks.json"


def command(provider, extra):
    root = '"$CLAUDE_PROJECT_DIR"' if provider == "claude" else '"$(git rev-parse --show-toplevel 2>/dev/null || pwd)"'
    flags = " ".join(["--provider", provider] + [shlex.quote(x) for x in extra])
    return f'f={root}/{SCRIPT[provider]}; [ -f "$f" ] && python3 "$f" {flags}; exit 0'


def update(config, cmd):
    """Return config with the retro Stop entry removed, then added when cmd is given."""
    hooks = config.setdefault("hooks", {})
    groups = []
    for group in hooks.get("Stop", []):
        kept = [h for h in group.get("hooks", []) if MARKER not in str(h.get("command", ""))]
        if kept:
            groups.append({**group, "hooks": kept})
    if cmd:
        groups.append({"hooks": [{"type": "command", "command": cmd, "timeout": 10}]})
    if groups:
        hooks["Stop"] = groups
    else:
        hooks.pop("Stop", None)
    if not hooks:
        config.pop("hooks")
    return config


def main():
    argv = sys.argv[1:]
    extra = argv[argv.index("--") + 1:] if "--" in argv else []
    argv = argv[: argv.index("--")] if "--" in argv else argv
    p = argparse.ArgumentParser()
    p.add_argument("--dest", default=os.getcwd())
    p.add_argument("--provider", default="claude,codex")
    p.add_argument("--shared", action="store_true", help="Claude: use the committed settings.json")
    p.add_argument("--remove", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)
    root = os.path.abspath(args.dest)
    providers = [x.strip() for x in args.provider.split(",") if x.strip()]
    bad = [x for x in providers if x not in SCRIPT]
    if bad:
        raise SystemExit(f"unknown provider(s) {bad}; use claude,codex")
    if not providers:
        raise SystemExit("--provider needs at least one provider; use claude,codex")
    if extra and not args.remove:
        if any(x == "--provider" or x.startswith("--provider=") for x in extra):
            raise SystemExit("choose providers before --; only threshold flags belong after --")
        try:
            build_parser().parse_args(["--provider", "claude"] + extra)
        except SystemExit:
            raise SystemExit(f"invalid hook flags: {' '.join(extra)}")
    registered = False
    for provider in providers:
        rel = config_path(provider, args.shared)
        path = os.path.join(root, rel)
        if not args.remove and not os.path.exists(os.path.join(root, SCRIPT[provider])):
            print(f"skipped {provider}: {SCRIPT[provider]} is missing; sync the session-retro bundle for {provider} first")
            continue
        config = {}
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                config = json.load(f)
        cmd = None if args.remove else command(provider, extra)
        new = update(config, cmd)
        if args.dry_run:
            print(f"[dry run] {rel} would become:\n{json.dumps(new, indent=2)}")
            continue
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(new, f, indent=2)
            f.write("\n")
        registered |= not args.remove
        print(f"{'removed from' if args.remove else 'registered in'} {rel}" + ("" if args.remove else f": {cmd}"))
    if registered:
        print("Codex: review the hook with /hooks. Claude Code: an untrusted folder asks for workspace trust; "
              "in a trusted folder the hook is live as soon as it is written.")


if __name__ == "__main__":
    main()
