from application import db
from src.utils import tools
import json
import hashlib
from flask import request
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy.types import JSON
from datetime import datetime, timedelta
from sqlalchemy import or_

class CoinNetwork(db.Model,SerializerMixin):
    id = db.Column(db.Integer, primary_key=True)
    coin_id = db.Column(db.Integer, db.ForeignKey('coin.id'))
    network_id = db.Column(db.Integer, db.ForeignKey('network.id'))

class Network(db.Model,SerializerMixin):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    explorer_url = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    symbol = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean, nullable=False)
    exchange_network_ticker = db.Column(db.String(255), nullable=False)

class Coin(db.Model,SerializerMixin):

    serialize_rules = ('-networks.coins',)

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
    networks = db.relationship('Network', secondary=CoinNetwork.__table__, backref='coins')

class Dump(db.Model,SerializerMixin):

    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(255), nullable=False)
    final_fiat_amount = db.Column(db.Float, nullable=True)
    dumped_at = db.Column(db.DateTime, nullable=True)
    fiat_currency = db.Column(db.String(255), nullable=True)
    exchange_trade_id = db.Column(db.String(255), nullable=True)

class Deposit(db.Model,SerializerMixin):

    serialize_rules = ('-coin.deposit','-coin.networks','-network.deposit','-network.coins','-dump')

    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(255), nullable=False)
    amount_generated_at = db.Column(db.DateTime, nullable=True)
    amount = db.Column(db.Numeric(18,8), nullable=True)
    confirmed_at = db.Column(db.DateTime, nullable=True)
    real_amount_received = db.Column(db.Numeric(18,8), nullable=True)
    deposit_address = db.Column(db.String(255), nullable=True)
    user_address = db.Column(db.String(255), nullable=True)
    blockchain_txid = db.Column(db.String(255), nullable=True)
    dump_id = db.Column(db.Integer, db.ForeignKey('dump.id'))
    dump = db.relationship('Dump', backref='deposit')
    coin_id = db.Column(db.Integer, db.ForeignKey('coin.id'))
    coin = db.relationship('Coin', backref='deposit')
    network_id = db.Column(db.Integer, db.ForeignKey('network.id'))
    network = db.relationship('Network', backref='deposit')
    
class Shop(db.Model,SerializerMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    api_key = db.Column(db.String(255), nullable=False)
    theme_customization = db.Column(JSON, nullable=False, default={})

class Transaction(db.Model,SerializerMixin):

    serialize_rules = ('-deposit.transaction','-shop.transaction')

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, nullable=False, default=tools.nowDatetimeUTC)
    expiry_at = db.Column(db.DateTime, nullable=True )
    hash = db.Column(db.String(255), unique=True, nullable=False)
    fiat_currency = db.Column(db.String(255), nullable=False)
    fiat_amount = db.Column(db.Numeric(10,2), nullable=False)
    real_fiat_received = db.Column(db.Numeric(10,2), nullable=True)
    product_id = db.Column(db.Integer, nullable=False)
    product_description = db.Column(db.String(255), nullable=False)
    shop_id = db.Column(db.Integer, db.ForeignKey('shop.id'))
    shop = db.relationship('Shop', backref='transaction')
    deposit_id = db.Column(db.Integer, db.ForeignKey('deposit.id'))
    deposit = db.relationship('Deposit', backref='transaction')

    def createTransaction(self):
        try:
            data = json.loads(request.data)
            
            expected_data = {
                "fiat_currency": data['fiat_currency'],
                "fiat_amount": data['fiat_amount'],
                "product_description": data['product_description'],
                "product_id": data['product_id'],
                "shop_api_key": data['shop_api_key'],
            }

            if data["fiat_amount"] < 10:
                return tools.JsonResp({"message": "minimum amount is 20"}, 400)

            txn_fingerprint = str(data['fiat_currency']) + str(data['fiat_amount']) + str(tools.nowDatetimeUTC()) + str(tools.randID())
            hs = hashlib.sha1(txn_fingerprint.encode('ascii'))
            hash = hs.hexdigest()

            shop = Shop.query.filter_by(api_key=expected_data['shop_api_key']).first()
            if shop is None:
                return tools.JsonResp({"message": "shop not found"}, 404)

            transaction = Transaction(
                hash=hash,
                expiry_at=tools.nowDatetimeUTC() + timedelta(hours=1),
                fiat_currency=expected_data['fiat_currency'].lower(),
                fiat_amount=expected_data['fiat_amount'],
                product_description=expected_data['product_description'],
                product_id=expected_data['product_id'],
                shop_id=shop.id
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
            amount = transaction.fiat_amount
            if transaction.real_fiat_received is None:
                amount = transaction.fiat_amount
            else:
                if transaction.real_fiat_received >= transaction.fiat_amount:
                    amount = transaction.fiat_amount
                else:
                    amount = transaction.real_fiat_received

            status = transaction.deposit.status

            data = {
                "hash": transaction.hash,
                "status": status,
                "amount": amount,
            }

            resp = tools.JsonResp({"message": "txn found", "data": data}, 200)
        except Exception as e:
            print(e)
            resp = tools.JsonResp({"message": "txn not found"}, 500)
            
        return resp

    def setDeposit(self, hash, ws_data=False):

        try:

            if ws_data:
                data = ws_data
            else:
                data = json.loads(request.data)
                
            expected_data = {
                "coin_id": data['coin_id'],
                "network_id": data['network_id'],
            }

            transaction = Transaction.query.filter_by(hash=hash).first()
            transaction.deposit.status = "initiated"
            
            transaction.deposit.deposit_address = Kraken().getDepositAddress(expected_data['coin_id'], expected_data['network_id'])
            transaction.deposit.amount = Kraken().getAmount(transaction.fiat_currency,transaction.fiat_amount,expected_data['coin_id'])
            transaction.deposit.amount_generated_at = tools.nowDatetimeUTC()
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
            transaction.deposit.amount_generated_at = tools.nowDatetimeUTC()
            db.session.commit()
            resp = tools.JsonResp({"message": "amount updated","data":{"amount":transaction.deposit.amount}}, 200)
        except Exception as e:
            print(e)
            resp = tools.JsonResp({"message": "amount not updated"}, 500)
            
        return resp

    def getCoins(self,hash):
        try:
            transaction = Transaction.query.filter_by(hash=hash).first()
            if transaction is None:
                return tools.JsonResp({"message": "txn not found"}, 500)
            coins = Coin.query.all()
            resp = tools.JsonResp({"message": "coins found","coins":coins}, 200)
        except Exception as e:
            print(e)
            resp = tools.JsonResp({"message": "coins not found"}, 500)
        return resp

    def getCoinNetworks(self,coin_id):
        try:
            coin = Coin.query.filter_by(id=coin_id).first()
            if coin is None:    
                return tools.JsonResp({"message": "coin not found"}, 500)
            resp = tools.JsonResp({"message": "networks found","networks":coin.networks}, 200)
        except Exception as e:
            print(e)
            resp = tools.JsonResp({"message": "networks not found"}, 500)
        return resp

    def getTransactionsToProcess(self):
        try:
            # get all transactions that are not expired and have deposit status pending or waiting
            transactions = Transaction.query.with_entities(Transaction.hash).filter(or_(Transaction.deposit.has(status="initiated"),Transaction.deposit.has(status="waitingconfirm"))).all()
            resp = tools.JsonResp({"message": "transactions found","transactions":transactions}, 200)
        except Exception as e:
            print(e)
            resp = tools.JsonResp({"message": "transactions not found"}, 500)
        return resp

    def getDumpToProcess(self):
        try:
            # get all transactions that are not expired and have deposit status pending or waiting
            transactions = Transaction.query.with_entities(Transaction.hash).filter(Transaction.deposit.has(status="confirmed")).filter(or_(Transaction.deposit.has(Deposit.dump.has(status="pending")),Transaction.deposit.has(Deposit.dump.has(status="pending")))).all()
            resp = tools.JsonResp({"message": "transactions found","transactions":transactions}, 200)
        except Exception as e:
            print(e)
            resp = tools.JsonResp({"message": "transactions not found"}, 500)
        return resp

from src.kraken.models import Kraken