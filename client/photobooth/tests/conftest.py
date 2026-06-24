import base64
import io
import os

import pytest
from PIL import Image

from photobooth.models import Photo


@pytest.fixture(autouse=True)
def media_root(tmp_path, settings):
    settings.MEDIA_ROOT = str(tmp_path / "media")
    os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
    settings.DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"
    settings.STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
            "OPTIONS": {"location": settings.MEDIA_ROOT},
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
    return settings.MEDIA_ROOT


@pytest.fixture(autouse=True)
def static_root(tmp_path, settings):
    static_dir = str(tmp_path / "static")
    settings.STATIC_ROOT = static_dir
    os.makedirs(os.path.join(static_dir, "img"), exist_ok=True)
    return static_dir


@pytest.fixture
def mask_image(static_root):
    mask_path = os.path.join(static_root, "img", "photobooth-mask.png")
    img = Image.new("RGBA", (640, 480), (0, 0, 0, 0))
    img.save(mask_path, format="PNG")
    return mask_path


def _make_jpeg_bytes(width=640, height=480):
    img = Image.new("RGB", (width, height), color=(255, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture
def sample_jpeg():
    return _make_jpeg_bytes()


@pytest.fixture
def sample_photo_data_uri(sample_jpeg):
    encoded = base64.b64encode(sample_jpeg).decode("utf-8")
    return f"data:image/jpeg;base64{encoded}"


@pytest.fixture
def saved_photo(media_root, sample_jpeg, mask_image, db):
    import uuid

    from django.core.files.base import ContentFile
    from django.core.files.storage import default_storage

    photo_uuid = uuid.uuid4()
    now = "2024-01-01-12-00-00_"

    filename = f"{now}{photo_uuid}.jpg"
    default_storage.save(filename, ContentFile(sample_jpeg))

    bg_filename = f"{now}{photo_uuid}_background.jpg"
    default_storage.save(bg_filename, ContentFile(sample_jpeg))

    photo = Photo.objects.create(
        id=photo_uuid,
        photo=filename,
        photo_with_bg=bg_filename,
        datetime_str=now,
    )
    return photo
