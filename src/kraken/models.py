from application import db
from src.utils import tools
import json,random
import hashlib
from flask import request
import krakenex
from src.gateway.models import Coin,Network,Transaction
from datetime import datetime
from application import socketio
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
            resp = tools.JsonResp({"status":"not-found","message":"deposit not found"},200)
            for deposit in data["result"]:
                if float(deposit["amount"]) == transaction.deposit.amount and deposit["info"] == transaction.deposit.deposit_address and datetime.fromtimestamp(deposit["time"]) >= transaction.created_at:
                    print(deposit)
                    right_deposit = deposit
                    break
            
            right_deposit = {
                "status":"Success",
                "amount":0.0001,
                "txid":"0x0000000000000000000"
            }

            if right_deposit is not None:
                print(deposit)
                if right_deposit["status"] == "Success":
                    resp = tools.JsonResp({"status":"Success","message":"Transaction found"},200)
                    status = "confirmed"
                    transaction.deposit.confirmed_at = tools.nowDatetimeUTC()
                elif right_deposit["status"] == "Settled":
                    resp = tools.JsonResp({"status":"Settled","message":"Transaction pending"},200)
                    status = "waitingconfirm"
                elif right_deposit["status"] == "Failure":
                    resp = tools.JsonResp({"status":"Failure","message":"Transaction Failure"},200)
                    status = "failed"

                transaction.deposit.status = status
                transaction.deposit.real_amount_received = right_deposit["amount"]
                transaction.deposit.blockchain_txid = right_deposit["txid"]
            

                db.session.commit()

                socketio.emit(transaction.hash, tools.SocketResp(transaction.to_dict()))


        
        return resp

    def loadData(self):
        data = json.loads(request.data)
        for coin in data:
            db_coin = Coin(
                name=coin["altname"],
                description=coin["altname"],
                symbol=coin["altname"],
                decimals=coin["decimals"],
                exchange_coin_ticker=coin["altname"],
                exchange_btc_pair_ticker=f"XBT{coin['altname']}",
                exchange_eur_pair_ticker=f"{coin['altname']}EUR",
                exchange_usd_pair_ticker=f"{coin['altname']}USD",
                active=True,
            )

            for network in coin["deposit_methods"]:
                network = Network(
                    name=network["method"],
                    description=network["method"],
                    exchange_network_ticker=network["method"],
                    symbol=network["method"],
                    active=True,
                    explorer_url="https://ether",
                )
            
                db_coin.networks.append(network)

            db.session.add(db_coin)
            db.session.commit()
                

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