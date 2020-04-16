# ChambersBot

## What is it?

ChambersBot is a reminder bot built with Django for Telegram users. Add ChambersBot to a group chat, or chat with it directly to set a reminder minutes or hours in advance. 

A chat must first be registered by typing `registergroup` in the chat. If successful, the bot will respond with a message, and provide a passcode which can be used to login on a provided webpage to view the list of reminders for the group.

A reminder can be requested in the format `remind me to submit my assignment online in 3 hours` or `remind me in 10 minutes to make a call`. The bot will acknowledge that a reminder is set, and send the reminder at the given time.

Request the list of reminders by typing `chamberlist`. The times returned are in **GMT**.

Type `clearlist` to clear all reminders in the list.

## Important steps:

**Remember to place .env file in the root folder.**

### Initial deploy steps:
```
heroku login
heroku create
heroku addons:create heroku-postgresql:hobby-dev -a <app-name>

- git processes -

heroku run python manage.py migrate
```

### To push to Heroku server:
```
git add .
git commit -m "<whatever>"
heroku git:remote -a <herokuapp name>
git push heroku master
```
Note that the third command need not be run once heroku is set.

For changes to models, run: 
```
heroku run python manage.py migrate
python manage.py migrate --run-syncdb
```

For changes to .env file, run 
```
python heroku-config.py
``` 
This sets the .env files in heroku. [Source](https://github.com/sdkcodes/heroku-config)

### Helpful commands

To view real time logs on Heroku, use `heroku logs -t`.

To generate requirements.txt from project dependencies only, we can use `pipreqs` - however, it fails on some dependencies e.g. gunicorn within django.

## References: 

https://devcenter.heroku.com/articles/git  

https://medium.com/@qazi/how-to-deploy-a-django-app-to-heroku-in-2018-the-easy-way-48a528d97f9c

## Limitations

1. The time returned on `chamberlist` may be in the wrong timezone.
2. Resolve CORS issues and provide CSRF cookie?
