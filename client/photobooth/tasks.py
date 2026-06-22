from celery import shared_task

from photobooth.backends import get_backend


@shared_task
def upload_photo(photo_uuid, datetime_str):
    backend = get_backend()
    backend.upload(photo_uuid, datetime_str)
