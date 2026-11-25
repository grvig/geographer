from PIL import Image

from geographer_pipeline.detect.crop import crop_box, crop_path, save_crop


def test_pads_by_fifteen_percent_of_the_box():
    # A 200 x 100 px box gets 30 px more on each side and 15 px above and below.
    assert crop_box((0.25, 0.25, 0.45, 0.35), 1000, 1000) == (220, 235, 480, 365)


def test_padding_stops_at_the_image_edge():
    assert crop_box((0.0, 0.9, 0.1, 1.0), 1000, 500) == (0, 442, 115, 500)


def test_saves_the_padded_crop(tmp_path):
    image = Image.new("RGB", (1000, 1000), "white")
    path = crop_path("123", "d1", tmp_path)
    save_crop(image, (0.25, 0.25, 0.45, 0.35), path)
    assert path == tmp_path / "123" / "d1.jpg"
    assert Image.open(path).size == (260, 130)
