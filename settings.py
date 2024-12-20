import os
from dotenv import load_dotenv

if os.environ.get("FLASK_ENV") == "development":
    load_dotenv("./.env")
    print("Loading .env file")

SECRET_KEY=os.environ['SECRET_KEY']
DB_USERNAME=os.environ['DB_USERNAME']
DB_PASSWORD=os.environ['DB_PASSWORD']
DB_HOST=os.environ['DB_HOST']
DATABASE_NAME=os.environ['DATABASE_NAME']
DB_URI = f"mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:3306/{DATABASE_NAME}"
SQLALCHEMY_DATABASE_URI = DB_URI
SQLALCHEMY_TRACK_MODIFICATIONS = True
SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
}
FRONTEND_DOMAIN = os.environ['FRONTEND_DOMAIN']
SOCKETIO_HOST = os.environ['SOCKETIO_HOST']
SOCKETIO_PORT = os.environ['SOCKETIO_PORT']

