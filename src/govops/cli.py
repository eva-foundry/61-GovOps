"""CLI entry points for GovOps.

Two console scripts are exposed:

* ``govops-demo``     — runs the demo server (legacy entry, preserved verbatim).
* ``govops``          — multi-command dispatcher (``govops demo``, ``govops impact-of``).

The ``demo`` subcommand is identical in behaviour to ``govops-demo``.
"""

from __future__ import annotations

import argparse
import os
import sys


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_DEMO_BANNER = (
    "  GovOps - Policy-Driven Service Delivery Machine\n"
    "  Pension Eligibility Case Study Demo"
)


def _add_demo_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Bind port (default: 8000)")
    parser.add_argument(
        "--reload", action="store_true", help="Enable auto-reload for development"
    )


def _run_demo(host: str, port: int, reload: bool) -> int:
    try:
        import uvicorn
    except ImportError:
        print("Error: uvicorn is required. Install with: pip install govops", file=sys.stderr)
        return 1

    print()
    print(_DEMO_BANNER)
    print()
    print(f"  Open http://{host}:{port} in your browser")
    print()
    print(f"  API docs:        http://{host}:{port}/docs")
    print(f"  Authority chain: http://{host}:{port}/authority")
    print()

    uvicorn.run(
        "govops.api:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )
    return 0


def _run_impact(citation: str, db_path: str | None, json_out: bool) -> int:
    """Phase 7 CLI: print every ConfigValue referencing ``citation``.

    The store hydrates from ``db_path`` if provided (or ``GOVOPS_DB_PATH``),
    otherwise an ephemeral in-memory store is hydrated from ``lawcode/`` so
    a freshly-cloned repo prints meaningful results without setup.
    """
    from pathlib import Path

    from govops.config import ConfigStore

    resolved_db = db_path or os.environ.get("GOVOPS_DB_PATH")
    store = ConfigStore(db_path=resolved_db)

    if resolved_db is None:
        lawcode = Path(__file__).resolve().parent.parent.parent / "lawcode"
        if lawcode.is_dir():
            store.load_from_yaml(lawcode)

    rows = store.find_by_citation(citation)

    if json_out:
        import json

        payload = [
            {
                "id": r.id,
                "key": r.key,
                "jurisdiction_id": r.jurisdiction_id,
                "value": r.value,
                "value_type": r.value_type,
                "effective_from": r.effective_from.isoformat() if r.effective_from else None,
                "effective_to": r.effective_to.isoformat() if r.effective_to else None,
                "citation": r.citation,
                "status": r.status,
            }
            for r in rows
        ]
        print(json.dumps({"query": citation, "total": len(rows), "results": payload}, indent=2))
        return 0

    if not rows:
        print(f"No ConfigValues reference «{citation}».")
        return 0

    print(f"  {len(rows)} record(s) referencing «{citation}»")
    print()
    current_scope: object = object()
    for r in rows:
        scope = r.jurisdiction_id or "global"
        if scope != current_scope:
            print(f"  [{scope}]")
            current_scope = scope
        date = r.effective_from.date().isoformat() if r.effective_from else "?"
        print(f"    {date}  {r.key}  →  {r.value!r}")
        print(f"               citation: {r.citation}")
    print()
    return 0


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------

def main():
    """Legacy ``govops-demo`` entry: starts the demo server."""
    parser = argparse.ArgumentParser(
        description="GovOps - Policy-Driven Service Delivery Machine",
    )
    _add_demo_args(parser)
    args = parser.parse_args()
    raise SystemExit(_run_demo(args.host, args.port, args.reload))


def dispatch(argv: list[str] | None = None) -> int:
    """``govops`` entry: multi-command dispatcher."""
    parser = argparse.ArgumentParser(
        prog="govops",
        description="GovOps - Policy-Driven Service Delivery Machine",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    demo_p = sub.add_parser("demo", help="Run the demo server")
    _add_demo_args(demo_p)

    impact_p = sub.add_parser(
        "impact-of",
        help="Find ConfigValues referencing a statutory citation",
    )
    impact_p.add_argument("citation", help="Citation substring (case-insensitive)")
    impact_p.add_argument(
        "--db",
        default=None,
        help="SQLite path; defaults to GOVOPS_DB_PATH or an ephemeral hydrated from lawcode/",
    )
    impact_p.add_argument(
        "--json",
        action="store_true",
        dest="json_out",
        help="Emit JSON instead of human-readable output",
    )

    args = parser.parse_args(argv)
    if args.command == "demo":
        return _run_demo(args.host, args.port, args.reload)
    if args.command == "impact-of":
        return _run_impact(args.citation, args.db, args.json_out)
    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(dispatch())
