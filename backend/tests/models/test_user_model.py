from app.modules.user.UserModel import User


class TestUserModel:
    def test_model_has_required_fields(self):
        required = {"id", "email", "password_hash", "name", "created_at", "updated_at"}
        columns = {c.name for c in User.__table__.columns}
        for field in required:
            assert field in columns, f"Missing field: {field}"

    def test_model_table_name(self):
        assert User.__tablename__ == "users"

    def test_model_relationships(self):
        relationships = User.__mapper__.relationships
        assert "interviews" in relationships

    def test_email_is_unique_indexed(self):
        email_col = User.__table__.columns["email"]
        assert email_col.unique
        assert email_col.index
