import pytest

from geographer_pipeline.detect.owl import DECOY_PROMPTS, OwlDetector

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
    assert detector.prompts["a post"] == ("bollard", 0.3)
    assert detector.prompts["a milestone"] == ("kilometre-marker", 0.5)
    assert detector.prompts[DECOY_PROMPTS[0]] == (None, 0.0)
    assert len(detector.prompts) == 3 + len(DECOY_PROMPTS)


def test_applies_each_categorys_threshold_and_normalises_boxes():
    detector = OwlDetector(CATEGORIES, device="cpu")
    boxes = [[100, 50, 200, 250], [0, 0, 30, 30], [-5, 400, 2100, 600]]
    scores = [0.42, 0.45, 0.61]
    labels = ["a post", "a milestone", "a milestone"]
    detections = detector.to_detections(boxes, scores, labels, 2000, 1000)
    # Highest score first.
    assert [d.category for d in detections] == ["kilometre-marker", "bollard"]
    assert detections[1].box == pytest.approx((0.05, 0.05, 0.1, 0.25))
    assert detections[1].source == "owl"
    # Boxes that spill over the edge are clipped to the image.
    assert detections[0].box == pytest.approx((0.0, 0.4, 1.0, 0.6))


def test_without_prompts_nothing_is_loaded():
    detector = OwlDetector(CATEGORIES[2:], device="cpu")
    assert detector.detect(image=None) == []
    assert detector.model is None


def test_drops_small_boxes_and_duplicates():
    detector = OwlDetector(CATEGORIES, device="cpu")
    boxes = [[100, 100, 140, 200], [102, 100, 142, 200], [500, 500, 520, 600]]
    detections = detector.to_detections(
        boxes, [0.4, 0.6, 0.9], ["a bollard", "a post", "a bollard"], 2000, 1000
    )
    # The 20 px wide box is too small; the two overlapping bollards are one object.
    assert len(detections) == 1
    assert detections[0].score == 0.6


def test_decoys_suppress_overlapping_boxes_and_are_dropped():
    detector = OwlDetector(CATEGORIES, device="cpu")
    sign_post = [100, 100, 140, 300]
    detections = detector.to_detections(
        [sign_post, [102, 100, 142, 300], [500, 100, 540, 300]],
        [0.5, 0.35, 0.45],
        [DECOY_PROMPTS[0], "a bollard", "a bollard"],
        2000,
        1000,
    )
    assert [d.box[0] for d in detections] == [0.25]
