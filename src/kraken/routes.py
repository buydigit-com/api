from flask import Blueprint

from application import db
from src.kraken.models import Kraken
from src.utils.middleware import cron_required

kraken_blueprint = Blueprint("kraken", __name__)

@kraken_blueprint.route("/check-kraken-deposit/<hash>", methods=["GET"])
@cron_required
def checkKrakenDeposit(hash):
    return Kraken().checkKrakenDeposit(hash)

@kraken_blueprint.route("/dump-to-fiat/<hash>", methods=["GET"])
@cron_required
def dumpToFiat(hash):
    return Kraken().dumpToFiat(hash)