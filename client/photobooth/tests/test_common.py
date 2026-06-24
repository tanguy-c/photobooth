import os
import uuid

import pytest
from exif import Image as ImageExif
from PIL import Image

from photobooth.common import (
    _decimal_to_dms,
    add_exif_data,
    duplicate_image_with_background,
)


class TestDecimalToDms:
    def test_positive_value(self):
        result = _decimal_to_dms(43.601298)
        assert result[0] == 43.0
        assert result[1] == 36.0
        assert abs(result[2] - 4.6728) < 0.01

    def test_negative_value(self):
        result = _decimal_to_dms(-73.935242)
        assert result[0] == 73.0
        assert result[1] == 56.0
        assert abs(result[2] - 6.8712) < 0.01

    def test_zero(self):
        result = _decimal_to_dms(0.0)
        assert result == (0.0, 0.0, 0.0)

    def test_integer_value(self):
        result = _decimal_to_dms(45.0)
        assert result == (45.0, 0.0, 0.0)


@pytest.mark.django_db
class TestAddExifData:
    def test_adds_datetime(self, media_root, sample_jpeg):
        photo_uuid = uuid.uuid4()
        now = "2024-01-01-12-00-00_"
        filepath = os.path.join(media_root, f"{now}{photo_uuid}.jpg")
        with open(filepath, "wb") as f:
            f.write(sample_jpeg)

        add_exif_data(photo_uuid, now)

        with open(filepath, "rb") as f:
            img = ImageExif(f)
        assert img.has_exif
        assert hasattr(img, "datetime_original")

    def test_adds_gps_coordinates(self, media_root, sample_jpeg, settings):
        settings.PHOTOBOOTH_GPS_COORDINATES = "43.601298,1.454514,155"
        photo_uuid = uuid.uuid4()
        now = "2024-01-01-12-00-00_"
        filepath = os.path.join(media_root, f"{now}{photo_uuid}.jpg")
        with open(filepath, "wb") as f:
            f.write(sample_jpeg)

        add_exif_data(photo_uuid, now)

        with open(filepath, "rb") as f:
            img = ImageExif(f)
        assert hasattr(img, "gps_latitude")
        assert hasattr(img, "gps_longitude")
        assert img.gps_latitude_ref == "N"
        assert img.gps_longitude_ref == "E"

    def test_no_gps_when_empty(self, media_root, sample_jpeg, settings):
        settings.PHOTOBOOTH_GPS_COORDINATES = ""
        photo_uuid = uuid.uuid4()
        now = "2024-01-01-12-00-00_"
        filepath = os.path.join(media_root, f"{now}{photo_uuid}.jpg")
        with open(filepath, "wb") as f:
            f.write(sample_jpeg)

        add_exif_data(photo_uuid, now)

        with open(filepath, "rb") as f:
            img = ImageExif(f)
        assert not hasattr(img, "gps_latitude")

    def test_southern_hemisphere(self, media_root, sample_jpeg, settings):
        settings.PHOTOBOOTH_GPS_COORDINATES = "-33.8688,151.2093"
        photo_uuid = uuid.uuid4()
        now = "2024-01-01-12-00-00_"
        filepath = os.path.join(media_root, f"{now}{photo_uuid}.jpg")
        with open(filepath, "wb") as f:
            f.write(sample_jpeg)

        add_exif_data(photo_uuid, now)

        with open(filepath, "rb") as f:
            img = ImageExif(f)
        assert img.gps_latitude_ref == "S"
        assert img.gps_longitude_ref == "E"
        assert img.gps_altitude == 0


@pytest.mark.django_db
class TestDuplicateImageWithBackground:
    def test_creates_background_image(self, media_root, sample_jpeg, mask_image):
        photo_uuid = uuid.uuid4()
        now = "2024-01-01-12-00-00_"
        filepath = os.path.join(media_root, f"{now}{photo_uuid}.jpg")
        with open(filepath, "wb") as f:
            f.write(sample_jpeg)

        result = duplicate_image_with_background(photo_uuid, now)

        assert result is not None
        saved_path = os.path.join(media_root, result)
        assert os.path.exists(saved_path)

        with Image.open(saved_path) as img:
            assert img.format == "JPEG"

    def test_output_filename(self, media_root, sample_jpeg, mask_image):
        photo_uuid = uuid.uuid4()
        now = "2024-01-01-12-00-00_"
        filepath = os.path.join(media_root, f"{now}{photo_uuid}.jpg")
        with open(filepath, "wb") as f:
            f.write(sample_jpeg)

        result = duplicate_image_with_background(photo_uuid, now)

        assert "_background.jpg" in result
        assert str(photo_uuid) in result
