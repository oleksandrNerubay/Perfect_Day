import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

_conn = None


def get_conn():
    global _conn
    if _conn is None or _conn.closed:
        _conn = psycopg2.connect(
            os.getenv("PG_DSN", "postgresql://perfectday:perfectday@localhost:5432/perfectday"),
            cursor_factory=psycopg2.extras.RealDictCursor,
        )
        _conn.autocommit = False
    return _conn


def _apply_schema():
    conn = get_conn()
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path) as f:
        sql = f.read()
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()


_apply_schema()
