# -*- coding: utf-8 -*-
# fbuploader/facebook.py
#
# Copyright (C) 2009-2010 Damien Churchill <damoxc@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.    If not, write to:
#   The Free Software Foundation, Inc.,
#   51 Franklin Street, Fifth Floor
#   Boston, MA    02110-1301, USA.
#

from zope.interface import implements

from twisted.internet import reactor
from twisted.internet.defer import Deferred, succeed
from twisted.internet.protocol import Protocol
from twisted.web.client import Agent, ResponseDone
from twisted.web.iweb import IBodyProducer
from twisted.web.http_headers import Headers

from fbuploader import pyfacebook

class CallbackProducer(object):
    implements(IBodyProducer)

    def __init__(self, body, chunk_size=1024, callback=None):
        self.body = body
        self.length = len(body)
        self.chunk_size = chunk_size
        self.callback = callback

    def startProducing(self, consumer):
        callback = self.callback
        body = self.body
        count = 0
        try:
            while len(body) > 0:
                if len(body) < self.chunk_size:
                    data = body
                    body = ''
                else:
                    data = body[0:self.chunk_size]
                    body = body[self.chunk_size:]

                consumer.write(data)
                count += 1
                if not callback:
                    continue

                callback(count, self.chunk_size, self.length)
        except Exception, e:
            print e

        return succeed(None)

    def pauseProducing(self):
        pass

    def stopProducing(self):
        pass

class FBResponseHandler(Protocol):

    def __init__(self, finished, client, method):
        self.finished = finished
        self.client = client
        self.data = ''
        self.method = method

    def dataReceived(self, bytes):
        self.data += bytes

    def connectionLost(self, reason):
        if reason.type != ResponseDone:
            # handle a connection error
            return
    
        response = self.client._parse_response(self.data, self.method)
        self.finished.callback(response)

class AuthProxy(pyfacebook.AuthProxy):
    
    def createToken(self):
        """
        """
        return self._client('%s.createToken' % self._name) \
            .addCallback(self._gotToken) \
            .addErrback(self._gotTokenError)

    def _gotToken(self, token):
        self._client.auth_token = token
        return token

    def _gotTokenError(self, err):
        pass

    def getSession(self):
        """
        """
        args = {}
        try:
            args['auth_token'] = self._client.auth_token
        except AttributeError:
            raise RuntimeError('Client does not have auth_token set.')

        return self._client('%s.getSession' % self._name, args) \
            .addCallback(self._gotSession) \
            .addErrback(self._gotSessionFail)

    def _gotSession(self, result):
        self._client.session_key = result['session_key']
        self._client.uid = result['uid']
        self._client.session_key = result['session_key']
        self._client.session_key_expires = result['expires']
        return result

    def _gotSessionFail(self, err):
        return err

pyfacebook.AuthProxy = AuthProxy

class PhotosProxy(pyfacebook.PhotosProxy):

    def upload(self, image, aid=None, caption=None, size=(640, 1024),
            filename=None, callback=None):
        args = {}

        if aid is not None:
            args['aid'] = aid

        if caption is not None:
            args['caption'] = caption

        args = list(self._client._build_post_args('facebook.photos.upload',
            self._client._add_session_args(args)).iteritems())

        try:
            import cStringIO as StringIO
        except ImportError:
            import StringIO

        # check for a filename specified...if the user is passing
        # binary data in image then a filename will be specified
        if filename is None:
            try:
                import Image
            except ImportError:
                data = StringIO.StringIO(open(image, 'rb').read())
            else:
                img = Image.open(image)
                if size:
                    img.thumbnail(size, Image.ANTIALIAS)
                data = StringIO.StringIO()
                img.save(data, img.format)
        else:
            # there was a filename specified, which indicates that image was
            # not the to an image file but rather the binary data of a file
            data = StringIO.String()(image)
            image = filename

        content_type, body = self.__encode_multipart_formdata(args,
            [(image, data)])

        body = CallbackProducer(body, callback=callback)

        return self._client.agent.request(
            'POST',
            self._client.facebook_url,
            Headers({
                'User-Agent': ['PyFacebook Client Library'],
                'Content-Type': [content_type],
                'Mime-version': ['1.0']
            }),
            body).addCallback(self._client._on_got_response,
                'facebook.photos.upload')

pyfacebook.PhotosProxy = PhotosProxy

class Facebook(pyfacebook.Facebook):

    def __init__(self, *args, **kwargs):
        super(Facebook, self).__init__(*args, **kwargs)
        self.agent = Agent(reactor)

    def __call__(self, method=None, args=None, secure=False):
        if args is not None and not args.has_key('locale'):
            args['locale'] = self.locale

        post_args = self._build_post_args(method, args)
        post_data = CallbackProducer(self.unicode_urlencode(post_args))

        d = Deferred()
        if self.proxy:
            # TODO: implement this
            pass
        else:
            return self.agent.request(
                'POST',
                self.facebook_secure_url if secure else self.facebook_url,
                Headers({
                    'User-Agent': ['PyFacebook Client Library']
                }),
                post_data).addCallback(self._on_got_response, method)

    def _on_got_response(self, response, method):
        d = Deferred()
        response.deliverBody(FBResponseHandler(d, self, method))
        return d
