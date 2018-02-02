import sqlite3
import transmissionrpc
from ..core.config import config
from ..core.env import env
import base64
import logging
import time

logger = logging.getLogger('seedbot')
logger.addHandler(logging.NullHandler())


class Torrent:
    def __init__(self, db_path, torrent_id):
        self.db_path = db_path
        self.torrent_id = torrent_id
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            self.torrent_hash, \
            self.torrent_name, \
            self.torrent_size, \
            self.torrent_added_time, \
            self.torrent_added_by = \
                cursor.execute('SELECT torrent_hash, torrent_name, '
                               'torrent_size, torrent_added_time, torrent_added_by '
                               'FROM torrents WHERE torrent_id=?', (self.torrent_id,)).fetchone()
        self.uploaded, self.downloaded, self.timestamp = None, None, None
        self.seek(0)

    def seek(self, timepoint):
        abs_timepoint = timepoint if timepoint > 0 else timepoint + time.time()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            self.uploaded, self.downloaded, self.timestamp = cursor.execute(
                'SELECT r.uploaded, r.downloaded r.timestamp '
                'FROM records AS r JOIN torrents AS t '
                'ON r.torrent_id = t.torrent_id '
                'WHERE t.torrent_id = ? '
                'ORDER BY ABS(r.timestamp - ?) ASC '
                'LIMIT 1', (self.torrent_id, abs_timepoint)).fetchone()


def add_torrent(torrent_bytes):
    protocol_name = env['protocol_name']
    client = transmissionrpc.Client(address=config.get('transmission_address'),
                                    port=config.get('transmission_port'),
                                    user=config.get('transmission_username'),
                                    password=config.get('transmission_password'))
    active_torrent_hash = set(x.hashString for x in client.get_torrents())
    t = client.add_torrent(base64.b64encode(torrent_bytes).decode())
    if t.hashString not in active_torrent_hash:
        with sqlite3.connect(config.get('db_path')) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO torrents '
                           '(torrent_hash, '
                           'torrent_added_by) '
                           'VALUES (?,?)', (t.hashString, protocol_name))


def get_torrents():
    protocol_name = env['protocol_name']
    db_path = config.get('db_path')
    client = transmissionrpc.Client(address=config.get('transmission_address'),
                                    port=config.get('transmission_port'),
                                    user=config.get('transmission_username'),
                                    password=config.get('transmission_password'))
    active_torrent_hash = set(x.hashString for x in client.get_torrents())
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        torrents = cursor.execute(
            """
            SELECT torrent_id, torrent_hash FROM torrents
            WHERE torrent_added_by = ?
            """, (protocol_name,)).fetchall()
        return [Torrent(db_path, t[0]) for t in torrents if t[1] in active_torrent_hash]


def get_global_torrents():
    db_path = config.get('db_path')
    client = transmissionrpc.Client(address=config.get('transmission_address'),
                                    port=config.get('transmission_port'),
                                    user=config.get('transmission_username'),
                                    password=config.get('transmission_password'))
    active_torrent_hash = set(x.hashString for x in client.get_torrents())
    torrents = []
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        for h in active_torrent_hash:
            t = cursor.execute("""
            SELECT torrent_id FROM torrents
            WHERE torrent_hash = ?
            ORDER BY torrent_added_time DESC
            LIMIT 1
            """, (h,)).fetchone()[0]
            torrents.append(Torrent(db_path, t))
    return torrents


def remove_torrent(torrent):
    client = transmissionrpc.Client(address=config.get('transmission_address'),
                                    port=config.get('transmission_port'),
                                    user=config.get('transmission_username'),
                                    password=config.get('transmission_password'))
    torrents = client.get_torrents()
    rm_torrent_ids = [t.id for t in torrents if t.hashString == torrent.torrent_hash]
    if rm_torrent_ids:
        client.remove_torrent(rm_torrent_ids, delete_data=True)
