#!/bin/bash

if [ ! -d "venv" ]; then
    echo "please be running in a venv with python3..."
    echo "install venv with python3 then run:"
    echo "python3 -m venv venv"
    echo "source venv/bin/activate"
    exit 1
fi

# will update if already installed so ¯\_(ツ)_/¯
pip install Flask
pip install requests

export SECRETS_CONFIG=config/secrets.cfg
echo "starting app..."
service/app.py