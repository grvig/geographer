"""OWLv2 open-vocabulary detection, for objects Mapillary doesn't detect."""

from geographer_pipeline.detect.geometry import Detection

MODEL_NAME = "google/owlv2-base-patch16-ensemble"


class OwlDetector:
    def __init__(self, categories: list[dict], device: str = "cuda"):
        # Every prompt points back to its category and that category's threshold.
        self.prompts = {}
        for category in categories:
            owl = category["detector"].get("owl")
            if owl:
                for prompt in owl["prompts"]:
                    self.prompts[prompt] = (category["id"], owl["threshold"])
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

        if not self.prompts:
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
        lowest = min(threshold for _, threshold in self.prompts.values())
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
            box = (
                max(0.0, x0 / width),
                max(0.0, y0 / height),
                min(1.0, x1 / width),
                min(1.0, y1 / height),
            )
            detections.append(Detection(category, "owl", box, round(score, 3)))
        return detections
