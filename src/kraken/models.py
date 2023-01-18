from application import db
from src.utils import tools
import json,random
import hashlib
from flask import request
import krakenex
from src.gateway.models import Coin,Network,Transaction
from datetime import datetime
class Kraken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean, nullable=False)
    key = db.Column(db.String(255), nullable=False)
    secret = db.Column(db.String(255), nullable=False)

    def getSession(self):
        k = krakenex.API(key=Kraken.query.filter_by(active=True).first().key,secret=Kraken.query.filter_by(active=True).first().secret)
        return k
    
    def closeSession(self,session):
        session.close()
        del session
        return True

    def getDepositAddress(self,coin_id,network_id):

        exchange_coin_ticker = Coin().query.filter_by(id=coin_id).first().exchange_coin_ticker
        exchange_network_ticker = Network().query.filter_by(id=network_id).first().exchange_network_ticker

        session = self.getSession()
        data = session.query_private('DepositAddresses',{'asset':exchange_coin_ticker,'method':exchange_network_ticker})
        self.closeSession(session)

        random_wallet = None
        try:
            random_wallet = random.choice(data["result"])["address"]
        except:
            session = self.getSession()
            data = session.query_private('DepositAddresses',{'asset':exchange_coin_ticker,'method':exchange_network_ticker,"new":True})
            self.closeSession(session)
            try:
                random_wallet = random.choice(data["result"])["address"]
            except:
                random_wallet = "NOT_AVAILABLE"

        return random_wallet

    def getAmount(self,fiat_currency,fiat_amount,coin_id):
        exchange_coin_fiat_ticker = getattr(Coin().query.filter_by(id=coin_id).first(),f"exchange_{fiat_currency}_pair_ticker")
        exchange_coin_decimals = Coin().query.filter_by(id=coin_id).first().decimals

        session = self.getSession()
        data = session.query_public('Ticker',{'pair':exchange_coin_fiat_ticker})
        self.closeSession(session)

        unique_amount = False
        try:
            coin_amount = str(round(fiat_amount / float(data["result"][exchange_coin_fiat_ticker]["c"][0]),exchange_coin_decimals))
            if (len(str(coin_amount).split(".")[1]) < exchange_coin_decimals):
                coin_amount = format(float(coin_amount),f".{exchange_coin_decimals}f")
            coin_amount = list(coin_amount)
            coin_amount[-1] = str(random.randint(1,9))
            coin_amount[-2] = str(random.randint(1,9))
            coin_amount[-3] = str(random.randint(1,9))
            unique_amount = "".join(coin_amount)
        except Exception as e:
            print(e)
            unique_amount = False
        return unique_amount

    def checkKrakenDeposit(self,hash):

        transaction = Transaction().query.filter_by(hash=hash).first()
        exchange_coin_ticker = Coin().query.filter_by(id=transaction.deposit.coin_id).first().exchange_coin_ticker
        exchange_network_ticker = Network().query.filter_by(id=transaction.deposit.network_id).first().exchange_network_ticker

        session = self.getSession()
        data = session.query_private('DepositStatus',{'asset':exchange_coin_ticker,'method':exchange_network_ticker})
        self.closeSession(session)


        if "result" not in data:
            resp = tools.JsonResp({"status":"error","message":"Kraken API error"},500)
        else:
            right_deposit = None
            resp = tools.JsonResp({"status":"not-found","message":"Transaction not found"},200)
            for deposit in data["result"]:
                if deposit["amount"] == transaction.deposit.amount and deposit["info"] == transaction.deposit.address and datetime.fromtimestamp(deposit["time"]) >= transaction.deposit.created_at:
                    print(deposit)
                    right_deposit = deposit
                    break
            
            if right_deposit is not None:
                print(deposit)
                if deposit["status"] == "Success":
                    resp = tools.JsonResp({"status":"Success","message":"Transaction found"},200)
                elif deposit["status"] == "Settled":
                    resp = tools.JsonResp({"status":"Settled","message":"Transaction pending"},200)
                elif deposit["status"] == "Failure":
                    resp = tools.JsonResp({"status":"Failure","message":"Transaction Failure"},200)
                
                transaction.deposit.status = right_deposit["status"]
                transaction.deposit.real_amount_sent = right_deposit["amount"]
                transaction.deposit.blockchain_tx_id = right_deposit["txid"]

                db.session.commit()

        
        return resp

    def dumpToFiat(self,hash):

        transaction = Transaction().query.filter_by(hash=hash).first()
        exchange_coin_fiat_ticker = getattr(Coin().query.filter_by(id=transaction.deposit.coin_id).first(),f"exchange_{transaction.fiat_currency}_pair_ticker")
        exchange_coin_decimals = Coin().query.filter_by(id=transaction.deposit.coin_id).first().decimals

        session = self.getSession()
        data = session.query_private('AddOrder',{'pair':exchange_coin_fiat_ticker,'type':'sell','ordertype':'market','volume':transaction.deposit.amount})
        self.closeSession(session)

        try:
            fiat_amount = round(float(transaction.deposit.amount) * float(data["result"][exchange_coin_fiat_ticker]["c"][0]),2)
        except:
            fiat_amount = False

        return fiat_amount