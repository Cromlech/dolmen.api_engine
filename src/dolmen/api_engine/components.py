# -*- coding: utf-8 -*-

from .responder import reply
from zope.interface import Interface, implementer


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


class IAction(Interface):
    pass


@implementer(IAction)
class Action(object):
    """Implementation of an action as a class.
    This works as an HTTP METHOD dispatcher.
    The method names of the class must be a valid uppercase HTTP METHOD name
    example : OPTIONS, GET, POST
    """

    def __call__(self, environ, start_response, overhead):
        method = environ['REQUEST_METHOD'].upper()
        worker = getattr(self, method, None)
        if worker is None:
            # Method not allowed
            response = reply(405)
        else:
            response = worker(environ, overhead)
        return response
        
