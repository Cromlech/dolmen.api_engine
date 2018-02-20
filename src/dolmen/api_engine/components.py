# -*- coding: utf-8 -*-

from zope.interface import Interface, implementer
from .responder import reply


class Endpoint(object):

    def __init__(self, mapper, overhead_factory=None):
        self.overhead_factory = overhead_factory
        self.mapper = mapper

    def process_action(self, environ, routing):
        action = routing.pop('controller')
        if self.overhead_factory is not None:
            overhead = self.overhead_factory(environ)
            overhead.routing = routing
        else:
            overhead = None
        return action(environ, overhead)

    def routing(self, environ):
        routing = self.mapper.match(path_info, environ)
        if routing:
            return self.process_action(environ, routing)
        return None
    
    def __call__(self, environ, start_response):
        # according to PEP 3333 the native string representing PATH_INFO
        # (and others) can only contain unicode codepoints from 0 to 255,
        # which is why we need to decode to latin-1 instead of utf-8 here.
        # We transform it back to UTF-8
        path_info = environ['PATH_INFO'].encode('latin-1').decode('utf-8')

        # Routing as usual.
        response = self.routing(environ)
        if response is None:
            response = reply(
                400, "Couldn't match any action. " +
                "Please consult the API documentation.")
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

    def __call__(self, environ, overhead):
        method = environ['REQUEST_METHOD'].upper()
        worker = getattr(self, method, None)
        if worker is None:
            # Method not allowed
            response = reply(405)
        else:
            response = worker(environ, overhead)
        return response
        
