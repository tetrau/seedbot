import json
import os
import hashlib
from .exceptions import BadConfig

config = {}


def config_normalize(raw_config):
    config = {}
    try:
        db_path = raw_config.get('db_path')
        plugin_dir = raw_config.get('plugin_dir')
        sample_schedule = raw_config.get('sample_schedule')
        protocols = raw_config.get('protocols')
    except KeyError:
        raise BadConfig('Missing critical fields (db_path/plugin_dir/sample_schedule/protocols)')
    config['db_path'] = os.path.abspath(db_path)
    config['plugin_dir'] = os.path.abspath(plugin_dir)
    config['sample_schedule'] = sample_schedule
    config['transmission_address'] = raw_config.get('transmission_address', '127.0.0.1')
    config['transmission_port'] = raw_config.get('transmission_port', 9091)
    config['transmission_username'] = raw_config.get('transmission_username', 'transmission')
    config['transmission_password'] = raw_config.get('transmission_password', 'transmission')
    config['protocols'] = []
    try:
        assert isinstance(protocols, list)
    except AssertionError:
        raise BadConfig('Wrong Type (protocols: list) get {} instead'.format(type(protocols)))
    try:
        assert protocols
    except AssertionError:
        raise BadConfig('No protocol')
    for protocol_idx, protocol in enumerate(protocols):
        try:
            assert isinstance(protocol, dict)
        except AssertionError:
            raise BadConfig('Wrong Type (protocol: dict) get {} instead'.format(type(protocol)))
        try:
            prepare = protocol['prepare']
            input = protocol['input']
            pipeline = protocol['pipeline']
            schedule = protocol['schedule']
        except KeyError:
            raise BadConfig('Missing critical fields in protocols[{}] (prepare/input/pipline/schedule)'
                            .format(protocol_idx))
        name = protocol.get('name', hashlib.md5(json.dumps(protocol, sort_keys=True).encode()).hexdigest())
        normalize_protocol = {'name': name,
                              'schedule': schedule,
                              'prepare': [],
                              'input': [],
                              'pipeline': []}
        for slot_name, slot in zip('prepare input pipeline'.split(), (prepare, input, pipeline)):
            if isinstance(slot, str):
                normalize_protocol[slot_name].append({'plugin': slot,
                                                      'args': [],
                                                      'kwargs': {}})
            elif isinstance(slot, dict):
                try:
                    plugin_name = slot['plugin']
                    args = slot.get('args', [])
                    kwargs = slot.get('kwargs', {})
                    normalize_protocol[slot_name].append({'plugin': plugin_name,
                                                          'args': args,
                                                          'kwargs': kwargs})
                except KeyError:
                    raise BadConfig('Missing critical fields in protocols[{}][{}] (plugin)'
                                    .format(protocol_idx, repr(slot_name)))
            elif isinstance(slot, list):
                for s_idx, s in enumerate(slot):
                    try:
                        plugin_name = s['plugin']
                        args = s.get('args', [])
                        kwargs = s.get('kwargs', {})
                        normalize_protocol[slot_name].append({'plugin': plugin_name,
                                                              'args': args,
                                                              'kwargs': kwargs})
                    except KeyError:
                        raise BadConfig('Missing critical fields in protocols[{}][{}][{}] (plugin)'
                                        .format(protocol_idx, repr(slot_name), s_idx))
            else:
                raise BadConfig('Wrong Type (protocols[{}][{}]: dict/str/list) get {} instead'
                                .format(protocol_idx, slot_name, type(slot)))

    config['protocols'].append(normalize_protocol)
    return config


def load_config(config_path_or_config):
    if isinstance(config_path_or_config, str):
        c = config_normalize(json.load(open(config_path_or_config)))
    else:
        c = config_normalize(config_path_or_config)
    config.update(c)


def get_config():
    global config
    return config
