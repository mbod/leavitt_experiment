# flask app for web socket chatroom 
# allow WS clients to join and 
# 1. listen to stream of messages
# 2. post messages
#
# stream of messages captured in sequence
#


from flask import Flask, request, render_template, session, url_for
from flask_socketio import SocketIO, join_room, leave_room, send
import logging


app = Flask(__name__)
app.config['SECRET_KEY'] = 'coll@bplan!'

socketio = SocketIO(app)


# TODO: move messages data structure
#       to a persistent db
messages = []

# TODO: migrate to redis
connected_clients = {}


# --- app routes --------------------------------------------------

@app.route('/chatroom')
def chatroom():
    '''
    Chatroom view
    '''

    session.clear()
    session['room'] = 'test'
    
    room = session.get('room')


    return render_template('chatroom.html',
                           room=room)


# ----- SOCKETIO handlers -----------------------------------------

@socketio.on('connect')
def handle_connect(auth):
    '''
    WS client connecting to room
    '''
    print('CONNECTION ATTEMPT', auth)
    logger.info(f'Connection request: {auth}')

    sid = request.sid
    
    if auth and auth.get('token') == app.config['SECRET_KEY']:
        connected_clients[sid] = {
            'client': sid,
            'room': auth.get('room')
        }

    else:
        if not session.get('room'):
            return False

        connected_clients[sid] = {
            'client': sid,
            'room': 'test'
        }
    
    logger.info(f'Connected clients: {connected_clients}')

    # join room
    join_room(connected_clients[sid]['room'])


@socketio.on('disconnect')
def handle_disconnect():
    '''
    WS client leaves a room
    '''
    room = session.get('room')
    leave_room(room)

@socketio.on('message')
def handle_message(payload):

    print('MESSAGE - ', payload, request.sid)

    client = connected_clients.get(request.sid)
    print(client)
    #if not client:
    #    return
    
    room = client['room'] # session.get('room')
    
    # message
    sender = payload['from']
    message = payload['message']    

    logger.info(f'Sending {payload} to {room}')
    send(payload, to=room)
    
    
    
if __name__ == "__main__":

    logger = logging.getLogger(__name__)

    socketio.run(app, port=5555, debug=True)