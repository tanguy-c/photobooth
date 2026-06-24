from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from django.utils import timezone

from photobooth.models import Photo


@pytest.mark.django_db
class TestUploadPhotoTask:
    @patch("photobooth.tasks.get_backend")
    def test_upload_success(self, mock_get_backend, db):
        mock_backend = MagicMock()
        mock_get_backend.return_value = mock_backend

        photo = Photo.objects.create(
            upload_status=Photo.UploadStatus.PENDING,
            datetime_str="2024-01-01-12-00-00_",
        )

        from photobooth.tasks import upload_photo

        upload_photo(str(photo.id), photo.datetime_str)

        photo.refresh_from_db()
        assert photo.upload_status == Photo.UploadStatus.SUCCESS
        assert photo.upload_error == ""
        assert photo.uploaded_at is not None
        mock_backend.upload.assert_called_once_with(str(photo.id), photo.datetime_str)

    @patch("photobooth.tasks.get_backend")
    def test_already_uploaded_skips(self, mock_get_backend, db):
        mock_backend = MagicMock()
        mock_get_backend.return_value = mock_backend

        photo = Photo.objects.create(
            upload_status=Photo.UploadStatus.SUCCESS,
            datetime_str="2024-01-01-12-00-00_",
        )

        from photobooth.tasks import upload_photo

        upload_photo(str(photo.id), photo.datetime_str)

        mock_backend.upload.assert_not_called()

    @patch("photobooth.tasks.get_backend")
    def test_upload_failure_sets_error(self, mock_get_backend, db):
        mock_backend = MagicMock()
        mock_backend.upload.side_effect = ConnectionError("timeout")
        mock_get_backend.return_value = mock_backend

        photo = Photo.objects.create(
            upload_status=Photo.UploadStatus.PENDING,
            datetime_str="2024-01-01-12-00-00_",
        )

        from photobooth.tasks import upload_photo

        with pytest.raises(ConnectionError):
            upload_photo(str(photo.id), photo.datetime_str)

        photo.refresh_from_db()
        assert photo.upload_status in [
            Photo.UploadStatus.UPLOADING,
            Photo.UploadStatus.FAILED,
        ]
        assert "timeout" in photo.upload_error


@pytest.mark.django_db
class TestRetryFailedUploads:
    @patch("photobooth.tasks.upload_photo.delay")
    def test_retries_failed_photos(self, mock_delay, db):
        Photo.objects.create(
            upload_status=Photo.UploadStatus.FAILED,
            datetime_str="2024-01-01-12-00-00_",
        )
        Photo.objects.create(
            upload_status=Photo.UploadStatus.SUCCESS,
            datetime_str="2024-01-01-12-00-01_",
        )

        from photobooth.tasks import retry_failed_uploads

        retry_failed_uploads()

        assert mock_delay.call_count == 1

    @patch("photobooth.tasks.upload_photo.delay")
    def test_retries_stale_pending(self, mock_delay, db):
        Photo.objects.create(
            upload_status=Photo.UploadStatus.PENDING,
            datetime_str="2024-01-01-12-00-00_",
            created_at=timezone.now() - timedelta(minutes=15),
        )

        from photobooth.tasks import retry_failed_uploads

        retry_failed_uploads()

        assert mock_delay.call_count == 1

    @patch("photobooth.tasks.upload_photo.delay")
    def test_retries_stuck_uploading(self, mock_delay, db):
        Photo.objects.create(
            upload_status=Photo.UploadStatus.UPLOADING,
            datetime_str="2024-01-01-12-00-00_",
            upload_attempted_at=timezone.now() - timedelta(minutes=35),
        )

        from photobooth.tasks import retry_failed_uploads

        retry_failed_uploads()

        assert mock_delay.call_count == 1

    @patch("photobooth.tasks.upload_photo.delay")
    def test_skips_recent_pending(self, mock_delay, db):
        Photo.objects.create(
            upload_status=Photo.UploadStatus.PENDING,
            datetime_str="2024-01-01-12-00-00_",
        )

        from photobooth.tasks import retry_failed_uploads

        retry_failed_uploads()

        mock_delay.assert_not_called()

    @patch("photobooth.tasks.upload_photo.delay")
    def test_no_photos_to_retry(self, mock_delay, db):
        from photobooth.tasks import retry_failed_uploads

        retry_failed_uploads()

        mock_delay.assert_not_called()
