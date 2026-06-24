from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command

from photobooth.models import Photo


@pytest.mark.django_db
class TestRetryUploadsCommand:
    @patch("photobooth.tasks.upload_photo.delay")
    def test_retries_all_non_success(self, mock_delay):
        Photo.objects.create(
            upload_status=Photo.UploadStatus.FAILED,
            datetime_str="2024-01-01-12-00-00_",
        )
        Photo.objects.create(
            upload_status=Photo.UploadStatus.PENDING,
            datetime_str="2024-01-01-12-00-01_",
        )
        Photo.objects.create(
            upload_status=Photo.UploadStatus.UPLOADING,
            datetime_str="2024-01-01-12-00-02_",
        )
        Photo.objects.create(
            upload_status=Photo.UploadStatus.SUCCESS,
            datetime_str="2024-01-01-12-00-03_",
        )

        out = StringIO()
        call_command("retry_uploads", stdout=out)

        assert mock_delay.call_count == 3
        assert "3 photo(s)" in out.getvalue()

    @patch("photobooth.tasks.upload_photo.delay")
    def test_failed_only_flag(self, mock_delay):
        Photo.objects.create(
            upload_status=Photo.UploadStatus.FAILED,
            datetime_str="2024-01-01-12-00-00_",
        )
        Photo.objects.create(
            upload_status=Photo.UploadStatus.PENDING,
            datetime_str="2024-01-01-12-00-01_",
        )

        out = StringIO()
        call_command("retry_uploads", "--failed-only", stdout=out)

        assert mock_delay.call_count == 1
        assert "1 photo(s)" in out.getvalue()

    @patch("photobooth.tasks.upload_photo.delay")
    def test_no_photos_to_retry(self, mock_delay):
        Photo.objects.create(
            upload_status=Photo.UploadStatus.SUCCESS,
            datetime_str="2024-01-01-12-00-00_",
        )

        out = StringIO()
        call_command("retry_uploads", stdout=out)

        mock_delay.assert_not_called()
        assert "No photos to retry" in out.getvalue()
