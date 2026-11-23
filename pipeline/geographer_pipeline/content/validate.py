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


def load_clues(content_dir: Path = CONTENT_DIR) -> tuple[list[dict], list[str]]:
    categories, errors = load_categories(content_dir)
    category_ids = {category["id"] for category in categories}
    clues = []
    files_by_id = {}
    for path in sorted((content_dir / "clues").glob("*/*.yaml")):
        label = path.relative_to(content_dir).as_posix()
        try:
            clue = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as error:
            errors.append(f"{label}: not valid YAML: {error}")
            continue
        problems = schema_errors(content_dir, "clue", clue, label)
        if problems:
            errors.extend(problems)
            continue
        clue_id = clue["id"]
        if path.stem != clue_id:
            errors.append(f"{label}: file name must match the id {clue_id}")
        if path.parent.name != clue["category"]:
            errors.append(f"{label}: belongs in clues/{clue['category']}/")
        if clue["category"] not in category_ids:
            errors.append(f"{label}: unknown category {clue['category']}")
        if clue_id in files_by_id:
            errors.append(f"{label}: id {clue_id} is used by {files_by_id[clue_id]}")
            continue
        files_by_id[clue_id] = label
        for reference in clue.get("references", []):
            if not (content_dir / "refs" / reference["file"]).is_file():
                errors.append(f"{label}: missing refs/{reference['file']}")
        clues.append(clue)
    for clue in clues:
        label = files_by_id[clue["id"]]
        for other in clue.get("lookalikes", []):
            if other == clue["id"]:
                errors.append(f"{label}: a clue can't be its own look-alike")
            elif other not in files_by_id:
                errors.append(f"{label}: unknown look-alike {other}")
    return clues, errors
