"""Command-line interface for running PgVault scans."""

from __future__ import annotations

import argparse
import asyncio

from pgvault.config import load_config
from pgvault.orchestrator import run_scan


def build_parser() -> argparse.ArgumentParser:
    """Build the PgVault CLI argument parser."""

    parser = argparse.ArgumentParser(prog="pgvault")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("scan", help="Run a PgVault catalog scan and print JSON.")
    return parser


async def _run_scan_command() -> int:
    """Execute a scan and print the JSON result."""

    result = await run_scan(load_config())
    print(result.model_dump_json(indent=2))
    return 0


def main() -> int:
    """CLI entrypoint used by `python -m pgvault`."""

    parser = build_parser()
    args = parser.parse_args()
    if args.command in {None, "scan"}:
        return asyncio.run(_run_scan_command())
    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
