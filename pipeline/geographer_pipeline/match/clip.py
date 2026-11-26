"""CLIP embeddings for crops, reference photos and clue descriptions."""

import numpy as np

BATCH_SIZE = 32


class ClipEmbedder:
    def __init__(self, model_name: str, pretrained: str, device: str = "cuda"):
        self.model_name = model_name
        self.pretrained = pretrained
        self.device = device
        self.model = None
        self.preprocess = None
        self.tokenizer = None

    @property
    def name(self) -> str:
        # Stored with every embedding, so a model change never mixes vectors.
        return f"{self.model_name}/{self.pretrained}"

    def load(self) -> None:
        import open_clip

        model, _, preprocess = open_clip.create_model_and_transforms(
            self.model_name, pretrained=self.pretrained
        )
        # fp16 on the GPU keeps the model well inside 4 GB.
        if self.device == "cuda":
            model = model.half()
        self.model = model.to(self.device).eval()
        self.preprocess = preprocess
        self.tokenizer = open_clip.get_tokenizer(self.model_name)

    def _normalised(self, encode, batch) -> np.ndarray:
        import torch

        with torch.no_grad():
            vectors = encode(batch.to(self.device)).float()
        vectors = torch.nn.functional.normalize(vectors, dim=-1)
        return vectors.cpu().numpy()

    def embed_images(self, images: list) -> np.ndarray:
        import torch

        if self.model is None:
            self.load()
        dtype = next(self.model.parameters()).dtype
        parts = []
        for start in range(0, len(images), BATCH_SIZE):
            chunk = images[start : start + BATCH_SIZE]
            batch = torch.stack(
                [self.preprocess(image.convert("RGB")) for image in chunk]
            )
            parts.append(self._normalised(self.model.encode_image, batch.to(dtype)))
        if not parts:
            return np.zeros((0, 0), dtype=np.float32)
        return np.concatenate(parts)

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        if self.model is None:
            self.load()
        return self._normalised(self.model.encode_text, self.tokenizer(texts))
