from unittest.mock import MagicMock
from scripts.upload_to_minio import upload_file_to_minio


def test_upload_calls_minio(tmp_path):
    fake_client = MagicMock()

    local_file = tmp_path / "file.csv"
    local_file.write_text("data")

    upload_file_to_minio(
        local_path=str(local_file),
        object_name="file.csv",
        bucket="test-bucket",
        client=fake_client
    )

    fake_client.fput_object.assert_called_once()