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
    export = commands.add_parser("export", help="write shards for an analysis area")
    export.add_argument("area", help="an analysis area name from areas.yaml")
    debug = commands.add_parser("debug", help="draw cached detections on images")
    debug.add_argument("images", nargs="+", help="Mapillary image ids")
    return parser


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
    from geographer_pipeline.areas import load_analysis_areas
    from geographer_pipeline.cache import connect
    from geographer_pipeline.content.validate import load_categories
    from geographer_pipeline.detect.mapillary import class_map
    from geographer_pipeline.detect.owl import OwlDetector
    from geographer_pipeline.detect.run import detect_area
    from geographer_pipeline.mapillary.client import MapillaryClient, load_token

    area = load_analysis_areas().get(args.area)
    if area is None:
        print(f"Unknown area {args.area}; see the analysis list in pipeline/areas.yaml")
        return 2
    categories, errors = load_categories()
    if errors:
        print("\n".join(errors))
        return 1
    client = MapillaryClient(load_token())
    owl = OwlDetector(categories, args.device)
    with connect() as db:
        detect_area(client, db, area, owl, class_map(categories))
    return 0


def run_export(args: argparse.Namespace) -> int:
    from geographer_pipeline.areas import load_analysis_areas
    from geographer_pipeline.cache import connect, images_with_detections
    from geographer_pipeline.export.index import add_analysed
    from geographer_pipeline.export.shards import export_area

    area = load_analysis_areas().get(args.area)
    if area is None:
        print(f"Unknown area {args.area}; see the analysis list in pipeline/areas.yaml")
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
    if args.command == "export":
        return run_export(args)
    if args.command == "debug":
        return run_debug(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
