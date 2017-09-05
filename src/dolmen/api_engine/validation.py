# -*- coding: utf-8 -*-

from webob import Request
from zope.schema import getFieldsInOrder, getValidationErrors

from .responder import reply
from .definitions import METHODS


BASE_SOURCES = frozenset(('POST', 'GET'))


class allowed(object):

    def __init__(self, *methods):
        self.methods = frozenset([method.upper() for method in methods])
        assert self.methods <= METHODS, (
            'Unsupported methods : %s' % (self.methods - METHODS))

    def __call__(self, app):
        def method_watchdog(inst, environ, start_response):            
            if not environ['REQUEST_METHOD'].upper() in self.methods:
                return reply(405)
            app.__allowed__ = self.methods
            return app(inst, environ, start_response)
        return method_watchdog


class validate(object):

    def __init__(self, iface, *sources=BASE_SOURCES):
        self.iface = iface
        self.fields = getFieldsInOrder(iface)
        self.names = tuple((field[0] for field in self.fields))
        assert (BASE_SOURCES | set(sources)) == BASE_SOURCES, (
            "Only validable sources are 'POST' and 'GET'")
        self.sources = sources

    def extract_params(self, environ):
        request = Request(environ)
        if self.sources == BASE_SOURCES:
            params = request.params
        elif 'POST' in self.sources:
            params = request.POST
        elif 'GET' in self.sources:
            params = request.GET
        return params.dict_of_lists()

    def __call__(self, action):
        RequestClass = namedtuple(action.__name__, self.names)
        def process_action(API, environ, start_response):            
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
            return action(API, request)
        return process_action
