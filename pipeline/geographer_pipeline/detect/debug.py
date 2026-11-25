"""Draws cached detections onto their image, to check the detectors by eye."""

import json

from PIL import ImageDraw

from geographer_pipeline.cache import DATA_DIR

DEBUG_DIR = DATA_DIR / "debug"


def draw_detections(image, detections, colours: dict[str, str]):
    canvas = image.copy()
    draw = ImageDraw.Draw(canvas)
    width, height = canvas.size
    for detection in detections:
        shape = json.loads(detection["shape"])
        colour = colours.get(detection["category"], "#ffffff")
        if shape["type"] == "rect":
            x0, y0, x1, y1 = shape["coords"]
            points = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        else:
            points = shape["coords"]
        pixels = [(x * width, y * height) for x, y in points]
        draw.polygon(pixels, outline=colour, width=3)
        left = min(x for x, _ in pixels)
        top = min(y for _, y in pixels)
        label = f"{detection['id']} {detection['category']} {detection['score']:.2f}"
        draw.text((left, max(0, top - 14)), label, fill=colour)
    return canvas
