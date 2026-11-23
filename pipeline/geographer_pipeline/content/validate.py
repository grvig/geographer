"""Checks the clue database before it is built into the site's clues.json."""

import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

CONTENT_DIR = Path(__file__).resolve().parents[3] / "content"


def schema_errors(content_dir: Path, name: str, data, label: str) -> list[str]:
    path = content_dir / "schema" / f"{name}.schema.json"
    validator = Draft202012Validator(json.loads(path.read_text(encoding="utf-8")))
    errors = []
    for error in validator.iter_errors(data):
        where = "/".join(str(part) for part in error.absolute_path)
        errors.append(f"{label}: {where or '(top level)'}: {error.message}")
    return sorted(errors)


def load_categories(content_dir: Path = CONTENT_DIR) -> tuple[list[dict], list[str]]:
    path = content_dir / "categories.yaml"
    categories = yaml.safe_load(path.read_text(encoding="utf-8"))
    errors = schema_errors(content_dir, "categories", categories, "categories.yaml")
    if errors:
        return [], errors
    seen = set()
    for category in categories:
        if category["id"] in seen:
            errors.append(f"categories.yaml: duplicate id {category['id']}")
        seen.add(category["id"])
    return categories, errors
