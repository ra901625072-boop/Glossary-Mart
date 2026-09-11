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
    def upload_file(cls, file):
        """Uploads a file to S3 if configured, else saves locally."""
        filename = secure_filename(file.filename)
        filename = f"{datetime.now().timestamp()}_{filename}"
        
        bucket_name = os.getenv('AWS_BUCKET_NAME')
        s3_client = cls.get_s3_client()
        
        if bucket_name and s3_client:
            # Upload to S3
            try:
                s3_client.upload_fileobj(
                    file,
                    bucket_name,
                    filename,
                    ExtraArgs={'ACL': 'public-read'} # Or whatever your bucket ACL requires
                )
                # Return the S3 URL
                return f"https://{bucket_name}.s3.amazonaws.com/{filename}"
            except Exception as e:
                current_app.logger.error(f"S3 Upload failed: {e}")
                raise e
        else:
            # Fallback to local storage
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            return f"uploads/{filename}"

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
