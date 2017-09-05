# -*- coding: utf-8 -*-

import mimetypes
from random import randrange


def make_boundary():
    return ('----------ThIs_Is_tHe_bouNdaRY_%s$' %
            hex(randrange(10<<63, 10<<64)))


def get_content_type(filename):
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'


def encode_multipart_formdata(fields, files, boundary=make_boundary):
    """
    - fields is a sequence of (name, value).
    - files is a sequence of (name, filename, value).

    Returns (content_type, body) to make an http request.
    """
    BOUNDARY = boundary()
    CRLF = '\r\n'
    L = []

    for (key, value) in fields:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"' % key)
        L.append('')
        L.append(value)

    for (key, filename, value) in files:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (
            key, filename))
        L.append('Content-Type: %s' % get_content_type(filename))
        L.append('')
        L.append(value)

    L.append('--' + BOUNDARY + '--')
    L.append('')
    body = CRLF.join(L)
    content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
    return content_type, body
