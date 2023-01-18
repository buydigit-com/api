from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# setup db
db = SQLAlchemy()

def create_app(**config_overrides):
    app = Flask(__name__)

    # Load config
    app.config.from_pyfile('settings.py')

    # apply overrides for tests
    app.config.update(config_overrides)

    # initialize db
    db.init_app(app)
    migrate = Migrate(app, db)

    # import blueprints
    from src.gateway.routes import gateway_blueprint
    from src.kraken.routes import kraken_blueprint

    # register blueprints
    app.register_blueprint(gateway_blueprint, url_prefix="/gateway")
    app.register_blueprint(kraken_blueprint, url_prefix="/kraken")

    return app
