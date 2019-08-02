from multiprocessing import Lock
from multiprocessing.managers import BaseManager

state = {
    'is_playing' : False,
    'position_sec' : 0,
    'duration_sec' : 0
}

events = {}
client_num = 0

class EventManager(BaseManager): pass

def add_waiting_client():
    global events
    global client_num

    client_num += 1
    events[client_num] = []
    return client_num

def add_event(event):
    global events
    for user_id in events.keys():
        events[user_id].append(event)

def get_events(user_id):
    global events
    if not has_events(user_id): return []
    evts = list(events[user_id])
    del events[user_id]
    return evts

def has_events(user_id):
    global events
    return user_id in events and len(events[user_id]) > 0

def update_state(_state):
    global state
    state.update(_state)

def get_state():
    global state
    return state

EventManager.register('add_waiting_client', add_waiting_client)
EventManager.register('has_events', has_events)
EventManager.register('add_event', add_event)
EventManager.register('get_events', get_events)
EventManager.register('update_state', update_state)
EventManager.register('get_state', get_state)
m = EventManager(('', 50001), b'password')
s = m.get_server()
s.serve_forever()


