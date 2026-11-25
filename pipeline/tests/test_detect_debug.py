import json

from PIL import Image

from geographer_pipeline.detect.debug import draw_detections


def detection(shape):
    return {"id": "d1", "category": "bollard", "score": 0.5, "shape": json.dumps(shape)}


def test_outlines_rects_and_polygons_in_category_colour():
    image = Image.new("RGB", (100, 100), "white")
    rect = detection({"type": "rect", "coords": [0.2, 0.2, 0.4, 0.6]})
    polygon = detection(
        {"type": "polygon", "coords": [[0.6, 0.5], [0.9, 0.5], [0.9, 0.9], [0.6, 0.9]]}
    )
    drawn = draw_detections(image, [rect, polygon], {"bollard": "#ff0000"})
    assert drawn.getpixel((20, 40)) == (255, 0, 0)
    assert drawn.getpixel((90, 70)) == (255, 0, 0)
    # The inside stays untouched, and so does the original image.
    assert drawn.getpixel((30, 40)) == (255, 255, 255)
    assert image.getpixel((20, 40)) == (255, 255, 255)
