import uuid

import pytest

from photobooth.models import Photo


@pytest.mark.django_db
class TestPhotoModel:
    def test_create_photo(self):
        photo = Photo.objects.create()
        assert photo.id is not None
        assert isinstance(photo.id, uuid.UUID)

    def test_default_upload_status(self):
        photo = Photo.objects.create()
        assert photo.upload_status == Photo.UploadStatus.PENDING

    def test_upload_status_choices(self):
        assert Photo.UploadStatus.PENDING == "pending"
        assert Photo.UploadStatus.UPLOADING == "uploading"
        assert Photo.UploadStatus.SUCCESS == "success"
        assert Photo.UploadStatus.FAILED == "failed"

    def test_timestamps_default(self):
        photo = Photo.objects.create()
        assert photo.created_at is not None
        assert photo.email_sent_at is None
        assert photo.uploaded_at is None
        assert photo.upload_attempted_at is None

    def test_upload_error_default(self):
        photo = Photo.objects.create()
        assert photo.upload_error == ""
