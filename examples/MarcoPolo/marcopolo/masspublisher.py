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

import logging
from time import clock

import gevent

from volttron.platform.vip.agent import BasicAgent, Core, RPC
from volttron.platform.agent import utils

utils.setup_logging()
_log = logging.getLogger(__name__)

class MassPublisher(BasicAgent):

    def __init__(self, parent):
        self.parent = parent
        self.vip = parent.vip
        super(MassPublisher, self).__init__()
        self._executing = False
        self._start_time = None
        self._finish_time = None
        self._finish_status = []
        self._received_async = []
        self._result_dict = {}
        self._agent_started = False
        self._operating_context = {
                                   'publish_topic': None,
                                   'response_topic': None,
                                   'num_bytes': None,
                                   'num_times': None,
                                   'completion_callback': None}


    @Core.receiver('onstart')
    def dostartthings(self, sender, **kwargs):
        self._agent_started = True

        if self._operating_context['completion_callback']:
            #start publishing things
            self._do_mass_publish()



    def _do_mass_publish(self):
        response_topic = self._operating_context['response_topic']
        _log.debug('Subscribing to the response topic {} with _onmessage'
                   .format(response_topic))
        self.vip.pubsub.subscribe(peer='pubsub',
                               prefix=response_topic,
                               callback=self._onmessage)

        _log.debug('Setting up run results dictionary')


        publish_topic = self._operating_context['publish_topic']
        num_bytes = self._operating_context['num_bytes']
        num_times = self._operating_context['num_times']

        self._results_dict = {}
        # Setup metadata about what is going to be sent.
        for x in range(num_times):
            self._result_dict[x] = {'idnum': x,
                                    'started': -1,
                                    'finished': -1,
                                    'eagains': 0}

        asyncResults = []
        built_bytes = '1'*num_bytes
        _log.debug('Starting publishes result')
        for x in range(num_times):
            headers = {'idnum': x}

            result = self.vip.pubsub.publish(peer='pubsub',
                              headers=headers,
                              topic=publish_topic,
                              message=built_bytes)

            asyncResults.append(result)
            _log.debug('Result loaded')

        _log.debug('Done with _do_mass_publish')


    @RPC.export
    def publish(self, publish_topic, response_topic, num_bytes, num_times,
                complete_callback):

        self._operating_context = {
                                   'publish_topic': publish_topic,
                                   'response_topic': response_topic,
                                   'num_bytes': num_bytes,
                                   'num_times': num_times,
                                   'completion_callback': complete_callback}

        # if the agent has already started then do it, otherwise
        # let the start method call the mass publish
        if self._agent_started:
            self._do_mass_publish()


    def _onmessage(self, peer, sender, bus, topic, headers, message):
        '''Handle incoming messages on the bus.'''
        self._received_async.append((headers, message))
