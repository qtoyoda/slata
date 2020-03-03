#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from flask import Blueprint
from flask import current_app
from flask import request
from flask import jsonify
import requests
import sys

HTTP_200_OK = 200
HTTP_400_BAD_REQUEST = 400
SLACK_API = 'https://slack.com/api/'
REACTION_RESOURCE = 'reactions.list'

v1api = Blueprint('v1', 'v1api')

@v1api.route('/status', methods=['GET'])
def get_status():
    return jsonify('OK'), HTTP_200_OK

@v1api.route('/getReactionsCount')
def get_reactions():
    url = SLACK_API + REACTION_RESOURCE
    bearer = current_app.config["SLACK_BEARER"]
    headers = { 'Authorization':  'Bearer ' + bearer }

    react_count = dict()
    try:
        r = requests.get(url, headers=headers)
        body = r.json()
        items = body["items"]
        for item in items:
            for reaction in item["message"]["reactions"]:
                react = reaction["name"]
                if not react in react_count:
                    react_count[react] = 0
                react_count[react] += reaction["count"]
    except KeyError:
        print("yeah i probably messed up")
        return jsonify({}), HTTP_400_BAD_REQUEST 
    except:
        print("Bad request", sys.exc_info()[0])
        return jsonify({}), HTTP_400_BAD_REQUEST
    return jsonify(react_count), HTTP_200_OK
