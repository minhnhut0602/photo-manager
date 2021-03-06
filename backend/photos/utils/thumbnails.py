import os

from django.conf import settings
from django.utils import timezone
from PIL import Image, ImageOps

from photos.models import Photo
from photos.utils.metadata import PhotoMetadata


def generate_thumbnails_for_photo(photo):
    if not isinstance(photo, Photo):
        photo = Photo.objects.get(id=photo)
    for thumbnail in settings.THUMBNAIL_SIZES:
        try:
            generate_thumbnail(photo, thumbnail[0], thumbnail[1], thumbnail[2], thumbnail[3])
        except (FileNotFoundError, IndexError):
            pass


def generate_thumbnail(photo, width=256, height=256, aspect='cover', quality=75):
    pf = photo.files.filter(mimetype='image/jpeg')[0]
    im = Image.open(pf.path)

    if im.mode != 'RGB':
        im = im.convert("RGB")

    metadata = PhotoMetadata(pf.path)

    if metadata.get('Orientation') in ['Rotate 90 CW', 'Rotate 270 CCW']:
        im = im.rotate(-90, expand=True)
    elif metadata.get('Orientation') in ['Rotate 90 CCW', 'Rotate 270 CW']:
        im = im.rotate(90, expand=True)

    if aspect == 'cover':
        im = ImageOps.fit(im, (width, height), Image.ANTIALIAS)
    else:
        im.thumbnail((width, height), Image.ANTIALIAS)

    directory = os.path.join(settings.THUMBNAIL_ROOT, '{}x{}_{}_q{}'.format(width, height, aspect, quality))
    if not os.path.exists(directory):
        os.makedirs(directory)

    path = os.path.join(directory, '{}.jpg'.format(photo.id))

    im.save(path, format='JPEG', quality=quality)

    photo.last_thumbnailed_version = 0
    photo.last_thumbnailed_at = timezone.now()
    photo.save()
