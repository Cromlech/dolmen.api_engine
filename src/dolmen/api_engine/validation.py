# -*- coding: utf-8 -*-

import json
import inspect
from functools import wraps
from collections import namedtuple, Iterable
from jsonschema import Draft4Validator

from webob import Request
from zope.schema import getFieldsInOrder, getValidationErrors
from zope.schema.interfaces import ICollection

from .responder import reply
from .definitions import METHODS
from .components import IAction


SimpleOverhead = namedtuple('Overhead', ['action_request'])


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
            if hasattr(field, 'fromUnicode'):
                value = field.fromUnicode(value)
            yield value


def extract_get(environ):
    request = Request(environ)
    params = request.GET
    return params.dict_of_lists()


def extract_put(environ):
    payload = environ['wsgi.input'].read()
    if environ["Content-Type"] == 'application/json':
        return json.dumps(payload)
    return payload


def extract_post(environ):
    request = Request(environ)
    if request.content_type == 'application/json':
        return request.JSON
    params = request.POST
    return params.dict_of_lists()


class validate(object):

    extractors = {
        'GET': extract_get,
        'POST': extract_post,
        'PUT': extract_put,
    }

    def __init__(self, iface, as_dict=False, *sources):
        self.iface = iface
        self.fields = getFieldsInOrder(iface)
        self.as_dict = as_dict

    def extract(self, environ):
        method = environ['REQUEST_METHOD']
        extractor = self.extractors.get(method)
        if extractor is None:
            raise NotImplementedError('No extractor for method %s' % method)
        return extractor(environ)

    def process_action(self, environ, requestcls):
        params = self.extract(environ)            
        fields = list(extract_fields(self.fields, params))
        request = requestcls(*fields)
        errors = getValidationErrors(self.iface, request)
        nb_errors = len(errors)
    
        if nb_errors:
            summary = {}
            for field, error in errors:
                doc = getattr(error, 'doc', error.__str__)
                field_errors = summary.setdefault(field, [])
                field_errors.append(doc())

            return reply(
                400, text=json.dumps(summary),
                content_type="application/json")

        return request

    def __call__(self, action):
        names = tuple((field[0] for field in self.fields))
        RequestClass = namedtuple(action.__name__, names)

        @wraps(action)
        def method_validation(*args):
            if IAction.providedBy(args[0]):
                inst, environ, overhead = args
            else:
                inst = None
                environ, overhead = args

            result = self.process_action(environ, RequestClass)
            if isinstance(result, RequestClass):
                if self.as_dict:
                    result = result._asdict()

                if overhead is None:
                    overhead = SimpleOverhead(action_request=result)
                else:
                    overhead.action_request = result

                if inst is not None:
                    return action(inst, environ, overhead)
                return action(environ, overhead)

            return result
        return method_validation


class JSONSchema(object):

    def __init__(self, schema_string):
        self.string = schema_string
        self.schema = json.loads(schema_string)
        
    def validate(self, obj):
        errors = {}
        validator = Draft4Validator(self.schema)
        for error in sorted(validator.iter_errors(obj), key=str):
            for field in error.path:
                fielderrors = errors.setdefault(field, [])
                fielderrors.append(error.message)
        return errors

    def json_validator(self, method):
        @wraps(method)
        def validate_method(inst, environ, overhead):
            if environ.get('CONTENT_TYPE') != 'application/json':
                return reply(406, text="Content type must be application/json")
            
            request = Request(environ)
            errors = self.validate(request.json)
            if errors:
                return reply(
                    400, text=json.dumps(errors),
                    content_type='application/json')
            overhead.action_request = request.json
            return method(inst, environ, overhead)
        return validate_method
