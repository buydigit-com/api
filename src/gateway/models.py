from application import db
from src.utils import tools
import json
import hashlib
from flask import request


class CoinNetwork(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    coin_id = db.Column(db.Integer, db.ForeignKey('coin.id'))
    network_id = db.Column(db.Integer, db.ForeignKey('network.id'))

class Network(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    symbol = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean, nullable=False)
    exchange_network_ticker = db.Column(db.String(255), nullable=False)
    coin = db.relationship('Coin', secondary=CoinNetwork.__table__, backref='networks')

class Coin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    symbol = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean, nullable=False)
    decimals = db.Column(db.Integer, nullable=False)
    exchange_coin_ticker = db.Column(db.String(255), nullable=False)
    exchange_eur_pair_ticker = db.Column(db.String(255), nullable=False)
    exchange_usd_pair_ticker = db.Column(db.String(255), nullable=False)
    exchange_btc_pair_ticker = db.Column(db.String(255), nullable=False)
    network = db.relationship('Network', secondary=CoinNetwork.__table__, backref='coins')

class Dump(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(255), nullable=False)
    final_fiat_amount = db.Column(db.Float, nullable=True)
    dump_timestamp = db.Column(db.DateTime, nullable=True)
    fiat_currency = db.Column(db.String(255), nullable=True)
    exchange_trade_id = db.Column(db.String(255), nullable=True)
    coin_id = db.Column(db.Integer, db.ForeignKey('coin.id'))
    network_id = db.Column(db.Integer, db.ForeignKey('network.id'))

class Deposit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Float, nullable=True)
    amount_timestamp = db.Column(db.DateTime, nullable=True)
    real_amount_received = db.Column(db.Float, nullable=True)
    deposit_address = db.Column(db.String(255), nullable=True)
    blockchain_txid = db.Column(db.String(255), nullable=True)
    dump_id = db.Column(db.Integer, db.ForeignKey('dump.id'))
    dump = db.relationship('Dump', backref='deposit')
    coin_id = db.Column(db.Integer, db.ForeignKey('coin.id'))
    network_id = db.Column(db.Integer, db.ForeignKey('network.id'))
    
    

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, nullable=False, default=tools.nowDatetimeUTC)
    hash = db.Column(db.String(255), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=False)
    fiat_currency = db.Column(db.String(255), nullable=False)
    fiat_amount = db.Column(db.Integer, nullable=False)
    deposit_id = db.Column(db.Integer, db.ForeignKey('deposit.id'))
    deposit = db.relationship('Deposit', backref='transaction')

    def createTransaction(self):
        try:
            data = json.loads(request.data)
            
            expected_data = {
                "fiat_currency": data['fiat_currency'],
                "fiat_amount": data['fiat_amount'],
                "description": data['description'],
            }

            txn_fingerprint = str(data['fiat_currency']) + str(data['fiat_amount']) + str(tools.nowDatetimeUTC()) + str(tools.randID())
            hs = hashlib.sha1(txn_fingerprint.encode('ascii'))
            hash = hs.hexdigest()

            transaction = Transaction(
                hash=hash,
                description=expected_data['description'],
                fiat_currency=expected_data['fiat_currency'].lower(),
                fiat_amount=expected_data['fiat_amount']
            )

            deposit = Deposit(
                status="pending",
            )

            dump = Dump(
                status="pending",
            )

            transaction.deposit = deposit
            transaction.deposit.dump = dump

            db.session.add(transaction)
            db.session.commit()

            resp = tools.JsonResp({"message": "txn created", "hash": hash,
                              "redirect_url": f"/checkout/{hash}"}, 200)
                              
        except Exception as e:
            print(e)
            resp = tools.JsonResp({"message": "txn not created"}, 500)
            
        return resp

    def getTransaction(self, hash):
        try:
            transaction = Transaction.query.filter_by(hash=hash).first()
            resp = tools.JsonResp({"message": "txn found", "status": transaction.deposit.status}, 200)
        except Exception as e:
            print(e)
            resp = tools.JsonResp({"message": "txn not found"}, 500)
            
        return resp

    def setDeposit(self, hash):

        try:
            data = json.loads(request.data)
            
            expected_data = {
                "coin_id": data['coin_id'],
                "network_id": data['network_id'],
            }

            transaction = Transaction.query.filter_by(hash=hash).first()
            transaction.deposit.status = "initiated"
            transaction.deposit.deposit_address = Kraken().getDepositAddress(expected_data['coin_id'], expected_data['network_id'])
            transaction.deposit.amount = Kraken().getAmount(transaction.fiat_currency,transaction.fiat_amount,expected_data['coin_id'])
            transaction.deposit.amount_timestamp = tools.nowDatetimeUTC()
            transaction.deposit.coin_id = data['coin_id']
            transaction.deposit.network_id = data['network_id']
            db.session.commit()
            resp = tools.JsonResp({"message": "deposit set","data":{"amount":transaction.deposit.amount,"deposit_address":transaction.deposit.deposit_address}}, 200)
        except Exception as e:
            print(e)
            resp = tools.JsonResp({"message": "deposit not set"}, 500)
            
        return resp

    def updateAmount(self, hash):
        try:
            transaction = Transaction.query.filter_by(hash=hash).first()
            transaction.deposit.amount = Kraken.getAmount(transaction.fiat_currency,transaction.fiat_amount,transaction.deposit.coin_id)
            transaction.deposit.amount_timestamp = tools.nowDatetimeUTC()
            db.session.commit()
            resp = tools.JsonResp({"message": "amount updated","data":{"amount":transaction.deposit.amount}}, 200)
        except Exception as e:
            print(e)
            resp = tools.JsonResp({"message": "amount not updated"}, 500)
            
        return resp

from src.kraken.models import Kraken