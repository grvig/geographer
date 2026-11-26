import pytest

from geographer_pipeline.match.location import is_consistent

CLUE = {
    "regions": [
        {"country": "IN", "admin1": "Karnataka", "strength": "typical"},
        {"country": "FR", "strength": "also-seen"},
    ]
}


@pytest.mark.parametrize(
    ("country", "admin1", "expected"),
    [
        ("IN", "Karnataka", True),
        ("IN", "Tamil Nadu", False),
        ("FR", "Bourgogne", True),
        ("FR", None, True),
        ("BR", "Parana", False),
        (None, None, False),
    ],
)
def test_checks_country_and_region(country, admin1, expected):
    assert is_consistent(CLUE, country, admin1) is expected
