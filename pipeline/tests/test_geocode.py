from test_mapillary_images import FakeClient

from geographer_pipeline.cache import area_images, connect
from geographer_pipeline.geocode import geocode_images, locate
from geographer_pipeline.mapillary.images import cache_images


def test_locates_country_and_region():
    places = locate([(47.30, 4.24), (12.97, 77.59)])
    assert places == [("FR", "Bourgogne"), ("IN", "Karnataka")]
    assert locate([]) == []


def test_fills_in_places_for_an_area_once(tmp_path):
    db = connect(tmp_path / "cache.sqlite")
    # The fake images sit at 47.3 N, 4.2 E, in Burgundy.
    cache_images(FakeClient(), db, ["1", "2"], "FR/test")
    assert geocode_images(db, "FR/test") == 2
    assert geocode_images(db, "FR/test") == 0
    row = area_images(db, "FR/test")[0]
    assert (row["country"], row["admin1"]) == ("FR", "Bourgogne")
