"""MinIO client wrapper for IDP data storage."""

import io
import logging

import polars as pl
from minio import Minio
from minio.error import S3Error

from idp.common.exceptions import StorageError

logger = logging.getLogger(__name__)


class MinioClient:
    """Wrapper around minio-py for common IDP storage operations."""

    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        secure: bool = False,
        bucket_name: str = "bronze",
    ) -> None:
        """Initialize MinIO client.

        Args:
            endpoint: MinIO server endpoint (e.g. 'localhost:9000').
            access_key: Access key / root user.
            secret_key: Secret key / root password.
            secure: Whether to use HTTPS.
            bucket_name: Default bucket name to use.
        """
        self.endpoint = endpoint
        self.bucket_name = bucket_name

        try:
            self.client = Minio(
                endpoint=endpoint,
                access_key=access_key,
                secret_key=secret_key,
                secure=secure,
            )
            logger.debug(f"Initialized MinIO client for {endpoint}")
        except Exception as e:
            raise StorageError(f"Failed to initialize MinIO client: {str(e)}") from e

    def _ensure_bucket_exists(self) -> None:
        """Create bucket if it doesn't exist."""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Created bucket '{self.bucket_name}'")
        except Exception as e:
            raise StorageError(f"Error ensuring bucket '{self.bucket_name}': {str(e)}") from e

    def upload_dataframe(self, df: pl.DataFrame, object_name: str) -> str:
        """Upload a Polars DataFrame as Parquet to MinIO.

        Args:
            df: Polars DataFrame to upload.
            object_name: Destination path in the bucket.

        Returns:
            The full path (bucket/object_name).

        Raises:
            StorageError: If upload fails.
        """
        self._ensure_bucket_exists()

        try:
            # Write dataframe to in-memory buffer as parquet
            buffer = io.BytesIO()
            df.write_parquet(buffer)
            buffer.seek(0)
            file_size = buffer.getbuffer().nbytes

            # Upload buffer to MinIO
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=buffer,
                length=file_size,
                content_type="application/vnd.apache.parquet",
            )

            logger.info(f"Uploaded {file_size} bytes to {self.bucket_name}/{object_name}")
            return f"{self.bucket_name}/{object_name}"

        except Exception as e:
            logger.error(f"Failed to upload DataFrame to {object_name}: {str(e)}")
            raise StorageError(f"Upload failed: {str(e)}") from e

    def check_exists(self, object_name: str) -> bool:
        """Check if an object exists in the bucket.

        Args:
            object_name: Path to the object.

        Returns:
            True if exists, False otherwise.
        """
        try:
            self.client.stat_object(self.bucket_name, object_name)
            return True
        except S3Error as e:
            if e.code in ("NoSuchKey", "Not found"):
                return False
            # Re-raise unexpected S3 errors
            raise StorageError(f"Error checking if {object_name} exists: {str(e)}") from e
        except Exception as e:
            raise StorageError(f"Unexpected error checking {object_name}: {str(e)}") from e

    def list_objects(self, prefix: str = "") -> list[str]:
        """List objects in the bucket with a given prefix.

        Args:
            prefix: Path prefix to filter objects.

        Returns:
            List of object names.
        """
        try:
            if not self.client.bucket_exists(self.bucket_name):
                return []

            objects = self.client.list_objects(self.bucket_name, prefix=prefix, recursive=True)
            return [obj.object_name for obj in objects]

        except Exception as e:
            raise StorageError(f"Failed to list objects with prefix '{prefix}': {str(e)}") from e
