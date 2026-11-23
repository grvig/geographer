"""Countries and the areas inside them that start points are sampled from."""

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

AREAS_FILE = Path(__file__).resolve().parents[1] / "areas.yaml"


@dataclass(frozen=True)
class Area:
    name: str
    bbox: list[float]


@dataclass(frozen=True)
class Country:
    code: str
    name: str
    bbox: list[float]
    areas: list[Area]


def check_bbox(bbox: list[float], label: str, within=(-180, -90, 180, 90)) -> None:
    if len(bbox) != 4:
        raise ValueError(f"{label}: bbox needs [west, south, east, north]")
    west, south, east, north = bbox
    if west >= east or south >= north:
        raise ValueError(f"{label}: bbox {bbox} is not a valid box")
    if west < within[0] or south < within[1] or east > within[2] or north > within[3]:
        raise ValueError(f"{label}: bbox {bbox} lies outside {list(within)}")


def load_countries(path: Path = AREAS_FILE) -> list[Country]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    countries = []
    for entry in data["countries"]:
        code = entry["code"]
        if not re.fullmatch(r"[A-Z]{2}", code):
            raise ValueError(f"{code}: country codes are two capital letters")
        check_bbox(entry["bbox"], code)
        areas = []
        for area in entry["areas"]:
            check_bbox(area["bbox"], f"{code} {area['name']}", within=entry["bbox"])
            areas.append(Area(area["name"], area["bbox"]))
        countries.append(Country(code, entry["name"], entry["bbox"], areas))
    return countries
