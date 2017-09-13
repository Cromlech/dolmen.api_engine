# -*- coding: utf-8 -*-

from collections import namedtuple, Iterable
from webob import Request
from zope.schema import getFieldsInOrder, getValidationErrors
from zope.schema.interfaces import ICollection

from .responder import reply
from .definitions import METHODS


SOURCES = frozenset(('POST', 'GET'))
JSON = frozenset(('JSON',))


def extract_fields(fields, params):
    for name, field in fields:
        value = params.get(name)
        
        if value is None:
            yield value
        elif ICollection.providedBy(field):
            if not isinstance(value, Iterable):
                value = [value]
            yield value
        else:
            if (isinstance(value, Iterable) and
                not isinstance(value, (str, bytes))):
                value = value[0]
            yield value


class cors_aware(object):

    def __init__(self, request_handler, response_handler):
        self.request_handler = request_handler
        self.response_handler = response_handler

    def __call__(self, app):
        def options_handler(environ, start_response, overhead=None):
            if environ['REQUEST_METHOD'].upper() == 'OPTIONS':
                return self.request_handler(environ)
            response = app(environ, start_response, overhead)
            return self.response_handler(response)
        return options_handler


class allowed(object):

    def __init__(self, *methods):
        self.methods = frozenset((method.upper() for method in methods))
        assert self.methods <= METHODS, (
            'Unsupported methods : %s' % (self.methods - METHODS))

    def __call__(self, app):
        def method_watchdog(environ, start_response, overhead=None):            
            if not environ['REQUEST_METHOD'].upper() in self.methods:
                return reply(405)
            return app(environ, start_response, overhead)
        return method_watchdog


class validate(object):

    def __init__(self, iface, *sources):
        self.iface = iface
        self.fields = getFieldsInOrder(iface)
        self.names = tuple((field[0] for field in self.fields))
        self.sources = frozenset(sources)        
        assert self.sources <= SOURCES or self.sources == JSON, \
            "Only validable sources are 'POST' and/or 'GET' or 'JSON'"

    def extract_params(self, environ):
        request = Request(environ)

        # We return the JSON dict, directly
        if self.sources == JSON:
            return request.json

        # We use the webob extraction then merge into a simple dict.
        if self.sources == SOURCES:
            params = request.params
        elif 'POST' in self.sources:
            params = request.POST
        elif 'GET' in self.sources:
            params = request.GET

        return params.dict_of_lists()

    def __call__(self, action):
        RequestClass = namedtuple(action.__name__, self.names)
        def process_action(environ, start_response, overhead=None):
            params = self.extract_params(environ)            
            fields = list(extract_fields(self.fields, params))
            request = RequestClass(*fields)
            errors = getValidationErrors(self.iface, request)
            nb_errors = len(errors)
            
            if nb_errors:
                summary = []
                for field, error in errors:
                    doc = getattr(error, 'doc', None)
                    if doc is not None:
                        summary.append('`%s`: %s' % (field, doc()))
                    else:
                        summary.append(str(error))
                return reply(400, '\n'.join(summary))
            return action(request, overhead)
        return process_action
