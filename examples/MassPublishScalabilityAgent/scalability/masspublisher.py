# -*- coding: utf-8 -*- {{{
# vim: set fenc=utf-8 ft=python sw=4 ts=4 sts=4 et:
#
# Copyright (c) 2015, Battelle Memorial Institute
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# The views and conclusions contained in the software and documentation are those
# of the authors and should not be interpreted as representing official policies,
# either expressed or implied, of the FreeBSD Project.
#

# This material was prepared as an account of work sponsored by an
# agency of the United States Government.  Neither the United States
# Government nor the United States Department of Energy, nor Battelle,
# nor any of their employees, nor any jurisdiction or organization
# that has cooperated in the development of these materials, makes
# any warranty, express or implied, or assumes any legal liability
# or responsibility for the accuracy, completeness, or usefulness or
# any information, apparatus, product, software, or process disclosed,
# or represents that its use would not infringe privately owned rights.
#
# Reference herein to any specific commercial product, process, or
# service by trade name, trademark, manufacturer, or otherwise does
# not necessarily constitute or imply its endorsement, recommendation,
# r favoring by the United States Government or any agency thereof,
# or Battelle Memorial Institute. The views and opinions of authors
# expressed herein do not necessarily state or reflect those of the
# United States Government or any agency thereof.
#
# PACIFIC NORTHWEST NATIONAL LABORATORY
# operated by BATTELLE for the UNITED STATES DEPARTMENT OF ENERGY
# under Contract DE-AC05-76RL01830

#}}}

from __future__ import absolute_import

import json
import logging
import sys
from time import time

import gevent

from volttron.platform.vip.agent import Agent, BasicAgent, Core, RPC
from volttron.platform.agent import utils


utils.setup_logging()
_log = logging.getLogger(__name__)

class MassPub(Agent):
    
    def _getroot(self, id):
        return id[:-2]

    def __init__(self, identity, pubtopic, num_bytes, num_times,
                 finished_callback=None, address=None):
        super(MassPub, self).__init__(identity=identity, address=address)

        self.finished = True
        self.started = False

        self.finished_callback = finished_callback
        self.pubtopic = pubtopic
        self.num_times = num_times
        self.num_bytes = num_bytes
        self.parent_id = self._getroot(identity)

    @Core.receiver('onsetup')
    def on_setup(self, sender, **kwargs):
        _log.debug('Setting up MassPub')
        self.vip.rpc.export(self._start_publishing, 'start_publishing')
        
    @Core.receiver('onstart')
    def on_start(self, sender, **kwargs):
        _log.debug('Starting MassPub {}'.format(self.core.identity))
        _log.debug('HELLO {}'.format(self.vip.hello().get(timeout=2)))
        self.vip.rpc.call(self._getroot(self.core.identity), 'ready_to_work', self.core.identity)

    @Core.receiver('onstop')
    def on_stop(self, sender, **kwargs):
        _log.debug('Ending MassPub {}'.format(self.core.identity))

    def _start_publishing(self):
        _log.debug('Starting to publish from {}'.format(self.core.identity))




class MassPublisher(BasicAgent):

    def __init__(self, parent, pubtopic, outputfile,
                 num_bytes, num_times):
        super(MassPublisher, self).__init__()
        self.parent = parent
        self.vip = parent.vip
        self.pubtopic = pubtopic
        self.num_bytes = num_bytes
        self.num_times = num_times
        self.outputfile = outputfile

    @Core.receiver('onstart')
    def on_start(self, sender, **kwargs):
        self.outstream = open(self.outputfile, 'w')
        self.outstream.write('Test begins: {}'.format(time()))
        self.vip.pubsub.subscribe(peer='pubsub',
                                  prefix='control/publisher',
                                  callback=self.oncontrol)

        self.vip.pubsub.publish(peer='pubsub',
                                topic='control/subscriber',
                                message=self.num_times)
        self.start_publishing()

    @Core.receiver('onstop')
    def on_stop(self, sender, **kwargs):
        _log.debug('Stoping agent now!')
        self.outstream.write('Test ends: {}\n'.format(time()))
        self.outstream.close()

    def oncontrol(self, peer, sender, bus, topic, headers, message):
        self.parent.core.stop()

    def start_publishing(self):
        built_bytes = '1'*self.num_bytes
        for x in range(self.num_times):
            headers = {'idnum': x,
                       'started': time()}
            self.vip.pubsub.publish(peer='pubsub',
                                    headers=headers,
                                    topic=self.pubtopic,
                                    message=built_bytes)
            self.outstream.write("{}\n".format(json.dumps(headers)))
