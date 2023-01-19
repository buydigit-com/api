from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_socketio import SocketIO

# setup db
db = SQLAlchemy()
socketio = SocketIO()

def create_app(**config_overrides):
    app = Flask(__name__)

    # Load config
    app.config.from_pyfile('settings.py')

    # apply overrides for tests
    app.config.update(config_overrides)

    cors = CORS(app,supports_credentials=True, resources={  r"/*": { "origins": app.config["FRONTEND_DOMAIN"] }})
    # initialize db
    db.init_app(app)
    migrate = Migrate(app, db)

    # initialize socketio
    

    # import blueprints
    from src.gateway.routes import gateway_blueprint
    from src.kraken.routes import kraken_blueprint

    
    # register blueprints
    from src.gateway import wsnode
    app.register_blueprint(gateway_blueprint, url_prefix="/gateway")
    app.register_blueprint(kraken_blueprint, url_prefix="/kraken")
    socketio.init_app(app,cors_allowed_origins="*", async_mode="eventlet", logger=True, engineio_logger=True)
    return app
