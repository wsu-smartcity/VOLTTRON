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
from pprint import pprint
import sys
from time import time
from threading import Thread

import gevent

from . masspublisher import MassPub
from . masspublisher import MassPublisher
from . masssubscriber import MassSubscriber, MassSub
from volttron.platform.vip.agent import Agent, Core, PubSub, compat
from volttron.platform.agent import utils
from volttron.platform.messaging import headers as headers_mod
from twisted.test.test_pb import finishedCallback

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

    def _create_publisher_thread(self, identity, address):
        '''Starts an agent in the current thread.
        
        This function should be called from a secondary thread so that it
        will not block the main thread.  This function will spawn a configured
        MassPub agent.        
        '''
        _log.debug('Creating MassPub {}'.format(identity))
        agent = MassPub(address=address, identity=identity,
                        pubtopic=self.publish_to, num_bytes=self.num_bytes,
                        num_times=self.num_times)
        
        task = gevent.spawn(agent.core.run)
        try:
            task.join()
        finally:
            task.kill()

    def _create_subscriber_thread(self, identity, address):
        outfile=os.path.join(self.datadir, identity+'.txt')
        agent = MassSub(address=address, identity=identity,
                        subtopic=self.subscribe_to, 
                        outfile=outfile)
        task = gevent.spawn(agent.core.run)
        try:
            task.join()
        finally:
            task.kill()


    def _agent_finished(self, identity):
        _log.debug('Agent {} finished'.format(identity))


    def create_agent_threads(self, base_identity, address):
        '''Creates a agents separate threads so they can run independently.
        
        Loop over the number of agents specified in the configuration file. 
        For each index append -x to the end of base_identity to produce a
        'known' identity that we can communicate with the agent later on.
        
        The base_identity should be assumed to be *this* agent's identity.
        
        The generated identities are stored as the keys in the _threads 
        dictionary for later use.  The value of the _threads dictionary 
        will be the actual thread.
        
        parameters:
            base_identity - A string (should be the identity of *this* agent)
            address - The bus to connect the threaded agents to.  This 
                      address currently should be the same address that *this*
                      agent is connected to.
                      
        '''
        for x in range(self.num_agents):
            #increment so we have unique identities on the vip bus.
            identity = base_identity+'-{}'.format(x)
            if self._ispublisher:
                target = self._create_publisher_thread
            else:
                target = self._create_subscriber_thread
 
            thread = Thread(target=target, args=(identity, address))
            # Make sure the thread dies when this the scalability agent dies.
            thread.daemon = True
            thread.start()
            self._threads[identity] = thread
        _log.debug('Done creating {} threads.'.format(len(self._threads)))


    def __init__(self, config_path, **kwargs):

        self.config = utils.load_config(config_path)
        self.agent_id = self.config['agentid']
        self.config_as = self.config['config-as']
        self.publish_to = self.config.get('pubblish-to', None)
        self.subscribe_to = self.config.get('subscribe-to', None)
        self.datadir = self.config.get('datadir', None)
        address = self.config.get('address', None)
        self.num_agents = self.config.get('num_agents', 1)
        # in the if branch below we pass in either what is listed here or
        # the default publisher or subscriber depending on the context.
        identity = self.config.get('identity', kwargs.pop('identity'))
        if not identity and self._ispublisher:
            identity="masspublisher"
        elif not identity and self._issubscriber:
            identity="masssubscriber"


        super(Scalability, self).__init__(address=address, identity=identity,
                                              **kwargs)

        if self.config_as not in ('publisher', 'subscriber'):
            raise Exception('config-as must be either publisher '
                            + 'or subscriber in config file.')
        if self.config_as == 'publisher' and not self.publish_to:
            raise Exception('Invalid publish-to in config file.')
        if self.config_as == 'subscriber' and not self.subscribe_to:
            raise Exception('Invalid subscribe-to in config file.')
        if self._issubscriber:
            if not self.datadir:
                raise Exception('Invalid datafile passed.')
            try:
                os.makedirs(self.datadir)
            except:
                pass

        _log.info("id: {} config-as: {} pub-to: {} sub-to: {}"
              .format(self.agent_id, self.config_as, self.publish_to,
                      self.subscribe_to))
        
        #datafile = os.path.join(os.environ['VOLTTRON_HOME'], self.datafile)
        #_log.debug("datafile is {}".format(datafile))
        self._threads = {}
        self._ready = set()
        
        # These parameters are only necessary for publishers.
        if self._ispublisher:
            self.num_times = self.config.get('num-publishes', 5)
            self.num_bytes = self.config.get('message-size-bytes', 1)
#             self.agent = MassPublisher(self, self.publish_to, datafile,
#                                num_bytes, num_times)

    def agent_ready(self, identity):
        _log.debug('Agent {} is ready.'.format(identity))
        self._ready.add(identity)
        if self._ispublisher:
            if len(self._ready) == len(self._threads):
                self.start_work()

    @Core.receiver('onstart')
    def starting(self, sender, **kwargs):
        self.vip.rpc.export(self.agent_ready, 'ready_to_work')
        
    @Core.receiver('onstart')
    def startagent(self, sender, **kwargs):
        self.create_agent_threads(self.core.identity,
                                   self.core.address)

    def start_work(self):
        for k in self._threads.keys():
            self.vip.rpc.call(peer=k, method='start_publishing')

    @Core.receiver('onstop')
    def stopagent(self, sender, **kwargs):
        if self._ispublisher:
            self.stopagent = time()
            self.vip.rpc.call('control',
                              'stats.disable').get(timeout=10)
            d = self.vip.rpc.call('control',
                                  'stats.get').get(timeout=10)
            _log.debug('total time to publish {} msgs is {}'
                       .format(self.num_times,
                               self.stopagent- self.startagent))
            pprint(d)
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
