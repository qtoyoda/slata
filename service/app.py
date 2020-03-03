#!/usr/bin/env python3
import api
import json

from flask import Flask
from flask import jsonify

# We need to fix some constants, tho could be passed in as args
SERVICE_CONFIG = 'config.json'

def create_app():
    """ Function that initialises the application from the config. """
    _app = Flask(__name__)

    # _app.config.from_object('yourapplication.default_settings')
    _app.config.from_envvar('SECRETS_CONFIG')
    _app.service_config = {}
    return _app

if __name__ == '__main__':
    app = create_app()
    app.register_blueprint(api.v1api, url_prefix='/v1')
    app.run(host="0.0.0.0", port=5000)