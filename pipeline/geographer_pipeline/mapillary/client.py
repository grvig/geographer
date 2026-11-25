"""Thin Mapillary client: Graph API calls and vector tiles, with retries."""

import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

GRAPH_URL = "https://graph.mapillary.com"
TILES_URL = "https://tiles.mapillary.com"
ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
RETRY_STATUSES = {429, 500, 502, 503, 504}


class MapillaryError(Exception):
    pass


def load_token(env_file: Path = ENV_FILE) -> str:
    load_dotenv(env_file)
    token = os.environ.get("MAPILLARY_TOKEN", "").strip()
    if not token:
        raise MapillaryError(f"MAPILLARY_TOKEN is not set. Add it to {env_file}.")
    return token


class MapillaryClient:
    retries = 4
    backoff = 1.0

    def __init__(self, token: str, session=None, sleep=time.sleep):
        self.token = token
        self.session = session or requests.Session()
        self.session.headers["Authorization"] = f"OAuth {token}"
        self.sleep = sleep

    def get(
        self, url: str, params: dict | None = None, headers: dict | None = None
    ) -> requests.Response:
        # Errors leave out the query, so tokens and signatures stay out of logs.
        name = url.split("?")[0]
        for attempt in range(self.retries + 1):
            last_attempt = attempt == self.retries
            wait = self.backoff * 2**attempt
            try:
                response = self.session.get(
                    url, params=params, headers=headers, timeout=30
                )
            except (requests.ConnectionError, requests.Timeout) as error:
                if last_attempt:
                    raise MapillaryError(f"Could not reach {name}") from error
                self.sleep(wait)
                continue
            if response.status_code in RETRY_STATUSES and not last_attempt:
                self.sleep(wait)
                continue
            if not response.ok:
                raise MapillaryError(f"HTTP {response.status_code} from {name}")
            return response
        raise MapillaryError(f"No response from {name}")

    def tile(self, z: int, x: int, y: int) -> bytes:
        url = f"{TILES_URL}/maps/vtp/mly1_public/2/{z}/{x}/{y}"
        return self.get(url, {"access_token": self.token}).content

    def graph(self, path: str, fields: list[str], **params) -> dict:
        params["fields"] = ",".join(fields)
        return self.get(f"{GRAPH_URL}/{path}", params).json()

    def download(self, url: str) -> bytes:
        # Image URLs are signed CDN links: the token is not needed and is not sent.
        return self.get(url, headers={"Authorization": None}).content
