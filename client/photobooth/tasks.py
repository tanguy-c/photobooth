import logging

from celery import shared_task
from django.utils import timezone

from photobooth.backends import get_backend

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    max_retries=5,
    retry_backoff=60,
    retry_backoff_max=3600,
    retry_jitter=True,
)
def upload_photo(self, photo_uuid, datetime_str):
    from photobooth.models import Photo

    try:
        backend = get_backend()
        backend.upload(photo_uuid, datetime_str)
    except Exception:
        Photo.objects.filter(id=photo_uuid).update(
            upload_status=Photo.UploadStatus.FAILED,
            upload_error=f"Upload failed, retry {self.request.retries}/{self.max_retries}",
        )
        raise

    Photo.objects.filter(id=photo_uuid).update(
        upload_status=Photo.UploadStatus.SUCCESS,
        upload_error="",
        uploaded_at=timezone.now(),
    )


@shared_task
def retry_failed_uploads():
    from datetime import timedelta

    from photobooth.models import Photo

    # Only retry photos older than 2 minutes (give the initial task time to complete)
    cutoff = timezone.now() - timedelta(minutes=2)
    photos = Photo.objects.filter(
        upload_status__in=[Photo.UploadStatus.PENDING, Photo.UploadStatus.FAILED],
        created_at__lt=cutoff,
    )
    count = 0
    for photo in photos:
        upload_photo.delay(str(photo.id), photo.datetime_str)
        count += 1
    if count:
        logger.info("Re-queued %d photos for upload", count)
