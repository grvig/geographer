"""Matching settings from pipeline/matching.yaml."""

from dataclasses import dataclass
from pathlib import Path

import yaml

SETTINGS_FILE = Path(__file__).resolve().parents[2] / "matching.yaml"


@dataclass(frozen=True)
class Settings:
    model: str
    pretrained: str
    weight: float
    temperature: float
    none_visual: float
    threshold: float
    margin: float


def load_settings(path: Path = SETTINGS_FILE) -> Settings:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    settings = Settings(**data)
    for name in ["weight", "none_visual", "threshold", "margin"]:
        value = getattr(settings, name)
        if not 0 <= value <= 1:
            raise ValueError(
                f"{path.name}: {name} must be between 0 and 1, not {value}"
            )
    if settings.temperature <= 0:
        raise ValueError(f"{path.name}: temperature must be above 0")
    return settings
