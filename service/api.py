#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from flask import Blueprint
from flask import current_app
from flask import request
from flask import jsonify
from datetime import datetime
from dateutil.relativedelta import relativedelta
import requests
import sys
import time
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

ONE_DAY = 24*60*60
HTTP_200_OK = 200
HTTP_400_BAD_REQUEST = 400
SLACK_API = 'https://slack.com/api/'
REACTION_RESOURCE = 'reactions.list'
CONVERSATION_LIST_RESOURCE = 'conversations.list'
CONVERSATION_HISTORY_RESOURCE = 'conversations.history'

v1api = Blueprint('v1', 'v1api')

# this is a really dumb channel list cache
channel_updated = 0
channels = set()
def update_channels():
    global channel_updated
    global channels
    if time.time() - channel_updated <= ONE_DAY:
        print ("Didn't update the channel cache")
        return
    channel_updated = time.time()
    url = SLACK_API + CONVERSATION_LIST_RESOURCE
    bearer = current_app.config["SLACK_BEARER"]
    headers = { 'Authorization':  'Bearer ' + bearer } 
    try:
        r = requests.get(url, headers=headers)
        body = r.json()
        items = body["channels"]
        for channel in items:
            channels.add(channel["id"])
    except:
        print("failed to update channel list")

@v1api.route('/status', methods=['GET'])
def get_status():
    return jsonify('OK'), HTTP_200_OK

@v1api.route('/getSentiment', methods=['GET'])
def get_sentiment():
    global channels
    update_channels()

    timeframe = request.args.get("timeframe", "months")
    num_timeframes = datetime.today().hour if timeframe == "day" else request.args.get('num', '3')
    timeframes = get_timeframes(timeframe, int(num_timeframes))
        
    url = SLACK_API + CONVERSATION_HISTORY_RESOURCE
    bearer = current_app.config["SLACK_BEARER"]
    headers = { 'Authorization':  'Bearer ' + bearer } 

    sentiment_analyzer = SentimentIntensityAnalyzer()
    result = []

    try:
        for timeframe in timeframes:
            msg_count, pos, neg, neu, avg = 0, 0, 0, 0, 0
            for channel in channels:
                request_body = {
                    'channel': channel,
                    'oldest': str(timeframe[2].timestamp()),
                    'latest': str(timeframe[1].timestamp())
                }
                r = requests.post(url, data=request_body, headers=headers)
                body = r.json()
                # print(body)
                for message in body["messages"]:
                    msg_count += 1
                    score = sentiment_analyzer.polarity_scores(message["text"])['compound']
                    avg += score
                    if score > 0:
                        pos += 1
                    elif score < 0:
                        neg += 1
                    else:
                        neu += 1
                    # print(message["text"] + " has a score: " + str(sentiment_analyzer.polarity_scores(message["text"])))
                if msg_count > 0:
                    avg = (avg * 100) / msg_count
                #TODO: months of years? 
            result.append((timeframe[0], {"pos": pos, "neg": neg, "neu": neu, "avg": avg}))
    except KeyError:
        print("yeah i probably messed up")
        return jsonify({}), HTTP_400_BAD_REQUEST 
    except:
        print("Bad request", sys.exc_info()[0])
        return jsonify({}), HTTP_400_BAD_REQUEST
    
    return jsonify(result), HTTP_200_OK

def get_timeframes(timeframe, num_timeframes):
    intervals = []
    latest = datetime.today()
    oldest = datetime.today()
    label = ""
    for i in range (num_timeframes):
        if (timeframe == "months"):
            if (latest.day != 1):
                oldest = latest.replace(day=1)
            else:
                oldest -= relativedelta(months=1)
            label = oldest.strftime("%b")
        if (timeframe == "weeks"):
            oldest -= relativedelta(weekday=6)
            oldest -= relativedelta(weeks=1)
            label = oldest.strftime("%m/%d/%Y") + " - " + latest.strftime("%m/%d/%Y")
        if (timeframe == "day"):
            oldest -= relativedelta(hours=1)
            label = latest.strftime("%H")
        intervals.append((label, latest, oldest))
        latest = oldest
    # print(intervals)
    return intervals

# ARGS:
#      n_months - number of months to go back and retrieve messages
#               - Int, default 3
@v1api.route('/getMessageCount', methods=['GET', 'POST'])
def get_message_count():
    global channels
    update_channels()
    
    timeframe = request.args.get("timeframe", "months")
    num_timeframes = datetime.today().hour if timeframe == "day" else request.args.get('num', '3')
    timeframes = get_timeframes(timeframe, int(num_timeframes))

    url = SLACK_API + CONVERSATION_HISTORY_RESOURCE
    bearer = current_app.config["SLACK_BEARER"]
    headers = { 'Authorization':  'Bearer ' + bearer } 

    messages = dict()   # dict of month number to num messages (0 is cur month)
    try:
        for timeframe in timeframes:
            for channel in channels:
                request_body = {
                    'channel': channel,
                    'oldest': str(timeframe[2].timestamp()),
                    'latest': str(timeframe[1].timestamp())
                }
                r = requests.post(url, data=request_body, headers=headers)
                body = r.json()
                # print(body)
                if timeframe[0] not in messages:
                    messages[timeframe[0]] = 0
                messages[timeframe[0]] += len(body["messages"])
    except KeyError:
        print("yeah i probably messed up")
        return jsonify({}), HTTP_400_BAD_REQUEST 
    except:
        print("Bad request", sys.exc_info()[0])
        return jsonify({}), HTTP_400_BAD_REQUEST
    return jsonify(messages), HTTP_200_OK

@v1api.route('/getMessageTypes', methods=['GET'])
def get_message_types():
    global channels
    update_channels()
    
    timeframe = request.args.get("timeframe", "months")
    num_timeframes = datetime.today().hour if timeframe == "day" else request.args.get('num', '3')
    timeframes = get_timeframes(timeframe, int(num_timeframes))
        
    url = SLACK_API + CONVERSATION_HISTORY_RESOURCE
    bearer = current_app.config["SLACK_BEARER"]
    headers = { 'Authorization':  'Bearer ' + bearer } 

    result = []

    try:
        for timeframe in timeframes:
            files, links, text = 0, 0, 0
            for channel in channels:
                request_body = {
                    'channel': channel,
                    'oldest': str(timeframe[2].timestamp()),
                    'latest': str(timeframe[1].timestamp())
                }
                r = requests.post(url, data=request_body, headers=headers)
                body = r.json()
                # print(body)
                for message in body["messages"]:
                    # print(message)
                    if "blocks" in message:
                        for blocks in message["blocks"]:
                            for message_elements in blocks["elements"]:
                                for element in message_elements["elements"]:
                                    if element["type"] == "link":
                                        links += 1
                                    elif element["type"] == "text":
                                        text += 1
                    elif "files" in message:
                        files += 1
            result.append((timeframe[0], {"text": text, "links": links, "files": files}))
    except KeyError:
        print("yeah i probably messed up")
        return jsonify({}), HTTP_400_BAD_REQUEST 
    except:
        print("Bad request", sys.exc_info()[0])
        return jsonify({}), HTTP_400_BAD_REQUEST
    
    return jsonify(result), HTTP_200_OK

@v1api.route('/getReactionsCount', methods=['GET'])
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
