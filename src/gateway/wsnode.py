from flask_socketio import emit
from application import socketio

@socketio.on('connect')
def connect(auth):
    emit('txnUpdate', {'data': 'Hello World!'})

