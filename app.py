#!/usr/bin/env python

import urllib
import json
import os
import bsgenerator

from flask import Flask
from flask import request
from flask import make_response

# Flask app should start in global layout
app = Flask(__name__)


@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)

    print("Request:")
    print(json.dumps(req, indent=4))

    res = processRequest(req)

    res = json.dumps(res, indent=4)
    # print(res)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r

possibleActions = ["weatherAction","gregAction","chuckNorrisAction","jokeAction","bsAction"]

def processRequest(req):
    if req.get("result").get("action") not in possibleActions:
        return {}
    if req.get("result").get("action") == "weatherAction":
        return processWeatherRequest(req)
    if req.get("result").get("action") == "gregAction":
        return processGregRequest(req)
    if req.get("result").get("action") == "chuckNorrisAction":
        return processJokeRequest(req)
    if req.get("result").get("action") == "jokeAction":
        return processJokeRequest(req)
    if req.get("result").get("action") == "bsAction":
        return processBSRequest(req)

def processGregRequest(req):
    speech = "Yeah, this is a bit embarrassing, I'm not really sure yet what to do with your request.\nBut this is definitely coming from a webhook.\nSo technically it's working. Just so you know."
    return {
        "speech": speech,
        "displayText": speech,
        # "data": data,
        # "contextOut": [],
        "source": "apiai-gregsagent"
    }

def processBSRequest(req):
    #speech = "Never mind"
    speech = bsgenerator.generatePhrase()
    return {
        "speech": speech,
        "displayText": speech,
        # "data": data,
        # "contextOut": [],
        "source": "apiai-gregsagent via the BS Generator"
    }


def processWeatherRequest(req):
    baseurl = "https://query.yahooapis.com/v1/public/yql?"
    yql_query = makeYqlQuery(req)
    if yql_query is None:
        return {}
    yql_url = baseurl + urllib.urlencode({'q': yql_query}) + "&format=json"
    result = urllib.urlopen(yql_url).read()
    data = json.loads(result)
    res = makeWeatherWebhookResult(data)
    return res

def processJokeRequest(req):
    #check if name overriden or default Chuck Norris
    result = req.get("result")
    parameters = result.get("parameters")
    name = parameters.get("name")
    if name is None:
        name = 'Chuck Norris'
    
    baseurl = "http://api.icndb.com/jokes/random"
    result = urllib.urlopen(baseurl).read()
    data = json.loads(result)
    
    resp = data.get('type')
    if resp!="success":
        return {}
    joke = data.get('value').get('joke')

    #override name in joke (default: Chuck Norris)
    joke = joke.replace('Chuck Norris',name)
    if name != 'Chuck Norris': #otherwise the default becomes Chuck Chuck Norris
        joke = joke.replace('Chuck',name) #cases where only Chuck appears
    
    return {
        "speech": joke,
        "displayText": joke,
        # "data": data,
        # "contextOut": [],
        "source": "apiai-gregsagent"
    }
    
def makeYqlQuery(req):
    result = req.get("result")
    parameters = result.get("parameters")
    city = parameters.get("geo-city")
    if city is None:
        return None

    return "select * from weather.forecast where woeid in (select woeid from geo.places(1) where text='" + city + "')"


def makeWeatherWebhookResult(data):
    query = data.get('query')
    if query is None:
        return {}

    result = query.get('results')
    if result is None:
        return {}

    channel = result.get('channel')
    if channel is None:
        return {}

    item = channel.get('item')
    location = channel.get('location')
    units = channel.get('units')
    if (location is None) or (item is None) or (units is None):
        return {}

    condition = item.get('condition')
    if condition is None:
        return {}

    # print(json.dumps(item, indent=4))

    speech = "I don't know why you're asking me about the weather, but if you really want to know, today in " + location.get('city') + ": " + condition.get('text') + \
             ", the temperature is " + condition.get('temp') + " " + units.get('temperature') + " [webhook]"

    print("Response:")
    print(speech)

    return {
        "speech": speech,
        "displayText": speech,
        # "data": data,
        # "contextOut": [],
        "source": "apiai-gregsagent"
    }

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

    print "Starting app on port %d" % port

    app.run(debug=False, port=port, host='0.0.0.0')
