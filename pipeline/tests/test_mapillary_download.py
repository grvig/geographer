import pytest
from test_mapillary_images import FakeClient

from geographer_pipeline.mapillary.client import MapillaryError
from geographer_pipeline.mapillary.download import download_images, raw_path


class DownloadClient(FakeClient):
    def __init__(self, body=b"\xff\xd8jpeg"):
        super().__init__()
        self.body = body
        self.downloaded = []

    def download(self, url):
        self.downloaded.append(url)
        return self.body


def test_downloads_only_missing_images(tmp_path):
    raw_path("1", tmp_path).write_bytes(b"\xff\xd8old")
    client = DownloadClient()
    assert download_images(client, ["1", "2"], tmp_path) == 1
    assert client.downloaded == ["https://cdn.example/2.jpg?sig=x"]
    assert raw_path("2", tmp_path).read_bytes() == b"\xff\xd8jpeg"
    assert raw_path("1", tmp_path).read_bytes() == b"\xff\xd8old"
    assert download_images(client, ["1", "2"], tmp_path) == 0


def test_rejects_responses_that_are_not_jpegs(tmp_path):
    client = DownloadClient(body=b"<html>expired</html>")
    with pytest.raises(MapillaryError, match="JPEG"):
        download_images(client, ["3"], tmp_path)
    assert list(tmp_path.iterdir()) == []
