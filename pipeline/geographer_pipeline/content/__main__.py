"""``python -m geographer_pipeline.content validate``: check the clue database."""

import argparse
import sys

from geographer_pipeline.content.validate import CONTENT_DIR, load_clues


def main(argv: list[str] | None = None, content_dir=CONTENT_DIR) -> int:
    parser = argparse.ArgumentParser(
        prog="geographer_pipeline.content",
        description="Check the clue database in content/.",
    )
    parser.add_argument("command", choices=["validate"])
    parser.parse_args(argv)
    clues, errors = load_clues(content_dir)
    for error in errors:
        print(error, file=sys.stderr)
    if errors:
        print(f"{len(errors)} problem(s) found.", file=sys.stderr)
        return 1
    print(f"{len(clues)} clues are valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
