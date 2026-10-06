import os
from io import BytesIO

import pytest

from app.shared.storage.service import (
    StorageServiceError,
    delete_file,
    download_file,
    download_fileobj,
    generate_presigned_url,
    read_file,
    save_file,
    upload_file_to_s3,
)


class TestLocalStorageService:
    def test_save_and_read_file_success(self, tmp_path, monkeypatch):
        monkeypatch.setattr("app.shared.storage.service.STORAGE_DIR", str(tmp_path))
        file_content = b"%PDF-1.4 test report content"
        saved_path = save_file(BytesIO(file_content), "reports/test_report.pdf")

        assert os.path.exists(saved_path)
        read_content = read_file(saved_path)
        assert read_content == file_content

    def test_upload_file_to_s3_alias(self, tmp_path, monkeypatch):
        monkeypatch.setattr("app.shared.storage.service.STORAGE_DIR", str(tmp_path))
        saved_path = upload_file_to_s3(BytesIO(b"alias test"), "reports/alias.pdf", "application/pdf")

        assert os.path.exists(saved_path)
        assert download_fileobj(saved_path) == b"alias test"

    def test_read_file_not_found(self, tmp_path, monkeypatch):
        monkeypatch.setattr("app.shared.storage.service.STORAGE_DIR", str(tmp_path))
        with pytest.raises(StorageServiceError):
            read_file("nonexistent/file.pdf")

    def test_download_file_copy(self, tmp_path, monkeypatch):
        monkeypatch.setattr("app.shared.storage.service.STORAGE_DIR", str(tmp_path))
        source_path = save_file(BytesIO(b"content to copy"), "reports/source.pdf")

        destination_path = str(tmp_path / "copied.pdf")
        result = download_file(source_path, destination_path)

        assert result == destination_path
        assert os.path.exists(destination_path)
        with open(destination_path, "rb") as f:
            assert f.read() == b"content to copy"

    def test_download_file_not_found(self, tmp_path, monkeypatch):
        monkeypatch.setattr("app.shared.storage.service.STORAGE_DIR", str(tmp_path))
        with pytest.raises(StorageServiceError):
            download_file("nonexistent.pdf", str(tmp_path / "dest.pdf"))

    def test_delete_file_success(self, tmp_path, monkeypatch):
        monkeypatch.setattr("app.shared.storage.service.STORAGE_DIR", str(tmp_path))
        saved_path = save_file(BytesIO(b"to delete"), "reports/to_delete.pdf")
        assert os.path.exists(saved_path)

        result = delete_file(saved_path)
        assert result is True
        assert not os.path.exists(saved_path)

    def test_delete_file_nonexistent_returns_true(self, tmp_path, monkeypatch):
        monkeypatch.setattr("app.shared.storage.service.STORAGE_DIR", str(tmp_path))
        result = delete_file("already_deleted.pdf")
        assert result is True

    def test_generate_presigned_url_returns_path(self, tmp_path, monkeypatch):
        monkeypatch.setattr("app.shared.storage.service.STORAGE_DIR", str(tmp_path))
        url = generate_presigned_url("reports/sample.pdf")
        assert "sample.pdf" in url
