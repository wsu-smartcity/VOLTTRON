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
from pprint import pprint
import sys
import time

import gevent

from . polo import Polo
from . masspublisher import MassPublisher
from volttron.platform.vip.agent import Agent, Core, PubSub, compat
from volttron.platform.agent import utils
from volttron.platform.messaging import headers as headers_mod

utils.setup_logging()
_log = logging.getLogger(__name__)


class MarcoPolo(Agent):
    '''An agent based marco polo pool game.

    The MarcoPolo agent can be constructed as either a marco or a polo agent.
    A MarcoPolo can be
    '''

    def _onmessage(self, peer, sender, bus, topic, headers, message):
        '''Handle incoming messages on the bus.'''

        if self._ispolo:
            retmessage = headers
            retmessage['clock']=time.clock()
            self.vip.pubsub.publish(peer='pubsub',
                                topic=self._publish_to,
                                message=retmessage)

    @property
    def _ismarco(self):
        return self._config_as == 'marco'

    @property
    def _ispolo(self):
        return self._config_as == 'polo'

    def __init__(self, config_path, **kwargs):
        super(MarcoPolo, self).__init__(**kwargs)
        self._config = utils.load_config(config_path)
        self._agent_id = self._config['agentid']
        self._config_as = self._config['config-as']
        self._publish_to = self._config['pubblish-to']
        self._subscribe_to = self._config['subscribe-to']

        if self._config_as not in ('marco', 'polo'):
            raise Exception('config-as must be either marco or polo in config file.')
        if not self._subscribe_to:
            raise Exception('Invalid subscribe-to in config file.')
        if not self._publish_to:
            raise Exception('Invalid publish-to in config file.')

        _log.info("id: {} config-as: {} pub-to: {} sub-to: {}"
              .format(self._agent_id, self._config_as, self._publish_to,
                      self._subscribe_to))

        if self._ispolo:
            self.agent = Polo(self, self._subscribe_to, self._publish_to)
            gevent.spawn(self.agent.core.run)
        else:
            self._num_publishes = self._config.get('num-publishes', 5)
            self._num_bytes = self._config.get('message-size-bytes', 1)
            self._mass_publisher = None



#     def do_marco(self):
#         self._marcostart = time.clock()
#         self.vip.pubsub.publish(peer='pubsub',
#                                 topic=self._publish_to,
#                                 message=self._send_message).get(timeout=2)
#
    @Core.receiver('onsetup')
    def setup(self, sender, **kwargs):
        if self._ismarco:
            _log.debug('Configured as marco')
            self._mass_publisher = MassPublisher(self)
            self._mass_publisher.publish(self._publish_to, self._subscribe_to,
                                         self._num_bytes, self._num_publishes,
                                         self._completed)
            gevent.spawn(self._mass_publisher.core.run)

        if self._ispolo:
            _log.debug('Configured as polo')
            _log.debug('Subscribed to topic: \'{}\''.format(self._subscribe_to))
            self.vip.pubsub.subscribe('pubsub',
                                      self._subscribe_to,
                                      self._onmessage)
#
    def _completed(self, statistics):
        pprint(statistics)
        self._mass_publisher.core.stop()


def main(argv=sys.argv):
    '''Main method called by the eggsecutable.'''
    try:
        utils.vip_main(MarcoPolo)
    except Exception as e:
        _log.exception('unhandled exception')


if __name__ == '__main__':
    # Entry point for script
    sys.exit(main())
