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
import os
import sys
import time

import gevent

from . masspublisher import MassPublisher
from . masssubscriber import MassSubscriber
from volttron.platform.vip.agent import Agent, Core, PubSub, compat
from volttron.platform.agent import utils
from volttron.platform.messaging import headers as headers_mod

utils.setup_logging()
_log = logging.getLogger(__name__)


class Scalability(Agent):
    '''An agent based marco polo pool game.

    The MarcoPolo agent can be constructed as either a marco or a polo agent.
    A MarcoPolo can be
    '''
    @property
    def _ispublisher(self):
        return self.config_as == 'publisher'

    @property
    def _issubscriber(self):
        return self.config_as == 'subscriber'

    def __init__(self, config_path, **kwargs):
        super(Scalability, self).__init__(**kwargs)
        self.config = utils.load_config(config_path)
        self.agent_id = self.config['agentid']
        self.config_as = self.config['config-as']
        self.publish_to = self.config.get('pubblish-to', None)
        self.subscribe_to = self.config.get('subscribe-to', None)
        self.datafile = self.config.get('outfile', None)

        if self.config_as not in ('publisher', 'subscriber'):
            raise Exception('config-as must be either publisher '
                            + 'or subscriber in config file.')
        if self.config_as == 'publisher' and not self.publish_to:
            raise Exception('Invalid publish-to in config file.')
        if self.config_as == 'subscriber' and not self.subscribe_to:
            raise Exception('Invalid subscribe-to in config file.')
        if not self.datafile:
            raise Exception('Invalid datafile passed.')

        _log.info("id: {} config-as: {} pub-to: {} sub-to: {}"
              .format(self.agent_id, self.config_as, self.publish_to,
                      self.subscribe_to))
        datafile = os.path.join(os.environ['VOLTTRON_HOME'], self.datafile)
        _log.debug("datafile is {}".format(datafile))
        if self._issubscriber:
            self.agent = MassSubscriber(self, datafile,
                                        self.subscribe_to)
        else:
            num_times = self.config.get('num-publishes', 5)
            num_bytes = self.config.get('message-size-bytes', 1)
            self.agent = MassPublisher(self, self.publish_to, datafile,
                               num_bytes, num_times)
#
    @Core.receiver('onstart')
    def startagent(self, sender, **kwargs):
        gevent.spawn(self.agent.core.run)
        if self._ispublisher:
            self.vip.rpc.call('control',
                              'stats.enable').get(timeout=2)

    @Core.receiver('onstop')
    def stopagent(self, sender, **kwargs):
        if self._ispublisher:
            self.vip.rpc.call('control',
                              'stats.disable').get(timeout=2)
        self.agent.core.stop()

def main(argv=sys.argv):
    '''Main method called by the eggsecutable.'''
    try:
        utils.vip_main(Scalability)
    except Exception as e:
        _log.exception('unhandled exception')


if __name__ == '__main__':
    # Entry point for script
    sys.exit(main())
