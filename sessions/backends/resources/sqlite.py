__all__ = "SQLiteConnection",

from sqlite3 import connect as sqlite_connect, Row
from threading import Lock, current_thread
from time import time

from .abstract import Resource

class SQLiteConnection(Resource):
    __slots__ = "db_name", "conn", "cursor", "_thread_id", "_last_use", "id"
    lock = Lock()
    ID = 0

    def __init__(self, db_name):
        SQLiteConnection.ID += 1
        self.id = SQLiteConnection.ID
        self.db_name = db_name
        self.conn = sqlite_connect(db_name)
        self.conn.row_factory = Row
        self.cursor = self.conn.cursor()
        self._thread_id = self.thread.ident
        self._last_use = time()

    def __enter__(self):
        return self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.conn.rollback()
        else:
            self.conn.commit()


    def close(self):
        self.conn.close()

    @property
    def thread(self):
        return current_thread()

    def commit(self):
        self.conn.commit()

    def create_table(self, name, columns, commit=False):
        with self:
            self.cursor.execute(f"CREATE TABLE IF NOT EXISTS {name} ({columns})")
        if commit:
            self.conn.commit()
        self._last_use = time()

    def delete(self, sql, params, commit=False):
        validation = sql.upper()
        assert "DELETE" in validation, "Only DELETE statements are allowed."

        with self:
            self.cursor.execute(sql, params)
        if commit:
            self.conn.commit()
        self._last_use = time()

    def insert(self, sql, params, commit=False):
        validation = sql.upper()
        assert "INSERT" in validation or "UPDATE" in validation or "REPLACE" in validation, "Only INSERT, UPDATE, and REPLACE statements are allowed."

        with self:
            self.cursor.execute(sql, params)
        if commit:
            self.conn.commit()
        self._last_use = time()

    def select(self, sql, params, commit=False):
        validation = sql.upper()
        assert "SELECT" in validation, "Only SELECT statements are allowed."

        with self:
            self.cursor.execute(sql, params)
            results =  self.cursor.fetchall()
        self._last_use = time()
        if commit:
            self.conn.commit()
        return results

    def keys(self, table):
        return self.select(f"SELECT key FROM {table}")