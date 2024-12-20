#!/usr/bin/env python3.6


import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from application import create_app, socketio
app = create_app()

if __name__ == "__main__":
    socketio.run(app, debug=True, use_reloader=True,host="api.buydigit.com",port="5000")
