import numpy as np
import pytest
import torch
from PIL import Image

from geographer_pipeline.match import clip
from geographer_pipeline.match.clip import ClipEmbedder


class FakeModel(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.scale = torch.nn.Parameter(torch.ones(1))

    def encode_image(self, batch):
        # Mean colour per channel: red and green images point different ways.
        return batch.mean(dim=(2, 3)) * self.scale

    def encode_text(self, tokens):
        return tokens.float()


def fake_embedder():
    embedder = ClipEmbedder("fake", "none", device="cpu")
    embedder.model = FakeModel()
    embedder.preprocess = lambda image: torch.tensor(
        np.asarray(image, dtype=np.float32).transpose(2, 0, 1)
    )
    embedder.tokenizer = lambda texts: torch.tensor([[len(t), 1.0, 0.0] for t in texts])
    return embedder


def test_image_embeddings_are_unit_length_and_batched(monkeypatch):
    monkeypatch.setattr(clip, "BATCH_SIZE", 2)
    images = [Image.new("RGB", (4, 4), colour) for colour in ["red", "green", "red"]]
    vectors = fake_embedder().embed_images(images)
    assert vectors.shape == (3, 3)
    assert np.linalg.norm(vectors, axis=1) == pytest.approx([1, 1, 1])
    assert vectors[0] @ vectors[2] == pytest.approx(1)
    assert vectors[0] @ vectors[1] == pytest.approx(0)


def test_text_embeddings_are_unit_length():
    vectors = fake_embedder().embed_texts(["a post", "a stone"])
    assert np.linalg.norm(vectors, axis=1) == pytest.approx([1, 1])


def test_name_records_model_and_weights():
    assert ClipEmbedder("ViT-B-16", "datacomp").name == "ViT-B-16/datacomp"
