# -*- coding: utf-8 -*- {{{
# vim: set fenc=utf-8 ft=python sw=4 ts=4 sts=4 et:

# Copyright (c) 2015, Battelle Memorial Institute
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# The views and conclusions contained in the software and documentation
# are those of the authors and should not be interpreted as representing
# official policies, either expressed or implied, of the FreeBSD
# Project.
#
# This material was prepared as an account of work sponsored by an
# agency of the United States Government.  Neither the United States
# Government nor the United States Department of Energy, nor Battelle,
# nor any of their employees, nor any jurisdiction or organization that
# has cooperated in the development of these materials, makes any
# warranty, express or implied, or assumes any legal liability or
# responsibility for the accuracy, completeness, or usefulness or any
# information, apparatus, product, software, or process disclosed, or
# represents that its use would not infringe privately owned rights.
#
# Reference herein to any specific commercial product, process, or
# service by trade name, trademark, manufacturer, or otherwise does not
# necessarily constitute or imply its endorsement, recommendation, or
# favoring by the United States Government or any agency thereof, or
# Battelle Memorial Institute. The views and opinions of authors
# expressed herein do not necessarily state or reflect those of the
# United States Government or any agency thereof.
#
# PACIFIC NORTHWEST NATIONAL LABORATORY
# operated by BATTELLE for the UNITED STATES DEPARTMENT OF ENERGY
# under Contract DE-AC05-76RL01830
#}}}

import asynchat
import asyncore
import socket
import sys

from flexjsonrpc.util import asynchunk
from flexjsonrpc.framing import chunked

class TestAsynchunkModule(object):
    _chunks = ['This is a test', 'of the asynchunk module.', '']
    _encoded = 'e\r\n{}\r\n18\r\n{}\r\n0\r\n\r\n'.format(*_chunks)

    def setup(self):
        self.map = {}
        self.incoming = []
        self.error = None
        async_sock, self.sock = socket.socketpair()
        self.dispatcher = asynchunk.Dispatcher(async_sock, self.map)
        self.dispatcher.handle_chunk = self.handle_chunk
        self.dispatcher.handle_error = self.handle_error

    def handle_chunk(self, chunk):
        self.incoming.append(chunk)

    def handle_error(self):
        self.error = sys.exc_info()

    def test_push(self):
        map(self.dispatcher.push_chunk, self._chunks)
        assert self.sock.recv(1024) == self._encoded
        assert not self.error

    def test_decode(self):
        self.sock.sendall(self._encoded)
        asyncore.loop(1, map=self.map, count=1)
        assert self.incoming == self._chunks
        assert not self.error

    def test_invalid_chunk_length(self):
        self.sock.sendall('get\r\na bogus message\r\n')
        asyncore.loop(1, map=self.map, count=1)
        assert self.error and self.error[0] is asynchunk.Error

    def test_chunk_length_with_extension(self):
        data = self._encoded[0:1] + '  ;  some extension  ' + self._encoded[1:]
        self.sock.sendall(data)
        asyncore.loop(1, map=self.map, count=1)
        assert self.incoming == self._chunks
        assert not self.error

