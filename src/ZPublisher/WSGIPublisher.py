##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
""" Python Object Publisher -- Publish Python objects on web servers
"""
from cStringIO import StringIO
import time

from ZServer.medusa.http_date import build_http_date
from ZPublisher.HTTPResponse import HTTPResponse
from ZPublisher.HTTPRequest import HTTPRequest
from ZPublisher.mapply import mapply
from ZPublisher.Publish import call_object
from ZPublisher.Publish import dont_publish_class
from ZPublisher.Publish import get_module_info
from ZPublisher.Publish import missing_name

_NOW = None     # overwrite for testing
def _now():
    if _NOW is not None:
        return _NOW
    return time.time()

class WSGIResponse(HTTPResponse):
    """A response object for WSGI

    This Response object knows nothing about ZServer, but tries to be
    compatible with the ZServerHTTPResponse.

    Most significantly, streaming is not (yet) supported.
    """
    _streaming = _chunking = 0
    _http_version = None
    _server_version = None
    _http_connection = None

    # Set this value to 1 if streaming output in
    # HTTP/1.1 should use chunked encoding
    http_chunk = 0

    def finalize(self):

        headers = self.headers
        body = self.body

        # set 204 (no content) status if 200 and response is empty
        # and not streaming
        if ('content-type' not in headers and
            'content-length' not in headers and
            not self._streaming and self.status == 200):
            self.setStatus('nocontent')

        # add content length if not streaming
        content_length = headers.get('content-length')

        if content_length is None and not self._streaming:
            self.setHeader('content-length', len(body))

        if self._http_version == '1.0':
            if (self._http_connection == 'keep-alive' and
                'content-length' in self.headers):
                self.setHeader('Connection', 'Keep-Alive')
            else:
                self.setHeader('Connection', 'close')

        # Close the connection if we have been asked to.
        # Use chunking if streaming output.
        if self._http_version == '1.1':
            if self._http_connection == 'close':
                self.setHeader('Connection', 'close')
            elif not self.headers.has_key('content-length'):
                if self.http_chunk and self._streaming:
                    self.setHeader('Transfer-Encoding', 'chunked')
                    self._chunking = 1
                else:
                    self.setHeader('Connection','close')

        return '%s %s' % (self.status, self.errmsg), self.listHeaders()

    def listHeaders(self):
        result = []
        if self._server_version:
            result.append(('Server', self._server_version))

        result.append(('Date', build_http_date(_now())))
        result.extend(HTTPResponse.listHeaders(self))
        return result

    def __str__(self):

        # XXX Consider how we are to handle the cases this logic was trying
        # to cover
        #if self._wrote:
        #    if self._chunking:
        #        return '0\r\n\r\n'
        #    else:
        #        return ''
        raise NotImplementedError

def publish(request, module_name, after_list, debug=0):

    (bobo_before,
     bobo_after,
     object,
     realm,
     debug_mode,
     err_hook,
     validated_hook,
     transactions_manager,
    )= get_module_info(module_name)

    request.processInputs()
    response = request.response

    after_list[0] = bobo_after

    if debug_mode:
        response.debug_mode = debug_mode

    if realm and not request.get('REMOTE_USER', None):
        response.realm = realm

    if bobo_before is not None:
        bobo_before()

    # Get the path list.
    # According to RFC1738 a trailing space in the path is valid.
    path = request.get('PATH_INFO')

    request['PARENTS'] = parents = [object]

    object = request.traverse(path, validated_hook=validated_hook)

    if transactions_manager:
        transactions_manager.recordMetaData(object, request)

    result = mapply(object,
                    request.args,
                    request,
                    call_object,
                    1,
                    missing_name,
                    dont_publish_class,
                    request,
                    bind=1,
                    )

    if result is not response:
        response.setBody(result)

    return response

def publish_module(environ, start_response):

    status = 200
    after_list = [None]
    stdout = StringIO()
    stderr = StringIO()
    response = WSGIResponse(stdout=stdout, stderr=stderr)
    response._http_version = environ['SERVER_PROTOCOL'].split('/')[1]
    response._http_connection = environ.get('CONNECTION_TYPE', 'close')
    response._server_version = environ['SERVER_SOFTWARE']

    request = HTTPRequest(environ['wsgi.input'], environ, response)

    # Let's support post-mortem debugging
    handle_errors = environ.get('wsgi.handleErrors', True)

    response = publish(request, 'Zope2', after_list=[None],
                       debug=handle_errors)
    if response:
        # Start the WSGI server response
        status, headers = response.finalize()
        # ZServerHTTPResponse calculates all headers and things when you
        # call it's __str__, so we need to get it, and then munge out
        # the headers from it. It's a bit backwards, and we might optimize
        # this by not using ZServerHTTPResponse at all, and making the
        # HTTPResponses more WSGI friendly. But this works.
        start_response(status, headers)
        # If somebody used response.write, that data will be in the
        # stdout StringIO, so we put that before the body.
        # XXX This still needs verification that it really works.
        result=(stdout.getvalue(), response.body)
    request.close()
    stdout.close()

    if after_list[0] is not None:
        after_list[0]()

    # Return the result body iterable.
    return result

