import sqlite3
from loguru import logger


class DB:
    """数据库操作类"""

    def __init__(self):
        self._conn = sqlite3.connect('./db.db', check_same_thread=False)
        self._cursor = self._conn.cursor()

    def add(self, lock, sql, param):
        try:
            lock.acquire()

            self._conn.execute(sql, param)
            self._conn.commit()
            return True

        except Exception as e:
            logger.error(f'DB err: {e}')
            return

        finally:
            lock.release()

    def select_exist(self, sql, lock=None):
        try:
            if lock:
                lock.acquire()

            self._cursor.execute(sql)
            result = self._cursor.fetchone()
        except Exception as e:
            logger.error(f'DB err: {e}')
            return
        finally:
            if lock:
                lock.release()

        if result:
            return True

    def select_many(self, sql, lock=None):
        try:
            if lock:
                lock.acquire()

            self._cursor.execute(sql)
            result = self._cursor.fetchall()
        except Exception as e:
            logger.error(f'DB err: {e}')
            return
        finally:
            if lock:
                lock.release()

        return result

    def delete(self, sql):
        try:
            self._cursor.execute(sql)
            self._conn.commit()
            return True

        except Exception as e:
            logger.error(f'DB err: {e}')
            return

    def web_add(self, sql, param):
        try:
            self._conn.execute(sql, param)
            self._conn.commit()
            return True

        except Exception as e:
            logger.error(f'DB err: {e}')
            return
