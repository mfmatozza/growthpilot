from app.core.config import normalize_database_url


def test_normalize_database_url_rewrites_postgres_scheme():
    assert normalize_database_url("postgres://u:p@host:5432/db") == "postgresql+psycopg://u:p@host:5432/db"


def test_normalize_database_url_rewrites_postgresql_scheme():
    assert normalize_database_url("postgresql://u:p@host:5432/db") == "postgresql+psycopg://u:p@host:5432/db"


def test_normalize_database_url_leaves_already_correct_scheme_alone():
    url = "postgresql+psycopg://u:p@host:5432/db"
    assert normalize_database_url(url) == url


def test_normalize_database_url_leaves_sqlite_alone():
    assert normalize_database_url("sqlite:///./test.db") == "sqlite:///./test.db"
