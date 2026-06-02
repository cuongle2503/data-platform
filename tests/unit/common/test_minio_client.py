"""Unit tests for MinIO client wrapper."""

from unittest.mock import Mock, patch

import polars as pl
import pytest

from idp.common.minio_client import MinioClient


@pytest.fixture
def minio_client() -> MinioClient:
    """Create a MinioClient with mocked underlying client."""
    client = MinioClient(
        endpoint="localhost:9000",
        access_key="testkey",
        secret_key="testsecret",
        secure=False,
    )
    return client


def test_client_initialization():
    """Test MinIO client initializes with proper endpoint."""
    # Act
    client = MinioClient(
        endpoint="localhost:9000",
        access_key="key123",
        secret_key="secret123",
        secure=False,
    )

    # Assert
    assert client.bucket_name == "bronze"
    assert client.endpoint == "localhost:9000"


def test_client_initialization_with_custom_bucket():
    """Test MinIO client with custom bucket name."""
    # Act
    client = MinioClient(
        endpoint="localhost:9000",
        access_key="key",
        secret_key="secret",
        bucket_name="my-bucket",
    )

    # Assert
    assert client.bucket_name == "my-bucket"


def test_upload_dataframe(minio_client: MinioClient):
    """Test uploading a Polars DataFrame as Parquet to MinIO."""
    # Arrange
    df = pl.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})

    with (
        patch.object(minio_client.client, "put_object") as mock_put,
        patch.object(minio_client.client, "bucket_exists", return_value=True),
    ):
        # Act
        result = minio_client.upload_dataframe(df, "test/path/data.parquet")

    # Assert
    assert result == "bronze/test/path/data.parquet"
    mock_put.assert_called_once()
    # Verify kwargs contain bucket_name and object_name
    call_kwargs = mock_put.call_args.kwargs
    assert call_kwargs["bucket_name"] == "bronze"
    assert call_kwargs["object_name"] == "test/path/data.parquet"


def test_upload_dataframe_creates_bucket_if_missing(minio_client: MinioClient):
    """Test bucket is created if it doesn't exist."""
    # Arrange
    df = pl.DataFrame({"x": [1]})

    with (
        patch.object(minio_client.client, "put_object"),
        patch.object(minio_client.client, "bucket_exists", return_value=False) as mock_exists,
        patch.object(minio_client.client, "make_bucket") as mock_make,
    ):
        # Act
        minio_client.upload_dataframe(df, "test/file.parquet")

    # Assert
    mock_exists.assert_called_once_with("bronze")
    mock_make.assert_called_once_with("bronze")


def test_upload_dataframe_uses_custom_bucket():
    """Test that custom bucket name is used."""
    # Arrange
    client = MinioClient(
        endpoint="localhost:9000",
        access_key="key",
        secret_key="secret",
        bucket_name="custom-bucket",
    )
    df = pl.DataFrame({"x": [1]})

    with (
        patch.object(client.client, "put_object"),
        patch.object(client.client, "bucket_exists", return_value=True) as mock_exists,
    ):
        # Act
        client.upload_dataframe(df, "test/file.parquet")

    # Assert
    mock_exists.assert_called_once_with("custom-bucket")


def test_check_exists_returns_true(minio_client: MinioClient):
    """Test check_exists returns True when object exists."""
    # Arrange
    with patch.object(minio_client.client, "stat_object") as mock_stat:
        mock_stat.return_value = Mock()
        # Act
        result = minio_client.check_exists("test/file.parquet")

    # Assert
    assert result is True
    mock_stat.assert_called_once_with("bronze", "test/file.parquet")


def test_check_exists_returns_false_when_not_found(minio_client: MinioClient):
    """Test check_exists returns False when object does not exist."""
    # Arrange
    from minio.error import S3Error

    # We need a proper exception for side_effect
    class MockS3Error(S3Error):
        def __init__(self, code):
            self.code = code
            super(Exception, self).__init__("Mock error")

    with patch.object(minio_client.client, "stat_object", side_effect=MockS3Error("NoSuchKey")):
        # Act
        result = minio_client.check_exists("missing/file.parquet")

    # Assert
    assert result is False


def test_list_objects(minio_client: MinioClient):
    """Test listing objects with a prefix."""
    # Arrange
    mock_obj = Mock()
    mock_obj.object_name = "test/file1.parquet"
    mock_obj2 = Mock()
    mock_obj2.object_name = "test/file2.parquet"

    with (
        patch.object(minio_client.client, "bucket_exists", return_value=True),
        patch.object(minio_client.client, "list_objects", return_value=[mock_obj, mock_obj2]),
    ):
        # Act
        result = minio_client.list_objects("test/")

    # Assert
    assert result == ["test/file1.parquet", "test/file2.parquet"]


def test_list_objects_empty(minio_client: MinioClient):
    """Test listing objects with no results."""
    # Arrange
    with (
        patch.object(minio_client.client, "bucket_exists", return_value=True),
        patch.object(minio_client.client, "list_objects", return_value=[]),
    ):
        # Act
        result = minio_client.list_objects("nonexistent/")

    # Assert
    assert result == []


def test_read_dataframe_success(minio_client: MinioClient):
    """Test reading a Parquet file from MinIO."""
    # Arrange
    import io

    buffer = io.BytesIO()
    df = pl.DataFrame({"a": [1, 2, 3]})
    df.write_parquet(buffer)
    buffer.seek(0)

    mock_response = Mock()
    mock_response.read.return_value = buffer.getvalue()

    with patch.object(minio_client.client, "get_object", return_value=mock_response):
        # Act
        result_df = minio_client.read_dataframe("test_file.parquet")

    # Assert
    assert result_df.shape == (3, 1)
    assert result_df["a"].to_list() == [1, 2, 3]


def test_read_dataframe_failure(minio_client: MinioClient):
    """Test read_dataframe raises StorageError on failure."""
    # Arrange
    from idp.common.exceptions import StorageError

    with (
        patch.object(minio_client.client, "get_object", side_effect=Exception("S3 error")),
        pytest.raises(StorageError, match="Failed to read test_file\\.parquet"),
    ):
        minio_client.read_dataframe("test_file.parquet")
