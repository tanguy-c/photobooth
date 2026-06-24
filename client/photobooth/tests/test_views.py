import json
import uuid
from unittest.mock import patch

import pytest
from django.test import Client

from photobooth.models import Photo


@pytest.fixture
def client():
    return Client()


@pytest.mark.django_db
class TestHomeView:
    def test_home_returns_200(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_home_uses_template(self, client):
        response = client.get("/")
        assert "photobooth/index.html" in [t.name for t in response.templates]


@pytest.mark.django_db
class TestPhotoView:
    @patch("photobooth.views.duplicate_image_with_background")
    @patch("photobooth.views.add_exif_data")
    @patch("photobooth.tasks.upload_photo.delay")
    def test_valid_photo_upload(
        self,
        mock_upload_delay,
        mock_add_exif,
        mock_duplicate,
        client,
        sample_photo_data_uri,
        settings,
    ):
        mock_duplicate.return_value = "test_background.jpg"
        settings.PHOTOBOOTH_USE_QR_CODE = True

        response = client.post(
            "/photo/",
            data=sample_photo_data_uri,
            content_type="text/plain",
        )

        assert response.status_code == 200
        photo_uuid = response.content.decode()
        assert Photo.objects.filter(id=photo_uuid).exists()
        mock_add_exif.assert_called_once()
        mock_duplicate.assert_called_once()
        mock_upload_delay.assert_called_once()

    @patch("photobooth.views.duplicate_image_with_background")
    @patch("photobooth.views.add_exif_data")
    def test_photo_qr_disabled(
        self,
        mock_add_exif,
        mock_duplicate,
        client,
        sample_photo_data_uri,
        settings,
    ):
        mock_duplicate.return_value = "test_background.jpg"
        settings.PHOTOBOOTH_USE_QR_CODE = False

        response = client.post(
            "/photo/",
            data=sample_photo_data_uri,
            content_type="text/plain",
        )

        assert response.status_code == 200
        photo_uuid = response.content.decode()
        photo = Photo.objects.get(id=photo_uuid)
        assert photo.upload_status == Photo.UploadStatus.SUCCESS

    def test_invalid_data_returns_400(self, client):
        response = client.post(
            "/photo/",
            data="not-a-valid-data-uri",
            content_type="text/plain",
        )
        assert response.status_code == 400


@pytest.mark.django_db
class TestQrCodeView:
    def test_qrcode_link(self, client, saved_photo):
        response = client.get(f"/qrcode/{saved_photo.id}/")
        assert response.status_code == 200
        assert response["Content-Type"] == "image/png"

    def test_qrcode_link_404(self, client):
        fake_uuid = uuid.uuid4()
        response = client.get(f"/qrcode/{fake_uuid}/")
        assert response.status_code == 404

    def test_qrcode_background_link(self, client, saved_photo):
        response = client.get(f"/qrcode-background/{saved_photo.id}/")
        assert response.status_code == 200
        assert response["Content-Type"] == "image/png"

    def test_qrcode_background_link_404(self, client):
        fake_uuid = uuid.uuid4()
        response = client.get(f"/qrcode-background/{fake_uuid}/")
        assert response.status_code == 404


@pytest.mark.django_db
class TestImgResultView:
    def test_img_result(self, client, saved_photo):
        response = client.get(f"/img-result/{saved_photo.id}/")
        assert response.status_code == 200
        assert response["Content-Type"] == "image/jpeg"

    def test_img_result_404(self, client):
        fake_uuid = uuid.uuid4()
        response = client.get(f"/img-result/{fake_uuid}/")
        assert response.status_code == 404


@pytest.mark.django_db
class TestEmailView:
    def test_send_email(self, client, saved_photo, settings):
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

        response = client.post(
            "/email/",
            data=json.dumps({"uuid": str(saved_photo.id), "email": "test@example.com"}),
            content_type="application/json",
        )

        assert response.status_code == 200
        saved_photo.refresh_from_db()
        assert saved_photo.email == "test@example.com"
        assert saved_photo.email_sent_at is not None

    def test_email_404(self, client):
        fake_uuid = uuid.uuid4()
        response = client.post(
            "/email/",
            data=json.dumps({"uuid": str(fake_uuid), "email": "test@example.com"}),
            content_type="application/json",
        )
        assert response.status_code == 404
