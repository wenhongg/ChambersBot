from django.db import models

# Create your models here.

#room to chat ID
class Code(models.Model):
	code = models.CharField(max_length=20)
	chat_id = models.CharField(max_length=20)

#register room and reminders
class Reminder(models.Model):
	name = models.CharField(max_length=20)
	action = models.CharField(max_length=100)
	chat_id = models.ForeignKey(Code, related_name='+', on_delete=models.CASCADE)
	#chat_id = models.CharField(max_length=100)
	time = models.IntegerField()
	posted = models.IntegerField()
	reported = models.BooleanField()

	class Meta:
		order_with_respect_to = 'time'
	
