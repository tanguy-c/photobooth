import io
import os
import uuid

from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.utils import timezone
from exif import DATETIME_STR_FORMAT, GpsAltitudeRef
from exif import Image as ImageExif
from PIL import Image


def _decimal_to_dms(decimal_deg):
    d = int(abs(decimal_deg))
    m = int((abs(decimal_deg) - d) * 60)
    s = round((abs(decimal_deg) - d - m / 60) * 3600, 4)
    return (float(d), float(m), s)


def add_exif_data(photo_uuid: uuid.UUID, now: str):
    filepath = os.path.join(settings.MEDIA_ROOT, f"{now}{str(photo_uuid)}.jpg")
    with open(filepath, "rb") as image_file:
        my_image = ImageExif(image_file)

        my_image.datetime_original = timezone.localtime().strftime(DATETIME_STR_FORMAT)

        gps_coords = settings.PHOTOBOOTH_GPS_COORDINATES
        if gps_coords:
            parts = gps_coords.split(",")
            lat = float(parts[0])
            lon = float(parts[1])
            alt = float(parts[2]) if len(parts) > 2 else 0

            my_image.gps_latitude = _decimal_to_dms(lat)
            my_image.gps_latitude_ref = "N" if lat >= 0 else "S"
            my_image.gps_longitude = _decimal_to_dms(lon)
            my_image.gps_longitude_ref = "E" if lon >= 0 else "W"
            my_image.gps_altitude = alt
            my_image.gps_altitude_ref = GpsAltitudeRef.ABOVE_SEA_LEVEL

        with open(filepath, "wb") as new_my_image:
            new_my_image.write(my_image.get_file())


def duplicate_image_with_background(photo_uuid: uuid.UUID, now: str) -> str:
    filepath = os.path.join(settings.MEDIA_ROOT, f"{now}{str(photo_uuid)}.jpg")
    mask_path = os.path.join(settings.STATIC_ROOT, "img", "photobooth-mask.png")
    with Image.open(filepath) as img:
        background = Image.open(mask_path)

        # Define the coordinates for pasting image 2 onto image 1
        x, y = 0, 0

        img.paste(
            background, (x, y), background
        )  # The third argument, background, is used to manage transparency.

        # Convert the PIL Image to a byte stream
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="JPEG")
        img_bytes.seek(0)

        # Create an InMemoryUploadedFile object
        image_file = InMemoryUploadedFile(
            img_bytes,
            field_name="photo_with_bg",
            name=f"{now}{str(photo_uuid)}_background.jpg",
            content_type="image/jpeg",
            size=len(img_bytes.getvalue()),
            charset=None,
        )

    return default_storage.save(f"{now}{str(photo_uuid)}_background.jpg", image_file)
