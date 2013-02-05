from django.db import models
import datetime


class User(models.Model):
    username = models.CharField(max_length=255)
    password = models.CharField(max_length=255)


class Cardset(models.Model):
    title = models.CharField(max_length=255)
    username = models.ForeignKey(User)


class Card(models.Model):
    number = models.IntegerField()
    question = models.TextField()
    answer = models.TextField()
    hint = models.TextField(default="")
    cardset = models.ForeignKey(Cardset)

    def __unicode__(self):
        return self.question


class Temp_Card(models.Model):
    number = models.IntegerField()
    question = models.TextField()
    answer = models.TextField()
    hint = models.TextField(default="")

    def __unicode__(self):
        return self.question


class Session(models.Model):
    username = models.ForeignKey(User)
    title = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)
    num_cards = models.IntegerField(default=0)
    correct = models.IntegerField(default=0)
    wrong = models.IntegerField(default=0)
    skipped = models.IntegerField(default=0)


class VirtualCard(models.Model):
    number = models.IntegerField()
    card = models.ForeignKey(Card)
    session = models.ForeignKey(Session)
    state = models.IntegerField()

    def __unicode__(self):
        return self.card.question

