from .exceptions import *
from .plugin import *
import re
import datetime
import itertools
import time


class Schedule:
    def __init__(self, crontab: str):
        minute, hour, d, m, w = re.split(' +', crontab.strip())
        now = datetime.datetime.now()
        self.year = itertools.count(now.year)
        self.month = self.parse_crontab(m, 1, 12)
        self.weekday = self.parse_crontab(w, 1, 7)
        self.day = self.parse_crontab(d, 1, 31)
        self.hour = self.parse_crontab(hour, 0, 23)
        self.minute = self.parse_crontab(minute, 0, 59)
        self.raw_datetime_iter = ((y, m, d, h, mi)
                                  for y in self.year
                                  for m in self.month
                                  for d in self.day
                                  for h in self.hour
                                  for mi in self.minute)
        self.datetime_iter = filter(lambda x: x.timestamp() >= time.time(),
                                    filter(lambda x: x.isoweekday() in self.weekday,
                                           filter(lambda x: x is not None,
                                                  map(self.raw_datetime_2_datetime, self.raw_datetime_iter))))

    def parse_crontab(self, c, minimum, maximum):
        if ',' in c:
            return tuple(int(i) for i in c.split(','))
        if '/' in c:
            step = int(re.findall('/([0-9]+)', c)[0])
        else:
            step = 1
        if '-' in c:
            number_range = tuple(int(i) for i in re.findall('([0-9]+)\-([0-9]+)', c)[0])
            return tuple(range(number_range[0], number_range[1] + 1, step))
        elif '*' in c:
            return tuple(range(minimum, maximum + 1, step))
        else:
            return (int(c),)

    def raw_datetime_2_datetime(self, raw_datetime):
        try:
            return datetime.datetime(**{k: v for k, v in zip('year month day hour minute'.split(), raw_datetime)})
        except ValueError:
            return None

    def __iter__(self):
        return self

    def __next__(self):
        return next(self.datetime_iter)


class Protocol:
    def __init__(self, protocol_config):
        self.name = protocol_config['name']
        self.schedule = Schedule(protocol_config['schedule'])
        self.prepares = []
        for p in protocol_config['prepare']:
            plugin = SeedbotPrepare._search(p['plugin'])
            args = p['args']
            kwargs = p['kwargs']
            self.prepares.append(dict(plugin=plugin, args=args, kwargs=kwargs))
        self.inputs = []
        for p in protocol_config['input']:
            plugin = SeedbotInput._search(p['plugin'])
            args = p['args']
            kwargs = p['kwargs']
            self.inputs.append(dict(plugin=plugin, args=args, kwargs=kwargs))
        self.pipelines = []
        for p in protocol_config['pipeline']:
            plugin = SeedbotPipeline._search(p['plugin'])
            args = p['args']
            kwargs = p['kwargs']
            self.pipelines.append(dict(plugin=plugin, args=args, kwargs=kwargs))

    def run(self):
        try:
            for p in self.prepares:
                p['plugin'](*p['args'], **p['kwargs']).prepare()
        except NotReady:
            return
        torrents = []
        for p in self.inputs:
            torrents.extend(p['plugin'](*p['args'], **p['kwargs']).input())
        for p in self.pipelines:
            torrents = p['plugin'](*p['args'], **p['kwargs']).pipeline(torrents)
        return torrents
