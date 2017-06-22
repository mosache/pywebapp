#! /usr/bin/env python
# coding=utf-8

import src.config.config_default as default

configs = default.configs


def merge(defaults, override):
    r = {}
    for k, v in default.items():
        if k in override:
            if isinstance(v, dict):
                r[k] = merge(v, override[k])
            else:
                r[k] = override[k]
        else:
            r[k] = v
    return r


try:
    import src.config.config_override as conf_override

    configs = merge(configs, conf_override.configs)
except ImportError:
    pass
