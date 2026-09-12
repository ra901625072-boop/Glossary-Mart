import os
from datetime import datetime

import boto3
from flask import current_app
from werkzeug.utils import secure_filename


class StorageService:
    _s3_client = None

    @classmethod
    def get_s3_client(cls):
        """Returns a singleton S3 client, or None if not configured properly."""
        if cls._s3_client is None:
            bucket_name = os.getenv('AWS_BUCKET_NAME')
            aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
            aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
            
            if not bucket_name:
                return None
                
            if not aws_access_key or not aws_secret_key:
                if current_app:
                    current_app.logger.warning("AWS_BUCKET_NAME is set, but AWS credentials are missing!")
                return None
                
            cls._s3_client = boto3.client(
                's3',
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key,
                region_name=os.getenv('AWS_REGION', 'us-east-1')
            )
        return cls._s3_client

    @classmethod
    def upload_file(cls, file, allowed_extensions=None):
        """Uploads a validated image file using UUID naming to S3 or local storage."""
        import uuid
        from backend.utils.files import validate_image_file

        if allowed_extensions is None and current_app:
            allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif', 'webp'})

        is_valid, result = validate_image_file(file, allowed_extensions)
        if not is_valid:
            raise ValueError(f"File upload rejected: {result}")

        ext = result
        safe_name = f"{uuid.uuid4().hex}.{ext}"

        bucket_name = os.getenv('AWS_BUCKET_NAME')
        s3_client = cls.get_s3_client()

        if bucket_name and s3_client:
            # Upload to S3
            try:
                s3_client.upload_fileobj(
                    file,
                    bucket_name,
                    safe_name,
                    ExtraArgs={'ACL': 'public-read'}
                )
                # Return the S3 URL
                return f"https://{bucket_name}.s3.amazonaws.com/{safe_name}"
            except Exception as e:
                current_app.logger.error(f"S3 Upload failed: {e}")
                raise e
        else:
            # Fallback to local storage
            upload_dir = current_app.config.get('UPLOAD_FOLDER', 'frontend/static/uploads')
            os.makedirs(upload_dir, exist_ok=True)
            filepath = os.path.join(upload_dir, safe_name)
            if hasattr(file, 'save'):
                file.save(filepath)
            else:
                file.seek(0)
                with open(filepath, 'wb') as f_out:
                    f_out.write(file.read())
            return f"uploads/{safe_name}"

    @classmethod
    def delete_file(cls, path_or_url):
        """Deletes a file from S3 or local."""
        if not path_or_url:
            return
            
        bucket_name = os.getenv('AWS_BUCKET_NAME')
        s3_client = cls.get_s3_client()
        
        if bucket_name and s3_client and path_or_url.startswith('http'):
            # S3 deletion
            try:
                filename = path_or_url.split('/')[-1]
                s3_client.delete_object(Bucket=bucket_name, Key=filename)
            except Exception as e:
                current_app.logger.error(f"S3 Deletion failed: {e}")
            # Local deletion
            static_folder = current_app.static_folder if current_app and current_app.static_folder else 'frontend/static'
            old_image_path = os.path.join(static_folder, path_or_url)
            if not os.path.exists(old_image_path) and current_app:
                upload_dir = current_app.config.get('UPLOAD_FOLDER', 'frontend/static/uploads')
                alt_path = os.path.join(upload_dir, os.path.basename(path_or_url))
                if os.path.exists(alt_path):
                    old_image_path = alt_path

            if os.path.exists(old_image_path) and not os.path.isdir(old_image_path):
                try:
                    os.remove(old_image_path)
                except OSError:
                    pass
