import weakref
import logging
from .exceptions import *

logger = logging.getLogger('seedbot')
logger.addHandler(logging.NullHandler())


class SeedbotPlugin(type):
    def __new__(meta, name, bases, class_dict):
        cls = type.__new__(meta, name, bases, class_dict)
        if cls.__bases__ != (object,):
            cls._plugins.update({cls.__name__: cls})
        logger.debug('load plugin {}'.format(cls.__name__))
        return cls


class SeedbotPrepare(metaclass=SeedbotPlugin):
    _plugins = weakref.WeakValueDictionary()

    @classmethod
    def _search(cls, plugin_name):
        try:
            return cls._plugins[plugin_name]
        except KeyError:
            raise PluginNotFound('{}: {}'.format(cls.__name__, repr(plugin_name)))

    def prepare(self):
        pass


class SeedbotInput(metaclass=SeedbotPlugin):
    _plugins = weakref.WeakValueDictionary()

    @classmethod
    def _search(cls, plugin_name):
        try:
            return cls._plugins[plugin_name]
        except KeyError:
            raise PluginNotFound('{}: {}'.format(cls.__name__, repr(plugin_name)))

    def fetch(self):
        return []


class SeedbotPipeline(metaclass=SeedbotPlugin):
    _plugins = weakref.WeakValueDictionary()

    @classmethod
    def _search(cls, plugin_name):
        try:
            return cls._plugins[plugin_name]
        except KeyError:
            raise PluginNotFound('{}: {}'.format(cls.__name__, repr(plugin_name)))

    def Process(self, torrents):
        return []
