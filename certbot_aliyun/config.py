from yaml import safe_load


cache = None


def get_config(conf: str):
    global cache

    if cache:
        return cache

    with open(conf) as f:
        cache = safe_load(f)
        return cache
