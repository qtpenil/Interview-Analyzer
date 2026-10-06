from app.core.config import settings


class TestSettings:
    def test_settings_are_loaded(self):
        assert settings.ALGORITHM == "HS256"
        assert settings.SECRET_KEY is not None
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES > 0

    def test_database_url_is_constructed(self):
        url = settings.DATABASE_URL
        assert url is not None
        assert isinstance(url, str)

    def test_token_config_has_required_keys(self):
        config = settings.TOKEN_CONFIG
        assert "access" in config
        assert "refresh" in config
        assert "verification" in config
        for token_type in ("access", "refresh", "verification"):
            assert "cookie_name" in config[token_type]
            assert "expiry" in config[token_type]

    def test_ffmpeg_paths(self):
        assert settings.FFMPEG_PATH is not None
        assert settings.FFPROBE_PATH is not None

    def test_storage_config(self):
        assert settings.STORAGE_DIR is not None

    def test_cors_origins_is_list(self):
        assert isinstance(settings.CORS_ORIGINS, list)
