"""Command-line entry point: ``python -m geographer_pipeline <command>``."""

import argparse
import sys

from geographer_pipeline import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="geographer_pipeline",
        description="Fetch Mapillary imagery, detect and match clues, export shards.",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_subparsers(dest="command", metavar="<command>")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
