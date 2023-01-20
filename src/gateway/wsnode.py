from flask_socketio import emit
from application import socketio
from src.gateway.models import Transaction
from flask import request,jsonify
from src.utils import tools

@socketio.on('connect')
def connect():
    txn_hash = request.args.get('txn_hash')
    if txn_hash:
        txn = Transaction.query.filter_by(hash=txn_hash).first()
        if txn:
            emit(txn_hash, tools.SocketResp(txn.as_dict()))

@socketio.on('initiateTransaction')
def initiateTransaction(data):
    resp = Transaction().setDeposit(data['txn_hash'],data)
    if resp.status_code == 200:
        txn = Transaction.query.filter_by(hash=data['txn_hash']).first()
        if txn:
            emit(data['txn_hash'], tools.SocketResp(txn.as_dict()))
