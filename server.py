import requests
from flask import Flask, request, render_template, current_app, jsonify
from threading import Lock
import json, time, os, os.path
from multiprocessing.managers import BaseManager

app = Flask(__name__)
app.config.from_object(__name__)

PAGE_ACCESS_TOKEN = os.environ['PAGE_ACCESS_TOKEN']

lock = Lock()

class PlayerManager(BaseManager): pass

def get_player_manager():
    player_manager = PlayerManager(('', 50002), b'password123')
    player_manager.register('command')
    player_manager.connect()

    return player_manager

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
    print('handle_message')
    response = {}

    success, d = get_player_manager().command(message)._getvalue()
    print('commanded')
    response = { 'text' : d['message'] }

    call_send_api(sender_psid, response)
    print('send api')

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
