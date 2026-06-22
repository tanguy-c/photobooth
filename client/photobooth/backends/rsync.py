import subprocess
import uuid

from django.conf import settings

from photobooth.backends.base import BaseBackend


class RsyncBackend(BaseBackend):
    def upload(self, photo_uuid: uuid.UUID, datetime_str: str) -> None:
        subprocess.check_call(
            ["flock", "/tmp/photobooth.lock", "-c", settings.PHOTOBOOTH_RSYNC_COMMAND]
        )
