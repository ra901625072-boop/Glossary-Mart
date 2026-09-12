import io
import os
from PIL import Image

IMAGE_MAGIC_BYTES = {
    'jpeg': [b'\xff\xd8\xff'],
    'jpg': [b'\xff\xd8\xff'],
    'png': [b'\x89PNG\r\n\x1a\n'],
    'gif': [b'GIF87a', b'GIF89a'],
    'webp': [b'RIFF']
}


def allowed_file(filename, allowed_extensions):
    """Check if file extension is allowed."""
    if not filename or '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in allowed_extensions


def validate_image_file(file_obj, allowed_extensions=None):
    """
    Validates that file_obj is a legitimate, safe image file.
    Validates:
      1. Filename extension is in allowed_extensions.
      2. File header magic bytes match known image formats.
      3. PIL parses and verifies the image without errors.
    Resets file pointer to 0 after validation.
    Returns (bool, str) tuple: (is_valid, error_or_extension).
    """
    if not file_obj or not getattr(file_obj, 'filename', None):
        return False, "No file provided"

    filename = file_obj.filename
    if '.' not in filename:
        return False, "Missing file extension"

    ext = filename.rsplit('.', 1)[1].lower()
    if allowed_extensions and ext not in allowed_extensions:
        return False, f"Extension '.{ext}' is not permitted"

    # Read header bytes for magic byte verification
    file_obj.seek(0)
    header = file_obj.read(32)
    file_obj.seek(0)

    if len(header) < 8:
        return False, "File is too small to be a valid image"

    # Magic byte check
    is_magic_valid = False
    if header.startswith(b'\xff\xd8\xff'):
        is_magic_valid = True
    elif header.startswith(b'\x89PNG\r\n\x1a\n'):
        is_magic_valid = True
    elif header.startswith(b'GIF87a') or header.startswith(b'GIF89a'):
        is_magic_valid = True
    elif header.startswith(b'RIFF') and len(header) >= 12 and header[8:12] == b'WEBP':
        is_magic_valid = True

    if not is_magic_valid:
        return False, "File content does not match allowed image signatures"

    # Deep verification with Pillow
    try:
        file_obj.seek(0)
        with Image.open(file_obj) as img:
            img.verify()
            format_name = (img.format or '').lower()
            if format_name not in {'jpeg', 'png', 'gif', 'webp'}:
                return False, f"Unsupported image format: {img.format}"
    except Exception as e:
        return False, f"Corrupted or invalid image file: {e}"
    finally:
        file_obj.seek(0)

    return True, ext

