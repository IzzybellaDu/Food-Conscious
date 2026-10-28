"""
Database access layer for Food Conscious.
Provides a clean, unified interface for PostgreSQL (production) and SQLite (local dev),
using standard psycopg2 and sqlite3 libraries without any third-party wrappers.
"""

import os
import sqlite3
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor


class Database:
    def __init__(self, url=None):
        self.url = url or os.getenv("DATABASE_URL")
        self.is_postgres = False
        self.pg_pool = None
        self.sqlite_path = "system.db"

        if self.url and (self.url.startswith("postgres://") or self.url.startswith("postgresql://")):
            self.is_postgres = True
            if self.url.startswith("postgres://"):
                self.url = self.url.replace("postgres://", "postgresql://", 1)
            # Standard thread-safe connection pool for PostgreSQL
            self.pg_pool = pool.ThreadedConnectionPool(minconn=1, maxconn=10, dsn=self.url)

    def _get_connection(self):
        """Get an active connection from the pool, re-creating it if closed."""
        conn = self.pg_pool.getconn()
        if conn.closed:
            # If the connection closed (e.g. server idle timeout), replace it
            self.pg_pool.putconn(conn, close=True)
            conn = self.pg_pool.getconn()
        return conn

    def execute(self, sql, *args):
        """
        Execute a SQL query with parameter substitution.
        Accepts parameters as positional arguments (*args) or a single tuple/list.
        Returns:
            - list[dict] for SELECT queries
            - inserted ID (int) for INSERT queries
            - affected row count (int) for UPDATE/DELETE queries
        """
        # Normalize args if passed as a single tuple or list
        if len(args) == 1 and isinstance(args[0], (list, tuple)):
            args = tuple(args[0])
        elif len(args) > 0:
            args = tuple(args)
        else:
            args = None

        if self.is_postgres:
            return self._execute_postgres(sql, args)
        else:
            return self._execute_sqlite(sql, args)

    def _execute_postgres(self, sql, args):
        conn = self._get_connection()
        try:
            # Replace ? with %s for Postgres syntax
            pg_sql = sql.replace("?", "%s")
            stripped = pg_sql.strip().upper()
            is_select = stripped.startswith("SELECT")
            is_insert = stripped.startswith("INSERT")

            # Auto-append RETURNING clause for INSERT if not present
            if is_insert and "RETURNING" not in stripped:
                tokens = pg_sql.split()
                if len(tokens) >= 3 and tokens[0].upper() == "INSERT" and tokens[1].upper() == "INTO":
                    table = tokens[2].split("(")[0].strip("\"'").lower()
                    pk_map = {
                        "recipe": "recipeid",
                        "users": "userid",
                        "fooddiary": "logid",
                        "ingredients": "ingredientid"
                    }
                    pk = pk_map.get(table)
                    if pk:
                        pg_sql = f"{pg_sql.rstrip().rstrip(';')} RETURNING {pk};"

            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if args:
                    cur.execute(pg_sql, args)
                else:
                    cur.execute(pg_sql)

                if is_select or "RETURNING" in pg_sql.upper():
                    rows = cur.fetchall()
                    conn.commit()
                    res = [dict(r) for r in rows]
                    # If this was an INSERT with RETURNING, return the single ID
                    if is_insert and res and len(res) == 1 and len(res[0]) == 1:
                        return list(res[0].values())[0]
                    return res
                else:
                    conn.commit()
                    return cur.rowcount
        except Exception:
            conn.rollback()
            raise
        finally:
            self.pg_pool.putconn(conn)

    def _execute_sqlite(self, sql, args):
        conn = sqlite3.connect(self.sqlite_path)
        conn.row_factory = sqlite3.Row
        try:
            cur = conn.cursor()
            if args:
                cur.execute(sql, args)
            else:
                cur.execute(sql)

            stripped = sql.strip().upper()
            if stripped.startswith("SELECT"):
                rows = cur.fetchall()
                conn.commit()
                return [dict(r) for r in rows]
            elif stripped.startswith("INSERT"):
                last_id = cur.lastrowid
                conn.commit()
                return last_id
            else:
                affected = cur.rowcount
                conn.commit()
                return affected
        finally:
            conn.close()
