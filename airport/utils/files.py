import os
import uuid

from django.utils.text import slugify


def generate_image_file_path(
    name: str,
    filename: str,
    uploads_dir: str
) -> str:
    _, extension = os.path.splitext(filename)
    filename = f"{slugify(name)}-{uuid.uuid4()}{extension}"

    return os.path.join(uploads_dir, filename)
