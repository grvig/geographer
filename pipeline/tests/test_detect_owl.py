import pytest

from geographer_pipeline.detect.owl import OwlDetector

CATEGORIES = [
    {
        "id": "bollard",
        "detector": {"owl": {"prompts": ["a bollard", "a post"], "threshold": 0.3}},
    },
    {
        "id": "kilometre-marker",
        "detector": {"owl": {"prompts": ["a milestone"], "threshold": 0.5}},
    },
    {"id": "street-light", "detector": {"mapillary": ["object--street-light"]}},
]


def test_prompts_point_to_their_category_and_threshold():
    detector = OwlDetector(CATEGORIES, device="cpu")
    assert detector.prompts == {
        "a bollard": ("bollard", 0.3),
        "a post": ("bollard", 0.3),
        "a milestone": ("kilometre-marker", 0.5),
    }


def test_applies_each_categorys_threshold_and_normalises_boxes():
    detector = OwlDetector(CATEGORIES, device="cpu")
    boxes = [[100, 50, 200, 250], [0, 0, 10, 10], [-5, 400, 2100, 600]]
    scores = [0.42, 0.45, 0.61]
    labels = ["a post", "a milestone", "a milestone"]
    detections = detector.to_detections(boxes, scores, labels, 2000, 1000)
    assert [d.category for d in detections] == ["bollard", "kilometre-marker"]
    assert detections[0].box == pytest.approx((0.05, 0.05, 0.1, 0.25))
    assert detections[0].source == "owl"
    # Boxes that spill over the edge are clipped to the image.
    assert detections[1].box == pytest.approx((0.0, 0.4, 1.0, 0.6))


def test_without_prompts_nothing_is_loaded():
    detector = OwlDetector(CATEGORIES[2:], device="cpu")
    assert detector.detect(image=None) == []
    assert detector.model is None
