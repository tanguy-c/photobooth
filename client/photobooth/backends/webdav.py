import uuid
from pathlib import Path

import requests
from django.conf import settings

from photobooth.backends.base import BaseBackend


class WebDAVBackend(BaseBackend):
    def upload(self, photo_uuid: uuid.UUID, datetime_str: str) -> None:
        base_url = settings.PHOTOBOOTH_WEBDAV_URL.rstrip("/")
        auth = (
            settings.PHOTOBOOTH_WEBDAV_USERNAME,
            settings.PHOTOBOOTH_WEBDAV_PASSWORD,
        )

        filenames = [
            f"{datetime_str}{photo_uuid}.jpg",
            f"{datetime_str}{photo_uuid}_background.jpg",
        ]

        for filename in filenames:
            filepath = Path(settings.MEDIA_ROOT) / filename
            if not filepath.exists():
                continue
            with open(filepath, "rb") as f:
                response = requests.put(
                    f"{base_url}/{filename}",
                    data=f,
                    auth=auth,
                    headers={"Content-Type": "image/jpeg"},
                    timeout=60,
                )
                response.raise_for_status()
