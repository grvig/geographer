import pytest

from geographer_pipeline.areas import load_analysis_areas, load_countries


def test_shipped_areas_load_in_priority_order():
    countries = load_countries()
    assert [country.code for country in countries] == ["IN", "US", "BR", "RU", "FR"]
    assert all(country.areas for country in countries)


@pytest.mark.parametrize(
    ("country_bbox", "area_bbox", "message"),
    [
        ([0, 0, 10, 10], [5, 5, 4, 6], "not a valid box"),
        ([0, 0, 10, 10], [5, 5, 6], "west, south, east, north"),
        ([0, 0, 10, 10], [8, 8, 12, 9], "lies outside"),
        ([0, 0, 190, 10], [8, 8, 9, 9], "lies outside"),
    ],
)
def test_bad_boxes_are_rejected(tmp_path, country_bbox, area_bbox, message):
    path = tmp_path / "areas.yaml"
    path.write_text(
        "countries:\n"
        f"  - {{code: XX, name: Test, bbox: {country_bbox}, areas:\n"
        f"      [{{name: Town, bbox: {area_bbox}}}]}}\n"
    )
    with pytest.raises(ValueError, match=message):
        load_countries(path)


def test_shipped_analysis_areas_load():
    areas = load_analysis_areas()
    assert areas["saulieu"].country == "FR"
    assert areas["saulieu"].limit > 0


@pytest.mark.parametrize(
    ("entry", "message"),
    [
        ("{name: Big Town, country: XX, bbox: [1, 1, 2, 2], limit: 5}", "kebab-case"),
        ("{name: town, country: ZZ, bbox: [1, 1, 2, 2], limit: 5}", "unknown country"),
        ("{name: town, country: XX, bbox: [1, 1, 20, 2], limit: 5}", "lies outside"),
    ],
)
def test_bad_analysis_areas_are_rejected(tmp_path, entry, message):
    path = tmp_path / "areas.yaml"
    path.write_text(
        "countries:\n"
        "  - {code: XX, name: Test, bbox: [0, 0, 10, 10], areas: []}\n"
        f"analysis:\n  - {entry}\n"
    )
    with pytest.raises(ValueError, match=message):
        load_analysis_areas(path)
