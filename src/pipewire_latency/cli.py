"""Command line entry point."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from . import __version__
from .config import default_config_path, list_backups, render_config, restore_config, write_config
from .profiles import PROFILES, get_profile
from .report import render_info, render_json, render_report
from .state import collect_state


def _config_path(value: str | None) -> Path:
    return Path(value).expanduser() if value else default_config_path()


def cmd_info(args: argparse.Namespace) -> int:
    state = collect_state()
    if args.json:
        print(render_json(state))
    else:
        print(render_info(state))
    return 0 if state.is_complete else 1


def cmd_measure(args: argparse.Namespace) -> int:
    state = collect_state()
    if state.buffer_ms is None:
        if args.json:
            print(render_json(state))
        else:
            print("Could not read quantum and sample rate from PipeWire.")
            for warning in state.warnings:
                print(f"  - {warning}")
        return 1

    if args.json:
        print(render_json(state))
    else:
        print(f"buffer latency: {state.buffer_ms:.3f} ms")
        print(f"quantum: {state.quantum} samples at {state.rate} Hz")
    return 0


def cmd_tune(args: argparse.Namespace) -> int:
    profile = get_profile(args.profile)
    path = _config_path(args.config)

    try:
        result = write_config(profile, path, force=args.force, dry_run=args.dry_run)
    except FileExistsError as exc:
        print(exc, file=sys.stderr)
        return 1

    if args.dry_run:
        print(f"# {path}")
        print(result.content, end="")
        return 0

    print(f"wrote {result.path}")
    if result.backup:
        print(f"backup {result.backup}")
    print("restart PipeWire to apply: systemctl --user restart pipewire pipewire-pulse wireplumber")
    return 0


def cmd_restore(args: argparse.Namespace) -> int:
    path = _config_path(args.config)
    existed = path.exists()
    target, backup = restore_config(path)
    if backup:
        print(f"restored {target} from {backup}")
    elif existed:
        print(f"removed {target}")
    else:
        print(f"nothing to restore at {target}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    state = collect_state()
    path = _config_path(args.config)
    profile = get_profile(args.profile) if args.profile else None
    if args.json:
        print(render_json(state, profile, path))
    else:
        print(render_report(state, profile, path))
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    state = collect_state()
    path = _config_path(args.config)
    checks: list[tuple[str, bool, str]] = []

    for command in ("pw-metadata", "pw-dump", "pw-cli", "systemctl"):
        found = shutil.which(command) is not None
        checks.append((f"command {command}", found, "found" if found else "missing"))

    checks.append(("quantum readable", state.quantum is not None, str(state.quantum)))
    checks.append(("sample rate readable", state.rate is not None, str(state.rate)))
    checks.append(("config path", True, str(path)))
    checks.append(("config exists", path.exists(), "yes" if path.exists() else "no"))
    checks.append(("backups", True, str(len(list_backups(path)))))

    failures = 0
    for name, ok, detail in checks:
        mark = "ok" if ok else "fail"
        if not ok:
            failures += 1
        print(f"[{mark}] {name}: {detail}")

    if state.warnings:
        print("")
        for warning in state.warnings:
            print(f"warning: {warning}")

    return 1 if failures else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pipewire-latency",
        description="Inspect and tune PipeWire buffer latency on Linux.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    info = sub.add_parser("info", help="show the active graph quantum and rate")
    info.add_argument("--json", action="store_true")
    info.set_defaults(func=cmd_info)

    measure = sub.add_parser("measure", help="print buffer latency in milliseconds")
    measure.add_argument("--json", action="store_true")
    measure.set_defaults(func=cmd_measure)

    tune = sub.add_parser("tune", help="write a PipeWire drop-in profile")
    tune.add_argument("--profile", choices=sorted(PROFILES), default="balanced")
    tune.add_argument("--config", help="override the drop-in path")
    tune.add_argument("--dry-run", action="store_true")
    tune.add_argument("--force", action="store_true", help="replace an existing drop-in")
    tune.set_defaults(func=cmd_tune)

    restore = sub.add_parser("restore", help="restore the newest backup or remove the drop-in")
    restore.add_argument("--config", help="override the drop-in path")
    restore.set_defaults(func=cmd_restore)

    report = sub.add_parser("report", help="print a markdown report")
    report.add_argument("--profile", choices=sorted(PROFILES))
    report.add_argument("--config", help="override the drop-in path")
    report.add_argument("--json", action="store_true")
    report.set_defaults(func=cmd_report)

    doctor = sub.add_parser("doctor", help="check commands, state, and config")
    doctor.add_argument("--config", help="override the drop-in path")
    doctor.set_defaults(func=cmd_doctor)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
