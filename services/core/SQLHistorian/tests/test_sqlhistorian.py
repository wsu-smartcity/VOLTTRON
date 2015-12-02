# Example file using the weather agent.
#
# Requirements
#    - A VOLTTRON instance must be started
#    - A weatheragnet must be running prior to running this code.
#
# Author: Craig Allwardt

import dateutil.parser
from volttron.platform.vip.agent import Agent
import gevent
from gevent.core import callback
import random
from volttron.platform.messaging import headers as headers_mod


          

    
a = Agent()
gevent.spawn(a.core.run).join(0)
                       
try: 
    

    ''' This method publishes fake data for use by the rest of the agent.
    The format mimics the format used by VOLTTRON drivers.
    
    This method can be removed if you have real data to work against.
    '''
    
    #Make some random readings
    oat_reading = random.uniform(30,100)
    mixed_reading = oat_reading + random.uniform(-5,5)
    damper_reading = random.uniform(0,100)
    
    # Create a message for all points.
    all_message = [{'OutsideAirTemperature': oat_reading, 'MixedAirTemperature': mixed_reading, 
                'DamperSignal': damper_reading},
               {'OutsideAirTemperature': {'units': 'F', 'tz': 'UTC', 'type': 'float'},
                'MixedAirTemperature': {'units': 'F', 'tz': 'UTC', 'type': 'float'}, 
                'DamperSignal': {'units': '%', 'tz': 'UTC', 'type': 'float'}
                }]
    
    
    
    #Create timestamp
    now = '2015-11-18T21:24:10.000Z'
    headers = {
        headers_mod.DATE: now
    }
    
    #Publish messages
    result = a.vip.pubsub.publish(
        'pubsub', 'devices/Building/LAB/Device/all', headers, all_message).get(timeout=10)
            
    
    gevent.sleep(5)
    

    result = a.vip.rpc.call('platform.historian', 
                   'query', 
                    topic='Building/LAB/Device/OutsideAirTemperature',
                   count = 20,
                   order = "LAST_TO_FIRST").get(timeout=10)
    print('Query Result', result)
except Exception as e:
    print ("Could not contact historian. Is it running?")
    print(e)
                 
gevent.sleep(5)
a.core.stop()



