from django.shortcuts import render
from . import settings

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

import json
import requests
import string
import heapq

import threading
import time
from queue import PriorityQueue
import hashlib
from . import models as chamberBot_models


#settings import
BOT_URL = settings.BOT_URL
MASTER_CHAT_ID = settings.MASTER_CHAT_ID
OUTPUT_ID = settings.OUTPUT_ID
FRONT_URL = settings.FRONT_URL

"""
For website to connect to the backend/database.
CSRF exempt for now, although it is possible to add and allow authentication.
"""
@csrf_exempt
def connect(request):
	data = json.loads(request.body)

	if data['action']=='login':
		return attemptLogin(data)
	elif data['action']=='delete':
		return attemptDelete(data)
	elif data['action']=='clear':
		return attemptClear(data)
	
# Clear all current jobs
def attemptClear(data):
	#json received should contain 'code' field. check if code is valid
	if not chamberBot_models.Code.objects.filter(code=data['code']).exists():
		return generateJson({'success': False})
	#if code is valid, delete
	id_chat = chamberBot_models.Code.objects.get(code=data['code'])
	clearJobs(id_chat.chat_id)
	return generateJson({'success': True})
	
# Delete specific reminder
def attemptDelete(data):
	#json received should contain 'code' field. check if code is valid
	if not chamberBot_models.Code.objects.filter(code=data['code']).exists():
		return generateJson({'success': False}) #returns success whether or not deleted

	#if code is valid, delete
	id_chat = chamberBot_models.Code.objects.get(code=data['code'])
	chamberBot_models.Reminder.objects.filter(chat_id=id_chat,id=rid).delete()
	return generateJson({'success': True}) #returns success whether or not deleted

# Attempt to login from chambers page to access reminders
def attemptLogin(data):
	#json received should contain 'code' field. check if code is valid
	if not chamberBot_models.Code.objects.filter(code=data['code']).exists():
		return generateJson({'login': 1})

	#if code is valid, retrieve reminders
	id_chat = chamberBot_models.Code.objects.get(code=data['code'])
	data = chamberBot_models.Reminder.objects.filter(chat_id=id_chat).order_by('time')

	data = list(data.values())
	return generateJson({'login': 2, 'remind': data})

def generateJson(json):
	response = JsonResponse(json)
	response['Access-Control-Allow-Origin'] = '*' #very hacky TODO
	return response

#Accesses database every second and digs out reminders to send.
def remindJob():
	curr = time.time()
	#obtain result directly from database and check 
	data = chamberBot_models.Reminder.objects.filter(reported=False,time__lte=curr)
	for i in data:
		i.reported = True
		i.save()
		outputStr = i.name + ", here's your reminder to " + i.action + ". :)"
		sendMessage(i.chat_id.chat_id, outputStr)

def remindThread():
	while True:
		remindJob()
		time.sleep(1)
thread = threading.Thread(target=remindThread)
thread.daemon = True
thread.start()

"""
Telegram API calls ngrok, which then redirects and calls localhost and calls this method.
Telegram does not offer CSRF support (cannot insert CSRF cookie into response). 
Security is based completely on bot hash secrecy.
"""
@csrf_exempt 
def receive(request):
	data = json.loads(request.body)

	handleData(data) 
	return HttpResponse("Response received")

#Deals with data if it is a new TEXT message.
def handleData(data):
	#prepare json data to be sent.
	if 'message' not in data or 'text' not in data['message']:
		return
	chatID = data['message']['chat']['id']
	sender = data['message']['from']['first_name']
	chatString = data['message']['text'].lower()

	#Inspects message and redirects accordingly
	if chatString=="registergroup":
		#register group
		if chamberBot_models.Code.objects.filter(chat_id=chatID).exists():
			sendMessage(chatID,"Group has already been registered!")
		else:
			#print("Registering" + chatID)
			codeHash = hashlib.md5(str(chatID).encode('utf-8')).hexdigest()[:12]
			newChat = chamberBot_models.Code(chat_id=chatID, code=codeHash)

			newChat.save()
			sendMessage(chatID, "Chat successfully registered. Use '" + codeHash + "' as your passcode and login at " + FRONT_URL + ".")
			sendMessage(MASTER_CHAT_ID, "Chat " + str(chatID) + " was registered with " + codeHash + " as passcode.")

	#handle new reminder request
	if "remind me" in chatString and checkRegistered(chatID):
		ans = decodeReminder(chatID, chatString, sender)

	#displays list of reminders
	if chatString=="chamberlist" and checkRegistered(chatID):
		sendMessage(chatID, viewJobs(chatID))

	#clears list of reminders
	if chatString=="clearlist" and checkRegistered(chatID):
		clearJobs(chatID)
		sendMessage(chatID, "Cleared all reminders.")

def checkRegistered(chatID):
	if not chamberBot_models.Code.objects.filter(chat_id=chatID).exists():
		sendMessage(chatID, "Register this chat officially by typing 'registergroup'!")
		return False
	return True

def clearJobs(chatID):
	id_chat = chamberBot_models.Code.objects.get(chat_id=chatID)
	chamberBot_models.Reminder.objects.filter(chat_id=id_chat).delete()

def clearReminder(rid):
	chamberBot_models.Reminder.objects.get(id=rid).delete()

def viewJobs(chatID):
	id_chat = chamberBot_models.Code.objects.get(chat_id=chatID)
	data = chamberBot_models.Reminder.objects.filter(reported=False,chat_id=id_chat).order_by('time')
	if len(data)==0:
		return "No reminders at this time."

	ans = "Reminders:\n"
	for i in data:
		timeData = time.ctime(i.time)[4:16]
		actionData = i.action
		actionData = actionData[0].upper() + actionData[1:]
		strin = i.name + " - " + timeData + " - " + actionData + "\n"
		ans += strin

	ans += "\nView your reminders using passcode '" + id_chat.code + "'' at " + FRONT_URL + " ."
	return ans

# <excess> can you remind me in <time> to <action>
def decodeReminder(chatID, chatString, sender):
	dic = {"min": 60 , "minutes": 60, "minute": 60, "sec" : 1, "seconds" : 1, "second" : 1, "hours" : 3600, "hour" : 3600 }


	ans = chatString.split('remind me ', 1)
	if len(ans)==1:
		sendMessage(chatID, "Sorry, couldn't understand that.")
		return
	ans = ans[1]
	ans = ans.translate(str.maketrans('', '', string.punctuation))
	ans = ans.split(' ')
	#parse string and get values.
	actionStr = ""
	timeStr = ""
	timeArr = None

	#action

	timeBegin = -1
	actionBegin = -1
	for i in range(len(ans)):
		if ans[i]=="to" and actionBegin==-1:
			actionBegin = i+1

		if ans[i]=="in":
			if timeBegin==-1 or actionBegin==-1:
				timeBegin = i+1

		if ans[i]=="my":
			ans[i]="your"

	if actionBegin==-1:
		sendMessage(chatID, "Please specify both action and time.")
		return
	if timeBegin==-1:
		sendMessage(chatID, "Please specify both action and time.")
		return
	if actionBegin < timeBegin:
		#stack on action
		actionStr = ' '.join(ans[actionBegin:timeBegin-1])
		timeStr = ' '.join(ans[timeBegin:])
		timeArr = ans[timeBegin:]
	else:
		timeArr = ans[timeBegin:actionBegin-1]
		timeStr = ' '.join(ans[timeBegin:actionBegin-1])
		actionStr = ' '.join(ans[actionBegin:])

	c = -1
	timeDur = 0
	for i in timeArr:
		if i.isdigit():
			if c!=-1:
				sendMessage(chatID, "Sorry, couldn't understand that.")
				return
			c=int(i)
		else:
			if i not in dic or c==-1:
				sendMessage(chatID, "Sorry, couldn't understand that.")
				return
			timeDur += dic[i]*c
			c = -1

	#push reminder onto pq
	currTime = time.time()
	newTime = currTime + timeDur
	#put onto db
	en = chamberBot_models.Reminder(name=sender, action=actionStr, chat_id=chamberBot_models.Code.objects.get(chat_id=chatID), time=newTime, posted=currTime, reported=False)
	en.save()

	responseStr = "Okay " + sender + ", I'll remind you in " + timeStr + " to " + actionStr + "."
	sendMessage(chatID, responseStr)
	sendMessage(MASTER_CHAT_ID, "Chat " + str(chatID) + " requested a reminder to " + actionStr + " in " + timeStr)


def sendMessage(chatID, message):
	responseData = { "chat_id": chatID, "text": message}
	messageURL = BOT_URL + 'sendMessage'
	requests.post(messageURL, json=responseData)  # don't forget to make import requests lib