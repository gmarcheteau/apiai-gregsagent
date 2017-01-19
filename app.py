#!/usr/bin/env python

import urllib
import json
import os
import random
import ArtyFarty.bsgenerator as bs
import ArtyFarty.bsgenerator_en as bs_en
import ArtyFarty.imageapp as imageapp

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

possibleActions = ["weatherAction","gregAction","chuckNorrisAction","jokeAction","bsAction","startGameAction","provideClueAction","finishGameAction"]

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
    if req.get("result").get("action") == "startGameAction":
        return startGame(req)
    if req.get("result").get("action") == "provideClueAction":
        return returnGuess(req)
    if req.get("result").get("action") == "finishGameAction":
        return finishGame(req)

###prototype support for Tacotac agent-----###
###to be moved to proper project-----------###
def startGame(req):
    #if clue already provided, return guess
    if req.get("result").get("parameters").get("clue"):
        return returnGuess(req)

def wrongGuess(req):
    return returnGuess(req)

def correctGuess(req):
    #no bragging, simply triggering event
    bragging = ''
    response = {
        "speech": bragging,
            "displayText": bragging,
            "contextOut": [
                {
                    "name":"gameWonContext",
                    "lifespan":20,
                    "parameters":{"score":"289"}
                }],
            "source": "apiai-gregsagent for Tactotaac"
        }
    return response

def returnGuess(req):
    if req.get("result").get("parameters").get("score"):
        score = int(req.get("result").get("parameters").get("score"))
        score -= 1
        print "new score -- %d" %score
    else:
        print "no score found - setting to 0"
        score = 20
    clue=req.get("result").get("parameters").get("clue")
    guesses = ["flower","beef", "beer", "table", "car", "house", "Trump"]
    rand = random.randint(0,len(guesses)-1)
    guess = guesses[rand]
    speech = guess + "?"
    response = {
        "speech": speech,
        "displayText": speech,
        "contextOut": [
            {
                "name":"playing_context",
                "lifespan":20,
                "parameters":{
                    "guess":guess,
                    "score":score
                }
            }],
        "source": "apiai-gregsagent for Tactotaac"
    }
    return response

def finishGame(req):
    #get all stats
    try:
        score = int(req.get("result").get("parameters").get("score"))
        guess = req.get("result").get("parameters").get("guess")
        print "Game has ended:"
        print "Score: %d - The word to guess was %s" %(score,guess)
        
        response = {
            "contextOut": [
                {
                    "name":"gamestats_context",
                    "lifespan":20,
                    "parameters":{
                        "game_number":99,
                        "last_score":score
                    }
                }],
            "source": "apiai-gregsagent for Tactotaac"
        }
        return response

    except Exception as err:
        print "Error in finishGane -- %s" %str(err)
        return {}
    
    #curl -H "Content-Type: application/json; charset=utf-8" -H "Authorization: Bearer 92ba3f511fd44f158adf3df2178edf70" --data "{'event':{ 'name': 'gameWonEvent', 'data':{'score': 299}, 'lifespan': 4},'lang':'en', 'sessionId':'1234567890'}" "https://api.api.ai/v1/query?v=20150910"
###---------------------------------------###
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
    speech = bs_en.generatePhrase()
    speech += " https://artyfarty.herokuapp.com"
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
    
    #correct issue with quotes &quot;
    joke = joke.replace('&quot;','\'')

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

@app.route('/getbs', methods=['GET'])
def getBS():
  return "<p>"+bs.generatePhrase()+"</p>"

@app.route('/getbs_en', methods=['GET'])
def getBS_en():
  return "<p>"+bs_en.generatePhrase()+"</p>"

@app.route('/getbs_img', methods=['GET'])
def getBS_img():
  imageurl = request.args.get('imageurl')
  defaultURL = "http://www.telegraph.co.uk/content/dam/art/2016/10/04/picasso-large_trans++qVzuuqpFlyLIwiB6NTmJwbKTcqHAsmNzJMPMiov7fpk.jpg"
  if not imageurl:
    imageurl = defaultURL
  #remove quotes in url if any
  imageurl = imageurl.strip('"').strip('\'')
  if not imageurl.startswith("http"):
    imageurl = defaultURL
  
  #get data from image comment (comment, colors, drawn colors)
  imageresponse = imageapp.commentOnImage(imageurl)
  imagecomment = imageresponse["comment"]
  maincolors = imageresponse["colors"]
  print type(imageresponse)
  print type(imagecomment)
  print type(maincolors)
  
  #build html response
  response = ''
  response += "<h2>Artomatic 2000</h2>"
  response += "<img src=\""+imageurl+"\" alt=\"target pic\" />"
  response += "<p>"+imagecomment+"</p>"
  response += "<p><a href="+imageurl+">Source image</a></p>"
  response += "<p><i>Ask for a comment on a specific image using the imageurl parameter, adding ?imageurl=[your image url] to this page\'s url, e.g. try <a href=\"?imageurl=http://4.bp.blogspot.com/-se2NiVM6Ifw/VZPOXwYD3VI/AAAAAAAAIDo/_dDgrAfvanU/s1600/Rothko.jpg\">this image</a> or <a href=\"?imageurl=https://encrypted-tbn2.gstatic.com/images?q=tbn:ANd9GcRzYpcdAshr9xLfSwONO4Oku7bXXQ0RJ1LnZAtqAieDyNmqqpRbvA\">this one</a></i></p>"
  #response += "<div style=\"width:500px;height:100px;border:0px solid #000;background-color:rgb"+str(maincolors[0][0])+";\">Main color</div>"
  
  #TODO: getting image from local, saved in clustercolors.py, not working.
  #response += "<img src=\"colorboxes.png\" alt=\"main colors\" />"
  
  return response

@app.route("/simple.png")
def simple():
    import datetime
    import StringIO
    import random

    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    from matplotlib.figure import Figure
    from matplotlib.dates import DateFormatter

    fig=Figure()
    ax=fig.add_subplot(111)
    x=[]
    y=[]
    now=datetime.datetime.now()
    delta=datetime.timedelta(days=1)
    for i in range(10):
        x.append(now)
        now+=delta
        y.append(random.randint(0, 1000))
    ax.plot_date(x, y, '-')
    ax.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
    fig.autofmt_xdate()
    canvas=FigureCanvas(fig)
    png_output = StringIO.StringIO()
    canvas.print_png(png_output)
    response=make_response(png_output.getvalue())
    response.headers['Content-Type'] = 'image/png'
    return response


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

    print "Starting app on port %d" % port

    app.run(debug=False, port=port, host='0.0.0.0')
