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
    commands = parser.add_subparsers(dest="command", metavar="<command>")
    index = commands.add_parser("index", help="list start points for each country")
    index.add_argument("countries", nargs="*", help="country codes (default: all)")
    index.add_argument("--tiles-per-area", type=int, default=5)
    index.add_argument("--limit", type=int, default=500, help="start points each")
    index.add_argument("--seed", type=int, default=0)
    detect = commands.add_parser("detect", help="find objects in an analysis area")
    detect.add_argument("area", help="an analysis area name from areas.yaml")
    detect.add_argument("--device", default="cuda", help="cuda or cpu")
    detect.add_argument(
        "--redo", action="store_true", help="detect again in images already done"
    )
    match = commands.add_parser("match", help="match an area's objects to clues")
    match.add_argument("area", help="an analysis area name from areas.yaml")
    match.add_argument("--device", default="cuda", help="cuda or cpu")
    export = commands.add_parser("export", help="write shards for an analysis area")
    export.add_argument("area", help="an analysis area name from areas.yaml")
    debug = commands.add_parser("debug", help="draw cached detections on images")
    debug.add_argument("images", nargs="+", help="Mapillary image ids")
    return parser


def find_area(name: str):
    from geographer_pipeline.areas import load_analysis_areas

    area = load_analysis_areas().get(name)
    if area is None:
        print(f"Unknown area {name}; see the analysis list in pipeline/areas.yaml")
    return area


def run_index(args: argparse.Namespace) -> int:
    from geographer_pipeline.areas import load_countries
    from geographer_pipeline.export.index import INDEX_DIR, build_indexes
    from geographer_pipeline.mapillary.client import MapillaryClient, load_token

    countries = load_countries()
    if args.countries:
        wanted = [code.upper() for code in args.countries]
        countries = [country for country in countries if country.code in wanted]
        if len(countries) != len(wanted):
            print(f"Unknown country code in {wanted}; see pipeline/areas.yaml")
            return 2
    client = MapillaryClient(load_token())
    failed = build_indexes(
        client, countries, INDEX_DIR, args.tiles_per_area, args.limit, args.seed
    )
    if failed:
        return 1
    return 0


def run_detect(args: argparse.Namespace) -> int:
    from geographer_pipeline.cache import connect
    from geographer_pipeline.content.validate import load_categories
    from geographer_pipeline.detect.mapillary import class_map
    from geographer_pipeline.detect.owl import OwlDetector
    from geographer_pipeline.detect.run import detect_area
    from geographer_pipeline.mapillary.client import MapillaryClient, load_token

    area = find_area(args.area)
    if area is None:
        return 2
    categories, errors = load_categories()
    if errors:
        print("\n".join(errors))
        return 1
    client = MapillaryClient(load_token())
    owl = OwlDetector(categories, args.device)
    with connect() as db:
        detect_area(client, db, area, owl, class_map(categories), redo=args.redo)
    return 0


def run_match(args: argparse.Namespace) -> int:
    from geographer_pipeline.cache import connect
    from geographer_pipeline.content.validate import load_categories, load_clues
    from geographer_pipeline.match.clip import ClipEmbedder
    from geographer_pipeline.match.references import build_candidates
    from geographer_pipeline.match.run import match_area
    from geographer_pipeline.match.settings import load_settings

    area = find_area(args.area)
    if area is None:
        return 2
    clues, errors = load_clues()
    if errors:
        print("\n".join(errors))
        return 1
    categories, _ = load_categories()
    settings = load_settings()
    embedder = ClipEmbedder(settings.model, settings.pretrained, args.device)
    candidates = build_candidates(categories, clues, embedder)
    by_id = {clue["id"]: clue for clue in clues}
    with connect() as db:
        total, matched = match_area(
            db, area.name, embedder, candidates, by_id, settings
        )
    print(f"{area.name}: {matched} of {total} objects matched to a clue")
    return 0


def run_export(args: argparse.Namespace) -> int:
    from geographer_pipeline.cache import connect, images_with_detections
    from geographer_pipeline.export.index import add_analysed
    from geographer_pipeline.export.shards import export_area

    area = find_area(args.area)
    if area is None:
        return 2
    with connect() as db:
        paths = export_area(db, area)
        found = images_with_detections(db, area.name)
    # Images with something found in them become start points on the site.
    total = add_analysed(area.country, found)
    print(f"{area.name}: {len(paths)} shards, {total} analysed start points")
    return 0


def run_debug(args: argparse.Namespace) -> int:
    from PIL import Image

    from geographer_pipeline.cache import connect, image_detections
    from geographer_pipeline.content.validate import load_categories
    from geographer_pipeline.detect.debug import DEBUG_DIR, draw_detections
    from geographer_pipeline.mapillary.download import raw_path

    categories, _ = load_categories()
    colours = {category["id"]: category["overlay_colour"] for category in categories}
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    missing = 0
    with connect() as db:
        for image_id in args.images:
            if not raw_path(image_id).exists():
                print(f"{image_id}: not downloaded; run detect first")
                missing += 1
                continue
            image = Image.open(raw_path(image_id)).convert("RGB")
            drawn = draw_detections(image, image_detections(db, image_id), colours)
            path = DEBUG_DIR / f"{image_id}.png"
            drawn.save(path)
            print(path)
    if missing:
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 1
    if args.command == "index":
        return run_index(args)
    if args.command == "detect":
        return run_detect(args)
    if args.command == "match":
        return run_match(args)
    if args.command == "export":
        return run_export(args)
    if args.command == "debug":
        return run_debug(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
