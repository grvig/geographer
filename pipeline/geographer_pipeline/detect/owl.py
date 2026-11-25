"""OWLv2 open-vocabulary detection, for objects Mapillary doesn't detect."""

from geographer_pipeline.detect.geometry import (
    Detection,
    non_max_suppression,
)

MODEL_NAME = "google/owlv2-base-patch16-ensemble"
# Smaller boxes are too few pixels to crop and match reliably.
MIN_SIDE_PX = 24
NMS_IOU = 0.5
# Things that look like our posts but aren't clues. OWLv2 labels each box with
# its best-matching prompt, so these soak up sign posts that would otherwise be
# called bollards; boxes they win are dropped. Checked on Burgundy roads, where
# without them every "bollard" was a sign post.
DECOY_PROMPTS = ["a traffic sign on a pole", "a street name sign"]


class OwlDetector:
    def __init__(self, categories: list[dict], device: str = "cuda"):
        # Every prompt points back to its category and that category's threshold.
        self.prompts = {}
        for category in categories:
            owl = category["detector"].get("owl")
            if owl:
                for prompt in owl["prompts"]:
                    self.prompts[prompt] = (category["id"], owl["threshold"])
        for prompt in DECOY_PROMPTS:
            self.prompts[prompt] = (None, 0.0)
        self.device = device
        self.model = None
        self.processor = None

    def load(self) -> None:
        import torch
        from transformers import Owlv2ForObjectDetection, Owlv2Processor

        # fp16 halves the memory on the 4 GB laptop GPU; the CPU needs fp32.
        dtype = torch.float32
        if self.device == "cuda":
            dtype = torch.float16
        self.processor = Owlv2Processor.from_pretrained(MODEL_NAME)
        model = Owlv2ForObjectDetection.from_pretrained(MODEL_NAME, dtype=dtype)
        self.model = model.to(self.device).eval()

    def detect(self, image) -> list[Detection]:
        import torch

        if not any(category for category, _ in self.prompts.values()):
            return []
        if self.model is None:
            self.load()
        labels = list(self.prompts)
        inputs = self.processor(text=[labels], images=image, return_tensors="pt")
        inputs = inputs.to(self.device)
        inputs["pixel_values"] = inputs["pixel_values"].to(self.model.dtype)
        with torch.no_grad():
            outputs = self.model(**inputs)
        # Boxes come back in the original image's pixels (checked on transformers
        # 5.24: the processor undoes its own square padding).
        lowest = min(
            threshold for category, threshold in self.prompts.values() if category
        )
        result = self.processor.post_process_grounded_object_detection(
            outputs=outputs,
            target_sizes=[(image.height, image.width)],
            threshold=lowest,
            text_labels=[labels],
        )[0]
        return self.to_detections(
            result["boxes"].tolist(),
            result["scores"].tolist(),
            result["text_labels"],
            image.width,
            image.height,
        )

    def to_detections(self, boxes, scores, labels, width, height) -> list[Detection]:
        detections = []
        for (x0, y0, x1, y1), score, label in zip(boxes, scores, labels, strict=True):
            category, threshold = self.prompts[label]
            if score < threshold:
                continue
            if min(x1 - x0, y1 - y0) < MIN_SIDE_PX:
                continue
            box = (
                max(0.0, x0 / width),
                max(0.0, y0 / height),
                min(1.0, x1 / width),
                min(1.0, y1 / height),
            )
            detections.append(Detection(category, "owl", box, round(score, 3)))
        # Decoys take part in suppression, so a sign post found as a decoy also
        # removes the weaker bollard box on top of it, and are then dropped.
        kept = non_max_suppression(detections, NMS_IOU)
        return [detection for detection in kept if detection.category]
