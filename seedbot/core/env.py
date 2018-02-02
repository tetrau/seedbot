env = {}


def get_env():
    global env
    return env


def set_env(**kwargs):
    global env
    env.update(dict(**kwargs))
