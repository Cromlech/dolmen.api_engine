# -*- coding: utf-8 -*-

from functools import wraps


def allow_origins(origins, codes=(200,)):
    def cors_wrapper(method):
        @wraps(method)
        def add_cors_header(*args, **kwargs):
            res = method(*args, **kwargs)
            if not codes or not res.status_int in codes:
                return res
            res.headers["Access-Control-Allow-Origin"] = origins
            return res
        return add_cors_header
    return cors_wrapper
