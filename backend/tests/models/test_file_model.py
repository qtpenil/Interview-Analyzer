from app.modules.files.file import File
from app.modules.files.schema import FileType


class TestFileType:
    def test_all_types_present(self):
        expected = {"SUMMARY_PDF", "AUDIO", "VIDEO", "TRANSCRIPT"}
        actual = {t.value for t in FileType}
        assert actual == expected


class TestFileModel:
    def test_model_has_required_fields(self):
        required = {"id", "interview_id", "file_type", "storage_provider", "storage_path", "file_size", "created_at"}
        columns = {c.name for c in File.__table__.columns}
        for field in required:
            assert field in columns, f"Missing field: {field}"

    def test_model_table_name(self):
        assert File.__tablename__ == "files"
