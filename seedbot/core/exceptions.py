class SeedbotException(Exception):
    pass


class PluginNotFound(SeedbotException):
    pass


class BadConfig(SeedbotException):
    pass

class NotReady(SeedbotException):
    pass