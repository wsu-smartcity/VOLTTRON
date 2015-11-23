from time import time

def masspub(vip, sender, message, times, topic='marco', complete_callback=None):
    '''Publishes message to the vip pubsub bus.
    
    '''
    
    completed = []
    started = []
    x = 0
    messagelen = len(message)
    while len(started) < times:
        headers = {'idnum': x,
                   'sender': sender,
                   'started': time(),
                   'bytes-sent': messagelen}
        started.append(vip.pubsub.publish(peer='pubsub',
                                headers=headers,
                                topic=topic,
                                message=message))
        x += 1
        
    if complete_callback:
        complete_callback()