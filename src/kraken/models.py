from application import db
from src.utils import tools
import time
import json,random
import hashlib
import threading
from flask import request
import krakenex
from src.gateway.models import Coin,Network,Transaction
from datetime import datetime
from application import socketio
from sqlalchemy import or_

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

    def getCoinPrice(self,fiat_currency,coin_id):
        exchange_coin_fiat_ticker = getattr(Coin().query.filter_by(id=coin_id).first(),f"exchange_{fiat_currency}_pair_ticker")
        session = self.getSession()
        data = session.query_public('Ticker',{'pair':exchange_coin_fiat_ticker})
        print(data)
        self.closeSession(session)
        return float(data["result"][exchange_coin_fiat_ticker]["c"][0])

    def getAmount(self,fiat_currency,fiat_amount,coin_id):
        exchange_coin_decimals = Coin().query.filter_by(id=coin_id).first().decimals



        unique_amount = False
        try:
            coin_amount = str(round(fiat_amount / self.getCoinPrice(fiat_currency=fiat_currency,coin_id=coin_id),exchange_coin_decimals))
            if (len(str(coin_amount).split(".")[1]) < exchange_coin_decimals):
                coin_amount = format(float(coin_amount),f".{exchange_coin_decimals}f")
            coin_amount = list(coin_amount)
            coin_amount[-1] = str(random.randint(1,9))
            coin_amount[-2] = str(random.randint(1,9))
            coin_amount[-3] = str(random.randint(1,9))
            coin_amount[-4] = str(random.randint(1,9))
            unique_amount = "".join(coin_amount)
        except Exception as e:
            print(e)
            unique_amount = False
        return unique_amount

    def checkKrakenDeposit(self,hash):

        transaction = Transaction().query.filter_by(hash=hash).first()
        if transaction.deposit.status == "pending":
            resp = tools.JsonResp({"status":"not-checked","message":"deposit stillpending"},200)
            return resp

        exchange_coin_ticker = Coin().query.filter_by(id=transaction.deposit.coin_id).first().exchange_coin_ticker
        exchange_network_ticker = Network().query.filter_by(id=transaction.deposit.network_id).first().exchange_network_ticker

        if transaction.deposit.status == "confirmed" or transaction.deposit.status == "failed":
            resp = tools.JsonResp({"status":"already-checked","message":"deposit already checked"},200)
            return resp

        session = self.getSession()
        data = session.query_private('DepositStatus',{'asset':exchange_coin_ticker,'method':exchange_network_ticker})
        self.closeSession(session)
        if "result" not in data:
            resp = tools.JsonResp({"status":"error","message":"Kraken API error"},500)
        else:
            right_deposit = None
            resp = tools.JsonResp({"status":"not-found","message":"deposit not found"},200)


            print(data["result"])
            for deposit in data["result"]:
                if float(deposit["amount"]) == float(transaction.deposit.amount) and datetime.fromtimestamp(deposit["time"]) >= transaction.created_at:
                    right_deposit = deposit
                    break
                    
                
    
            if right_deposit is not None:
                
                if right_deposit["status"] == "Success":

                    if (datetime.fromtimestamp(right_deposit["time"]) - transaction.deposit.amount_generated_at).total_seconds() > 60:
                        print("TIME DIFFERENCE")
                        real_fiat_received = self.getCoinPrice(transaction.fiat_currency,transaction.deposit.coin_id) * float(right_deposit["amount"])
                        transaction.real_fiat_received = real_fiat_received

                    else:
                        transaction.real_fiat_received = transaction.fiat_amount

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
                #transaction.deposit.user_address = right_deposit["info"]
            

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
        print("DUMPING TO FIAT",hash)
        try:
            transaction = Transaction().query.filter_by(hash=hash).first()
            exchange_coin_fiat_ticker = getattr(Coin().query.filter_by(id=transaction.deposit.coin_id).first(),f"exchange_eur_pair_ticker")
            exchange_coin_decimals = Coin().query.filter_by(id=transaction.deposit.coin_id).first().decimals
            print(transaction.deposit.amount)
            



            
            session = self.getSession()
            #volume = session.query_private('Balance')['result'][Coin().query.filter_by(id=transaction.deposit.coin_id).first().exchange_coin_ticker]
            data = session.query_private('AddOrder',{'pair':exchange_coin_fiat_ticker,'type':'sell','ordertype':'market','volume':float(transaction.deposit.amount)})
            self.closeSession(session)
            print(data)
            if "result" not in data:
                print("Kraken API error")
                return tools.JsonResp({"status":"error","message":"Kraken API error"},500)
            

            exchange_trade_id = data["result"]["txid"][0]

        except Exception as e:
            print(e)
            return tools.JsonResp({"status":"error","message":"Kraken API error"},500)

        #fiat_amount = round(float(transaction.deposit.amount) * float(data["result"][exchange_coin_fiat_ticker]["c"][0]),2)

        transaction.deposit.dump.status = "confirmed"
        transaction.deposit.dump.fiat_currency = exchange_coin_fiat_ticker
        #transaction.deposit.dump.final_fiat_amount = fiat_amount
        transaction.deposit.dump.exchange_trade_id = exchange_trade_id

        db.session.commit()

        return tools.JsonResp({"status":"confirmed","message":"Dumped!"},200)

    def dump_cron(self):
        print("DUMPING TO FIAT")
        try:
            session = self.getSession()
            coins = session.query_private('Balance')['result']
            print(coins)
            for coin in coins:
                if coin == "ZEUR" or coin == "ZUSD":
                    continue
                try:
                    coin_db = Coin.query.filter(or_(
                        Coin.exchange_coin_ticker.like(f'%{coin}%'),
                        Coin.exchange_eur_pair_ticker.like(f'%{coin}%'),
                        Coin.exchange_usd_pair_ticker.like(f'%{coin}%'),
                        Coin.exchange_btc_pair_ticker.like(f'%{coin}%')
                    )).first()
                    exchange_coin_fiat_ticker = coin_db.exchange_eur_pair_ticker
                    print(exchange_coin_fiat_ticker)
                    eur = self.getCoinPrice("eur", coin_db.id) * float(coins[coin])
                    print(eur)
                    if eur >= 5:
                        data = session.query_private('AddOrder',{'pair':exchange_coin_fiat_ticker,'type':'sell','ordertype':'market','volume':float(coins[coin])})
                        print(data)
                        if "result" not in data:
                            print("Kraken API error")
                except Exception as e:
                    print(e)
                    continue
            self.closeSession(session)

        except Exception as e:
            print(e)
            return tools.JsonResp({"status":"error","message":"Kraken API error"},500)

        return tools.JsonResp({"status":"confirmed","message":"Dumped!"},200)