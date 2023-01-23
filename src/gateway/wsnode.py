from flask_socketio import emit
from application import socketio
from src.gateway.models import Transaction
from flask import request,jsonify
from src.utils import tools

def emitUpdate(txn_hash):
    txn = Transaction.query.filter_by(hash=txn_hash).first()
    if txn:
        emit(txn_hash, tools.SocketResp(txn.to_dict()))

@socketio.on('connect')
def connect():
    txn_hash = request.args.get('txn_hash')
    if txn_hash:
        emitUpdate(txn_hash)

@socketio.on('initiateTransaction')
def initiateTransaction(data):
    resp = Transaction().setDeposit(data['txn_hash'],data)
    if resp.status_code == 200:
        emitUpdate(data['txn_hash'])
