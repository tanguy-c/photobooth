import logging

from celery import shared_task
from django.db.models import Q
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

    if Photo.objects.filter(
        id=photo_uuid, upload_status=Photo.UploadStatus.SUCCESS
    ).exists():
        return

    Photo.objects.filter(id=photo_uuid).update(
        upload_status=Photo.UploadStatus.UPLOADING,
        upload_attempted_at=timezone.now(),
    )

    try:
        backend = get_backend()
        backend.upload(photo_uuid, datetime_str)
    except Exception as exc:
        is_final = self.request.retries >= self.max_retries
        Photo.objects.filter(id=photo_uuid).exclude(
            upload_status=Photo.UploadStatus.SUCCESS,
        ).update(
            upload_status=(
                Photo.UploadStatus.FAILED if is_final else Photo.UploadStatus.UPLOADING
            ),
            upload_error=str(exc),
        )
        raise

    Photo.objects.filter(id=photo_uuid).exclude(
        upload_status=Photo.UploadStatus.SUCCESS,
    ).update(
        upload_status=Photo.UploadStatus.SUCCESS,
        upload_error="",
        uploaded_at=timezone.now(),
    )


@shared_task
def retry_failed_uploads():
    from datetime import timedelta

    from photobooth.models import Photo

    cutoff_pending = timezone.now() - timedelta(minutes=10)
    cutoff_stuck = timezone.now() - timedelta(minutes=30)
    photos = Photo.objects.filter(
        Q(upload_status=Photo.UploadStatus.FAILED)
        | Q(upload_status=Photo.UploadStatus.PENDING, created_at__lt=cutoff_pending)
        | Q(
            upload_status=Photo.UploadStatus.UPLOADING,
            upload_attempted_at__lt=cutoff_stuck,
        ),
    )
    count = 0
    for photo in photos:
        upload_photo.delay(str(photo.id), photo.datetime_str)
        count += 1
    if count:
        logger.info("Re-queued %d photos for upload", count)
