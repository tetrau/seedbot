import sqlite3


def create_bare_database(db_path):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('CREATE TABLE torrents ('
                       'torrent_id INTEGER PRIMARY KEY ASC, '
                       'torrent_name TEXT, '
                       'torrent_hash TEXT, '
                       'torrent_size INTEGER,'
                       'torrent_added_time REAL,'
                       'torrent_added_by TEXT'
                       ')')
        cursor.execute('CREATE TABLE records ('
                       'timestamp REAL, '
                       'torrent_id INTEGER, '
                       'uploaded INTEGER, '
                       'downloaded INTEGER, '
                       'FOREIGN KEY(torrent_id) REFERENCES torrents(torrent_id) '
                       ')')
