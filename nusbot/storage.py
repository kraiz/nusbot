import errno
import os
import json
import sqlite3


def ensure_directory_exists(path):
    if len(path) > 0:
        try:
            os.makedirs(path)
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise


class SqliteStorage(object):

    def __init__(self, file_path):
        file_path = os.path.expanduser(file_path)
        ensure_directory_exists(os.path.dirname(file_path))
        self.db = sqlite3.connect(file_path, isolation_level=None,
                                  detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        self.setup_db()

    def setup_db(self):
        self.db.execute('CREATE TABLE IF NOT EXISTS filelists (cid TEXT PRIMARY KEY, timestamp timestamp, data TEXT)')
        self.db.execute('CREATE TABLE IF NOT EXISTS changes (cid TEXT, timestamp timestamp, diff TEXT)')

    def save_filelist(self, cid, timestamp, data):
        self.db.execute(
            'INSERT OR REPLACE INTO filelists(cid, timestamp, data) VALUES (?, ?, ?)',
            (cid, timestamp, data)
        )

    def get_filelist(self, cid):
        row = self.db.execute(
            'SELECT data FROM filelists WHERE cid = ?',
            (cid,)
        ).fetchone()
        return None if row is None else row[0]

    def save_change(self, cid, timestamp, diff):
        self.db.execute(
            'INSERT INTO changes(cid, timestamp, diff) VALUES (?, ?, ?)',
            (cid, timestamp, json.dumps(diff))
        )

    def get_changes(self, since):
        result = self.db.execute('SELECT cid, timestamp, diff FROM changes WHERE timestamp > ?', (since.isoformat(), ))
        if result is not None:
            for row in result:
                yield row[0], row[1], json.loads(row[2])

