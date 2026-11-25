from geographer_pipeline.detect.geometry import Detection
from geographer_pipeline.detect.merge import merge_detections

POLE = [(0.4, 0.1), (0.42, 0.1), (0.42, 0.6), (0.4, 0.6)]


def test_mapillary_outline_wins_over_an_overlapping_owl_box():
    mapillary = [
        Detection("utility-pole", "mapillary", (0.4, 0.1, 0.42, 0.6), 1.0, POLE)
    ]
    owl = [
        Detection("utility-pole", "owl", (0.399, 0.1, 0.421, 0.58), 0.5),
        Detection("bollard", "owl", (0.7, 0.5, 0.72, 0.6), 0.4),
        Detection("bollard", "owl", (0.1, 0.5, 0.12, 0.6), 0.35),
    ]
    merged = merge_detections(mapillary, owl)
    assert [(d.source, d.box[0]) for d in merged] == [
        ("owl", 0.1),
        ("mapillary", 0.4),
        ("owl", 0.7),
    ]


def test_a_box_merely_touching_an_outline_is_kept():
    mapillary = [Detection("street-light", "mapillary", (0.0, 0.0, 0.2, 0.2), 1.0)]
    owl = [Detection("bollard", "owl", (0.1, 0.1, 0.3, 0.3), 0.6)]
    assert len(merge_detections(mapillary, owl)) == 2
