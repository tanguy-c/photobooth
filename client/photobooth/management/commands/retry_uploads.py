from django.core.management.base import BaseCommand

from photobooth.models import Photo
from photobooth.tasks import upload_photo


class Command(BaseCommand):
    help = "Retry uploading photos that are in pending, uploading, or failed state"

    def add_arguments(self, parser):
        parser.add_argument(
            "--failed-only",
            action="store_true",
            help="Only retry photos that explicitly failed (not pending or stuck uploading)",
        )

    def handle(self, *args, **options):
        if options["failed_only"]:
            photos = Photo.objects.filter(upload_status=Photo.UploadStatus.FAILED)
        else:
            photos = Photo.objects.filter(
                upload_status__in=[
                    Photo.UploadStatus.PENDING,
                    Photo.UploadStatus.UPLOADING,
                    Photo.UploadStatus.FAILED,
                ],
            )

        count = 0
        for photo in photos:
            upload_photo.delay(str(photo.id), photo.datetime_str)
            count += 1

        if count == 0:
            self.stdout.write("No photos to retry.")
        else:
            self.stdout.write(self.style.SUCCESS(f"Queued {count} photo(s) for upload."))
