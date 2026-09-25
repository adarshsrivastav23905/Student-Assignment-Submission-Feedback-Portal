"""
Storage Service
===============
Abstracts file storage operations. Supports two backends:
1. LOCAL: Stores files on the local filesystem (development)
2. CLOUD: Stores files in cloud object storage (production)

Cloud Concept: This is the CLOUD OBJECT STORAGE layer.
- Database stores METADATA (who submitted, when, marks, feedback)
- Object Storage stores ACTUAL FILES (PDFs, DOCXs, ZIPs)

Storage Path Convention:
    assignments/{assignment_id}/students/{student_id}/{filename}

This separation is a core cloud architecture pattern:
- Metadata → Cloud Database (fast queries, indexing)
- Binary files → Object Storage (cheap, scalable, durable)
"""

import os
import uuid
import shutil
from werkzeug.utils import secure_filename
from backend.config import Config


class StorageService:
    """
    Unified storage service that works with local filesystem or cloud storage.
    
    In production, replace the local methods with cloud SDK calls:
    - Firebase Storage: firebase_admin.storage
    - AWS S3: boto3.client('s3')
    - Google Cloud Storage: google.cloud.storage
    - Supabase Storage: supabase.storage
    """

    def __init__(self):
        self.backend = Config.STORAGE_BACKEND
        self.upload_dir = Config.LOCAL_UPLOAD_DIR

        # Ensure local upload directory exists
        if self.backend == "local":
            os.makedirs(self.upload_dir, exist_ok=True)

    def upload_file(self, file, assignment_id, student_id, original_filename):
        """
        Upload a file to storage.

        Args:
            file: File object (from request.files)
            assignment_id: ID of the assignment
            student_id: ID of the student
            original_filename: Original name of the uploaded file

        Returns:
            dict: Contains storage_path and file_url

        Cloud Concept: In cloud deployment, this uploads to a cloud bucket.
        The storage_path is the key/path within the bucket.
        """
        # Generate a unique filename to prevent collisions
        safe_name = secure_filename(original_filename)
        ext = safe_name.rsplit(".", 1)[-1] if "." in safe_name else "bin"
        unique_filename = f"{uuid.uuid4().hex[:8]}_{safe_name}"

        # Create storage path following cloud convention
        storage_path = f"assignments/{assignment_id}/students/{student_id}/{unique_filename}"

        if self.backend == "local":
            return self._upload_local(file, storage_path)
        else:
            return self._upload_cloud(file, storage_path)

    def download_file(self, storage_path):
        """
        Get file path or URL for downloading.

        Args:
            storage_path: Path to the file in storage

        Returns:
            str: Local file path or cloud download URL
        """
        if self.backend == "local":
            return self._get_local_path(storage_path)
        else:
            return self._get_cloud_url(storage_path)

    def delete_file(self, storage_path):
        """
        Delete a file from storage.

        Args:
            storage_path: Path to the file in storage

        Returns:
            bool: True if deleted successfully
        """
        if self.backend == "local":
            return self._delete_local(storage_path)
        else:
            return self._delete_cloud(storage_path)

    def file_exists(self, storage_path):
        """Check if a file exists in storage."""
        if self.backend == "local":
            full_path = os.path.join(self.upload_dir, storage_path)
            return os.path.exists(full_path)
        else:
            return self._cloud_file_exists(storage_path)

    # -------------------------------------------------------------------------
    # LOCAL STORAGE METHODS (Development)
    # -------------------------------------------------------------------------

    def _upload_local(self, file, storage_path):
        """Save file to local filesystem."""
        full_path = os.path.join(self.upload_dir, storage_path)

        # Create directories if they don't exist
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        # Save the file
        file.save(full_path)

        return {
            "storage_path": storage_path,
            "file_url": f"/api/files/{storage_path}",
            "size_bytes": os.path.getsize(full_path),
        }

    def _get_local_path(self, storage_path):
        """Get full local path for a stored file."""
        full_path = os.path.join(self.upload_dir, storage_path)
        if os.path.exists(full_path):
            return full_path
        return None

    def _delete_local(self, storage_path):
        """Delete file from local filesystem."""
        full_path = os.path.join(self.upload_dir, storage_path)
        try:
            if os.path.exists(full_path):
                os.remove(full_path)
                # Clean up empty parent directories
                parent = os.path.dirname(full_path)
                while parent != self.upload_dir:
                    if not os.listdir(parent):
                        os.rmdir(parent)
                        parent = os.path.dirname(parent)
                    else:
                        break
            return True
        except Exception as e:
            print(f"Error deleting file: {e}")
            return False

    # -------------------------------------------------------------------------
    # CLOUD STORAGE METHODS (Production)
    # -------------------------------------------------------------------------
    # These are placeholder implementations. Replace with actual cloud SDK calls.

    def _upload_cloud(self, file, storage_path):
        """
        Upload file to cloud object storage.

        Example with Firebase Storage:
            bucket = storage.bucket()
            blob = bucket.blob(storage_path)
            blob.upload_from_file(file)
            blob.make_public()  # or generate signed URL
            return {"storage_path": storage_path, "file_url": blob.public_url}

        Example with AWS S3:
            s3_client = boto3.client('s3')
            s3_client.upload_fileobj(file, BUCKET_NAME, storage_path)
            url = s3_client.generate_presigned_url('get_object',
                Params={'Bucket': BUCKET_NAME, 'Key': storage_path},
                ExpiresIn=3600)
            return {"storage_path": storage_path, "file_url": url}

        Example with Supabase Storage:
            supabase.storage.from_('assignments').upload(storage_path, file)
            url = supabase.storage.from_('assignments').get_public_url(storage_path)
            return {"storage_path": storage_path, "file_url": url}
        """
        # Fallback to local for now
        print("⚠️  Cloud storage not configured. Falling back to local storage.")
        return self._upload_local(file, storage_path)

    def _get_cloud_url(self, storage_path):
        """
        Generate a signed/presigned URL for file download.

        Cloud Concept: SIGNED URLs provide temporary, secure access to private
        files without making them publicly accessible. They expire after a set time.

        Example with Firebase:
            blob = bucket.blob(storage_path)
            url = blob.generate_signed_url(expiration=timedelta(hours=1))
            return url

        Example with AWS S3:
            url = s3_client.generate_presigned_url('get_object',
                Params={'Bucket': BUCKET_NAME, 'Key': storage_path},
                ExpiresIn=3600)
            return url
        """
        return self._get_local_path(storage_path)

    def _delete_cloud(self, storage_path):
        """
        Delete file from cloud storage.

        Example with Firebase:
            blob = bucket.blob(storage_path)
            blob.delete()
        """
        return self._delete_local(storage_path)

    def _cloud_file_exists(self, storage_path):
        """Check if file exists in cloud storage."""
        return self.file_exists(storage_path)


# Singleton instance
storage_service = StorageService()
