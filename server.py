import requests
from flask import Flask, request, render_template, current_app, jsonify
from threading import Lock
import json, time, os, os.path
from multiprocessing.managers import BaseManager

app = Flask(__name__)
app.config.from_object(__name__)

PAGE_ACCESS_TOKEN = os.environ['PAGE_ACCESS_TOKEN']

lock = Lock()
events_file = 'events.evt'

class EventManager(BaseManager): pass
class PlayerManager(BaseManager): pass

def get_event_manager():
    event_manager = EventManager(('', 50001), b'password')
    event_manager.register('add_waiting_client')
    event_manager.register('add_event')
    event_manager.register('get_events')
    event_manager.register('has_events')
    event_manager.register('update_state')
    event_manager.register('get_state')
    event_manager.connect()

    return event_manager

def get_player_manager():
    player_manager = PlayerManager(('', 50002), b'password')
    player_manager.register('command')
    player_manager.connect()

    return player_manager
    
@app.route('/poll')
def poll():
    evt_mgr = get_event_manager()

    user_id = evt_mgr.add_waiting_client()._getvalue()

    while not evt_mgr.has_events(user_id)._getvalue():
        time.sleep(0.5)

    event = { "type" : "NONE" }
    with lock:
        event = evt_mgr.get_events(user_id)._getvalue()[0]
    
    return event

@app.route('/event', methods=['PUT'])
def event():
    evt_mgr = get_event_manager()
    d = request.get_json()
    with lock:
        evt_mgr.add_event(d)

    return ''

@app.route('/update_ytplayer_state', methods=['POST'])
def update_yt_player_state():
    get_event_manager().update_state(request.get_json())
    return '', 200

@app.route('/ytplayer_state', methods=['GET'])
def get_ytplayer_state():
    return jsonify(get_event_manager().get_state()._getvalue()), 200

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/webhook', methods=['POST'])
def subscribe():
    body = request.get_json()

    if body['object'] == 'page':
        for entry in body['entry']:
            webhook_event = entry['messaging'][0]
            sender_psid = webhook_event['sender']['id']
            if 'message' in webhook_event:
                handle_message(sender_psid, webhook_event['message'])
            elif 'postback' in webhook_event:
                handle_postback(sender_psid, webhook_event['postback'])
        return ('EVENT_RECEIVED', 200, [])
    else:
        return ('', 404, [])

@app.route('/webhook', methods=['GET'])
def get():
    VERIFY_TOKEN = '4891'

    mode = request.args['hub.mode']
    token = request.args['hub.verify_token']
    challenge = request.args['hub.challenge']

    if mode and token:
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            return (challenge, 200, [])
        else:
            return ('', 403, [])

def handle_message(sender_psid, message):
    response = {}

    success, d = get_player_manager().command(message)._getvalue()
    response = { 'text' : d['message'] }

    call_send_api(sender_psid, response)

def call_send_api(sender_psid, response):
    request_body = {
        'recipient' : {
            'id' : sender_psid
        },
        'message': response
    }

    r = requests.post(
        url='https://graph.facebook.com/v2.6/me/messages',
        params={ 'access_token' : PAGE_ACCESS_TOKEN },
        json=request_body)

def handle_postback(sender_psid, postback):
    pass

# sudo /usr/local/bin/certbot-auto renew or sudo /usr/local/bin/certbot renew
if __name__ == "__main__":
    app.run(threaded=True, host="0.0.0.0", port=443, ssl_context=(
        '/etc/letsencrypt/live/api.lucaduran.com/fullchain.pem', '/etc/letsencrypt/live/api.lucaduran.com/privkey.pem'))
