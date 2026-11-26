import pytest

from geographer_pipeline.match.settings import load_settings


def test_shipped_settings_load():
    settings = load_settings()
    assert settings.model == "ViT-B-16"
    assert 0 < settings.weight < 1


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ("weight: 1.5", "weight must be between 0 and 1"),
        ("temperature: 0", "temperature must be above 0"),
    ],
)
def test_out_of_range_values_are_rejected(tmp_path, change, message):
    lines = [
        "model: ViT-B-16",
        "pretrained: x",
        "weight: 0.75",
        "temperature: 0.02",
        "none_visual: 0.7",
        "threshold: 0.5",
        "margin: 0.1",
    ]
    key = change.split(":")[0]
    lines = [line for line in lines if not line.startswith(key)] + [change]
    path = tmp_path / "matching.yaml"
    path.write_text("\n".join(lines))
    with pytest.raises(ValueError, match=message):
        load_settings(path)


def test_unknown_or_missing_keys_fail(tmp_path):
    path = tmp_path / "matching.yaml"
    path.write_text("model: ViT-B-16\n")
    with pytest.raises(TypeError):
        load_settings(path)
