import os
from datetime import datetime

import boto3
from flask import current_app
from werkzeug.utils import secure_filename


class StorageService:
    @staticmethod
    def upload_file(file):
        """Uploads a file to S3 if configured, else saves locally."""
        filename = secure_filename(file.filename)
        filename = f"{datetime.now().timestamp()}_{filename}"
        
        bucket_name = os.getenv('AWS_BUCKET_NAME')
        
        if bucket_name:
            # Upload to S3
            s3_client = boto3.client(
                's3',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                region_name=os.getenv('AWS_REGION', 'us-east-1')
            )
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

    @staticmethod
    def delete_file(path_or_url):
        """Deletes a file from S3 or local."""
        if not path_or_url:
            return
            
        bucket_name = os.getenv('AWS_BUCKET_NAME')
        if bucket_name and path_or_url.startswith('http'):
            # S3 deletion
            try:
                filename = path_or_url.split('/')[-1]
                s3_client = boto3.client(
                    's3',
                    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                    region_name=os.getenv('AWS_REGION', 'us-east-1')
                )
                s3_client.delete_object(Bucket=bucket_name, Key=filename)
            except Exception as e:
                current_app.logger.error(f"S3 Deletion failed: {e}")
        else:
            # Local deletion
            old_image_path = os.path.join('static', path_or_url)
            if os.path.exists(old_image_path) and not os.path.isdir(old_image_path):
                try:
                    os.remove(old_image_path)
                except OSError:
                    pass
