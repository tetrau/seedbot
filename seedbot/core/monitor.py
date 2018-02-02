import sqlite3
from .config import get_config
import time
import transmissionrpc
import logging

logger = logging.getLogger('seedbot')
logger.addHandler(logging.NullHandler())


def record_torrents():
    _start_time = time.time()
    config = get_config()
    client = transmissionrpc.Client(address=config.get('transmission_address'),
                                    port=config.get('transmission_port'),
                                    user=config.get('transmission_username'),
                                    password=config.get('transmission_password'))
    db_path = config['db_path']
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        timestamp = time.time()
        torrents = client.get_torrents()
        records = [(timestamp, t.downloadedEver, t.uploadedEver, t.hashString) for t in torrents]
        torrents = [(t.name, t.totalSize, t.addedDate, t.hashString) for t in torrents]
        cursor.executemany("""
        UPDATE torrents SET torrent_name = ?, torrent_size = ?, torrent_added_time = ?
        WHERE torrent_id = (SELECT torrent_id FROM torrents
                            WHERE torrent_hash = ?
                            ORDER BY torrent_id DESC
                            LIMIT 1)
        """, torrents)
        cursor.executemany("""
        INSERT INTO records (timestamp, downloaded, uploaded, torrent_id)
        SELECT ?, ?, ?, torrent_id FROM torrents
        WHERE torrent_hash = ?
        ORDER BY torrent_added_time DESC
        LIMIT 1
        """, records)
    logger.debug('record {} torrents in {:0.3f} secend'.format(len(torrents), time.time() - _start_time))
