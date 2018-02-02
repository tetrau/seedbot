import os
import importlib.util
import sched
import time
import threading
import logging
from .core.config import get_config, load_config
from .core.env import env
from .core import Protocol, Schedule
from .utils.database import create_bare_database
from .core.monitor import record_torrents
from .utils.torrent import add_torrent

logger = logging.getLogger('seedbot')
logger.addHandler(logging.NullHandler())


class Seedbot:
    def __init__(self, config_path):
        load_config(config_path)
        self.config = get_config()
        self.plugin_module = []
        self.load_plugin_module()
        self.protocols = [Protocol(protocol) for protocol in self.config['protocols']]
        if not os.path.isfile(self.config['db_path']):
            create_bare_database(self.config['db_path'])
        self.sample_schedule = Schedule(self.config['sample_schedule'])
        self.protocol_scheduler = sched.scheduler(time.time, time.sleep)
        self.monitor_scheduler = sched.scheduler(time.time, time.sleep)
        self.main_thread = threading.Thread(target=self.protocols_run)
        self.monitor_thread = threading.Thread(target=self.monitor_run)

    def run(self):
        self.main_thread.start()
        self.monitor_thread.start()

    def protocols_run(self):
        def scheduled_run(scheduler, protocol):
            env['protocol_name'] = protocol.name
            torrents = protocol.run()
            for torrent in torrents:
                torrent = torrent['torrent']() if callable(torrent['torrent']) else torrent['torrent']
                add_torrent(torrent)
            scheduler.enterabs(next(protocol.schedule).timestamp(), 1, scheduled_run, argument=(scheduler, protocol))

        for protocol in self.protocols:
            self.protocol_scheduler.enterabs(next(protocol.schedule).timestamp(), 1, scheduled_run,
                                             argument=(self.protocol_scheduler, protocol))
        self.protocol_scheduler.run()

    def monitor_run(self):
        def scheduled_run(scheduler, func):
            func()
            scheduler.enterabs(next(self.sample_schedule).timestamp() + 43, 1, scheduled_run,
                               argument=(scheduler, func))

        self.monitor_scheduler.enterabs(next(self.sample_schedule).timestamp() + 43, 1, scheduled_run,
                                        argument=(self.monitor_scheduler, self.record))
        self.monitor_scheduler.run()

    def record(self):
        record_torrents()

    def load_plugin_module(self):
        self.plugin_module.clear()
        logger.debug('load plugin modules')
        plugin_dir = self.config['plugin_dir']
        plugin_files = filter(lambda x: not x.startswith('__'), os.listdir(plugin_dir))
        for f in plugin_files:
            filename = os.path.split(f)[-1]
            module_name = filename.replace('.py', '')
            # python 3.4+
            spec = importlib.util.spec_from_file_location(module_name, os.path.join(plugin_dir, f))
            self.plugin_module.append(importlib.util.module_from_spec(spec))
            spec.loader.exec_module(self.plugin_module[-1])
