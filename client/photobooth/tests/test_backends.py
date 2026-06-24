import os
import uuid
from unittest.mock import patch

import pytest
import responses

from photobooth.backends import get_backend
from photobooth.backends.rsync import RsyncBackend
from photobooth.backends.webdav import WebDAVBackend


class TestGetBackend:
    def test_rsync_backend(self, settings):
        settings.PHOTOBOOTH_BACKEND = "rsync"
        backend = get_backend()
        assert isinstance(backend, RsyncBackend)

    def test_webdav_backend(self, settings):
        settings.PHOTOBOOTH_BACKEND = "webdav"
        backend = get_backend()
        assert isinstance(backend, WebDAVBackend)

    def test_invalid_backend(self, settings):
        settings.PHOTOBOOTH_BACKEND = "invalid"
        with pytest.raises(ValueError, match="Unknown backend"):
            get_backend()


class TestWebDAVBackend:
    @responses.activate
    def test_upload_files(self, media_root, sample_jpeg, settings):
        settings.PHOTOBOOTH_WEBDAV_URL = "https://webdav.example.com/photos/"
        settings.PHOTOBOOTH_WEBDAV_USERNAME = "user"
        settings.PHOTOBOOTH_WEBDAV_PASSWORD = "pass"

        photo_uuid = uuid.uuid4()
        datetime_str = "2024-01-01-12-00-00_"

        for suffix in ["", "_background"]:
            filename = f"{datetime_str}{photo_uuid}{suffix}.jpg"
            filepath = os.path.join(media_root, filename)
            with open(filepath, "wb") as f:
                f.write(sample_jpeg)
            responses.add(
                responses.PUT,
                f"https://webdav.example.com/photos/{filename}",
                status=201,
            )

        backend = WebDAVBackend()
        backend.upload(photo_uuid, datetime_str)

        assert len(responses.calls) == 2
        for call in responses.calls:
            assert call.request.headers["Content-Type"] == "image/jpeg"

    @responses.activate
    def test_upload_skips_missing_file(self, media_root, sample_jpeg, settings):
        settings.PHOTOBOOTH_WEBDAV_URL = "https://webdav.example.com/photos/"
        settings.PHOTOBOOTH_WEBDAV_USERNAME = "user"
        settings.PHOTOBOOTH_WEBDAV_PASSWORD = "pass"

        photo_uuid = uuid.uuid4()
        datetime_str = "2024-01-01-12-00-00_"

        filename = f"{datetime_str}{photo_uuid}.jpg"
        filepath = os.path.join(media_root, filename)
        with open(filepath, "wb") as f:
            f.write(sample_jpeg)
        responses.add(
            responses.PUT,
            f"https://webdav.example.com/photos/{filename}",
            status=201,
        )

        backend = WebDAVBackend()
        backend.upload(photo_uuid, datetime_str)

        assert len(responses.calls) == 1

    @responses.activate
    def test_upload_raises_on_error(self, media_root, sample_jpeg, settings):
        settings.PHOTOBOOTH_WEBDAV_URL = "https://webdav.example.com/photos/"
        settings.PHOTOBOOTH_WEBDAV_USERNAME = "user"
        settings.PHOTOBOOTH_WEBDAV_PASSWORD = "pass"

        photo_uuid = uuid.uuid4()
        datetime_str = "2024-01-01-12-00-00_"

        filename = f"{datetime_str}{photo_uuid}.jpg"
        filepath = os.path.join(media_root, filename)
        with open(filepath, "wb") as f:
            f.write(sample_jpeg)
        responses.add(
            responses.PUT,
            f"https://webdav.example.com/photos/{filename}",
            status=500,
        )

        backend = WebDAVBackend()
        with pytest.raises(Exception):
            backend.upload(photo_uuid, datetime_str)


class TestRsyncBackend:
    @patch("subprocess.check_call")
    def test_upload_calls_rsync(self, mock_check_call, settings):
        settings.PHOTOBOOTH_RSYNC_COMMAND = "rsync -av media/ remote:photos/"
        photo_uuid = uuid.uuid4()
        datetime_str = "2024-01-01-12-00-00_"

        backend = RsyncBackend()
        backend.upload(photo_uuid, datetime_str)

        mock_check_call.assert_called_once_with(
            ["flock", "/tmp/photobooth.lock", "-c", "rsync -av media/ remote:photos/"]
        )
