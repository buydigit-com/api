from flask import Blueprint

from application import db
from src.gateway.models import Transaction
from src.utils.middleware import isMerchant,api_required

gateway_blueprint = Blueprint("gateway", __name__)



@gateway_blueprint.route("/transaction", methods=["PUT"])
@api_required
@isMerchant
def createTransaction():
	return Transaction().createTransaction()


@gateway_blueprint.route("/transaction/<hash>", methods=["GET"])
@api_required
@isMerchant
def getTransaction(hash):
    return Transaction().getTransaction(hash)

@gateway_blueprint.route("/set-deposit/<hash>", methods=["POST"])
def setDeposit(hash):
    return Transaction().setDeposit(hash)

@gateway_blueprint.route("/update-amount/<hash>", methods=["GET"])
def updateAmount(hash):
    return Transaction().updateAmount(hash)

@gateway_blueprint.route("/coins/<hash>", methods=["GET"])
def getCoins(hash):
    return Transaction().getCoins(hash)

@gateway_blueprint.route("/coins/<id>/networks", methods=["GET"])
def getCoinNetworks(id):
    return Transaction().getCoinNetworks(id)

