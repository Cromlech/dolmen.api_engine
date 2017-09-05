# -*- coding: utf-8 -*-

from .responder import reply


class Endpoint(object):

    def __init__(self, factory, actions):
        self.factory = factory
        self.actions = actions

    def __call__(self, environ, start_response):
        action = self.actions.get(environ['PATH_INFO'])
        if not action:
            response = reply(
                400, (u'Provided action does not exist. '
                      u'Please consult the API documentation.'))
        else:
            api = self.factory(environ)
            response = action(api, environ, start_response)
        return response(environ, start_response)
