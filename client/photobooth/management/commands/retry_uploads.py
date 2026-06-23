from django.core.management.base import BaseCommand

from photobooth.models import Photo
from photobooth.tasks import upload_photo


class Command(BaseCommand):
    help = "Retry uploading photos that are in pending or failed state"

    def add_arguments(self, parser):
        parser.add_argument(
            "--failed-only",
            action="store_true",
            help="Only retry photos that explicitly failed (not pending)",
        )

    def handle(self, *args, **options):
        statuses = [Photo.UploadStatus.FAILED]
        if not options["failed_only"]:
            statuses.append(Photo.UploadStatus.PENDING)

        photos = Photo.objects.filter(upload_status__in=statuses)
        count = photos.count()

        if count == 0:
            self.stdout.write("No photos to retry.")
            return

        for photo in photos:
            upload_photo.delay(str(photo.id), photo.datetime_str)

        self.stdout.write(self.style.SUCCESS(f"Queued {count} photo(s) for upload."))
