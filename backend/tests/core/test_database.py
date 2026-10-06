from app.core.database import Base, SessionLocal, engine, get_db


class TestDatabaseSetup:
    def test_engine_exists(self):
        assert engine is not None

    def test_base_is_declarative(self):
        assert hasattr(Base, "metadata")
        assert hasattr(Base, "registry")

    def test_session_local_is_callable(self):
        session = SessionLocal()
        assert session is not None
        session.close()

    def test_get_db_is_generator(self):
        gen = get_db()
        session = next(gen)
        assert session is not None
        try:
            next(gen)
        except StopIteration:
            pass
        session.close()
