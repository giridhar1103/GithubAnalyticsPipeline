from contextlib import contextmanager

import duckdb

from app.settings import get_settings


@contextmanager
def dashboard_connection():
    settings = get_settings()
    con = duckdb.connect(settings.dashboard_db_path, read_only=True)
    try:
        yield con
    finally:
        con.close()
