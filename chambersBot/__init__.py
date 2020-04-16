import requests
from bottle import run, post, response, request as bottleReq
from pyngrok import ngrok
from . import settings

#URL of bot which was created.
BOT_URL = settings.BOT_URL
PRODUCTION_MODE = settings.PRODUCTION_MODE
HOST_URL = settings.HOST_URL

#NGROK is used to redirect Telegram API webhooks to localhost.
def init():
	if PRODUCTION_MODE:
		setWH = BOT_URL + "setWebHook?url=" + HOST_URL + "/chambersBot/receive/" #webhooks sent to localhost:8000/testBot/receive
		requests.get(setWH) #sends get to telegram webhook to initialize ngrok <-> telegram link
	else:
		ngrok.kill() #kill existing NGROK process on localhost if any
		pubURL = ngrok.connect(8000) #connect NGROK to port 8000
		pubURL = pubURL.replace("http://","https://",1) #change pubURL string to SSL secured
		print("Public URL created at " + pubURL)
		setWH = BOT_URL + "setWebHook?url=" + pubURL + "/chambersBot/receive/" #webhooks sent to localhost:8000/testBot/receive
		requests.get(setWH) #sends get to telegram webhook to initialize ngrok <-> telegram link
	
	#contents = requests.get(BOT_URL + "getWebhookInfo")
	#print(contents.content)

init()