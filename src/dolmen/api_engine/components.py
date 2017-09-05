# -*- coding: utf-8 -*-

from .responder import reply


class Endpoint(object):

    def __init__(self, actions, overhead_factory=None):
        self.overhead_factory = overhead_factory
        self.actions = actions

    def __call__(self, environ, start_response):
        action = self.actions.get(environ['PATH_INFO'])
        if not action:
            response = reply(
                400, (u'Provided action does not exist. '
                      u'Please consult the API documentation.'))
        else:
            if self.overhead_factory is not None:
                overhead = self.overhead_factory(environ)
            else:
                overhead = None
            response = action(environ, start_response, overhead)
        return response(environ, start_response)
