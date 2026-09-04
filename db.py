"""
Database connection and utilities for WellnessBot.
Uses psycopg2 with Neon PostgreSQL and connection pooling.
"""

import os
import psycopg2
from psycopg2 import pool, extras

# ── Connection pool ───────────────────────────────────
_pool = None


def get_pool():
    """Get or create the connection pool (lazy init)."""
    global _pool
    if _pool is None:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise RuntimeError("DATABASE_URL environment variable is not set")
        _pool = pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=database_url,
        )
    return _pool


def get_conn():
    """Get a connection from the pool."""
    return get_pool().getconn()


def put_conn(conn):
    """Return a connection to the pool."""
    get_pool().putconn(conn)


def query(sql, params=None, fetchone=False, fetchall=False):
    """
    Execute a SQL query and optionally fetch results.
    Returns rows as dicts when fetching.
    """
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            if fetchone:
                result = cur.fetchone()
            elif fetchall:
                result = cur.fetchall()
            else:
                result = None
            conn.commit()
            return result
    except Exception:
        conn.rollback()
        raise
    finally:
        put_conn(conn)


def execute(sql, params=None):
    """Execute a SQL statement (INSERT, UPDATE, DELETE) without returning rows."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        put_conn(conn)


def init_db():
    """Initialize the database schema from schema.sql."""
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path, "r") as f:
        schema_sql = f.read()

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(schema_sql)
            conn.commit()
        print("[DB] Schema initialized successfully")
    except Exception as e:
        conn.rollback()
        print(f"[DB] Schema initialization error: {e}")
        raise
    finally:
        put_conn(conn)


def close_pool():
    """Close all connections in the pool."""
    global _pool
    if _pool is not None:
        _pool.closeall()
        _pool = None
