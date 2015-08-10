import StringIO
import json
import logging
import random
import urllib
import urllib2
from requests import HTTPError

# for sending images
from PIL import Image
import multipart

# standard app engine imports
from google.appengine.api import urlfetch
from google.appengine.ext import ndb
import webapp2

# lib for orchestrate and python-telegram-bot
from porc import Client
import telegram

# my own configuration
from config import *

BASE_URL = 'https://api.telegram.org/bot' + TOKEN + '/'
bot = telegram.Bot(token=TOKEN)
client = Client(ORCH_API_KEY, ORCH_HOST)


# ================================

class EnableStatus(ndb.Model):
  # key name: str(chat_id)
  enabled = ndb.BooleanProperty(indexed=False, default=False)
  settings = ndb.BooleanProperty(indexed=False, default=False)


# ================================

def setEnabled(chat_id, yes):
  es = EnableStatus.get_or_insert(str(chat_id))
  es.enabled = yes
  es.put()


def getEnabled(chat_id):
  es = EnableStatus.get_by_id(str(chat_id))
  if es:
    return es.enabled
  return False


def setSettings(chat_id, yes):
  es = EnableStatus.get_or_insert(str(chat_id))
  es.settings = yes
  es.put()


def getSettings(chat_id):
  es = EnableStatus.get_by_id(str(chat_id))
  if es:
    return es.settings
  return False


# ================================

class MeHandler(webapp2.RequestHandler):

  def get(self):
    urlfetch.set_default_fetch_deadline(60)
    # self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL +
    # 'getMe'))))
    self.response.write(bot.getMe())


class GetUpdatesHandler(webapp2.RequestHandler):

  def get(self):
    urlfetch.set_default_fetch_deadline(60)
    self.response.write(
        json.dumps(json.load(urllib2.urlopen(BASE_URL + 'getUpdates'))))


class SetWebhookHandler(webapp2.RequestHandler):

  def get(self):
    urlfetch.set_default_fetch_deadline(60)
    url = self.request.get('url')
    if url:
      self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'setWebhook', urllib.urlencode({'url': url})))))


class WebhookHandler(webapp2.RequestHandler):

  def post(self):
    urlfetch.set_default_fetch_deadline(60)
    body = json.loads(self.request.body)
    logging.info('request body:')
    logging.info(body)
    self.response.write(json.dumps(body))

    update_id = body['update_id']
    message = body['message']
    message_id = message.get('message_id')
    date = message.get('date')
    text = message.get('text')
    user_from = message.get('from')
    user_id = user_from.get('id')
    chat = message['chat']
    chat_id = chat['id']

    if not text:
      logging.info('no text')
      return

    if text.startswith('/'):
      if text == '/start':
        response = client.get('Chat', chat_id)
        try:
          response.raise_for_status()
        except HTTPError:
          response = client.put('Chat', chat_id, {
            'group': 0,
            'username': user_from.get('username')
            })
        bot.sendMessage(chat_id=chat_id, text=('Hello, @%s!' % user_from.get('username')))
        setEnabled(chat_id, True)
      elif text == '/help':
        bot.sendMessage(chat_id=chat_id, text='Help cooming soon...')
      elif text.startswith('/group'):
        try:
          group = text.split(' ')[1]
        except IndexError:
          group = '0'
          bot.sendMessage(chat_id=chat_id, text=('Enter, please, /group with number'))
        if group != '0':
          bot.sendMessage(chat_id=chat_id, text=('You enter group: %s' % str(group)))
          # Then load schedule for this group
      elif text.startswith('/setgroup'):
        try:
          group = text.split(' ')[1]
        except IndexError:
          group = '0'
          bot.sendMessage(chat_id=chat_id, text=('Enter, please, /setgroup with number'))
        if group != '0':
          # Saving settings
          response = client.put('Chat', chat_id, {
            'group': group,
            'username': user_from.get('username')
            })
          bot.sendMessage(chat_id=chat_id, text=('You enter group: %s\nSettings are saved' % str(group)))
      # elif text == '/cancel':
        # if getSettings(chat_id):
          # bot.sendMessage(chat_id=chat_id, text='Settings are not saved')
          # setSettings(chat_id, False)
      elif text.startswith('/today'):
        response = client.get('Chat', chat_id)
        try:
          response.raise_for_status()
        except HTTPError:
          bot.sendMessage(chat_id=chat_id, text='Sorry, something wrong!')
        group = response.json['group']
        if str(group) == '0':
          bot.sendMessage(chat_id=chat_id, text=('Set your group using /setgroup [number]'))
        else:
          bot.sendMessage(chat_id=chat_id, text=('Your group: %s' % str(group)))
          # Then load schedule for current group
      else:
        bot.sendMessage(chat_id=chat_id, text='Unknown command. Help cooming soon...')
    else:
      # bot.sendMessage(chat_id=chat_id, text='Unknown command. Help cooming soon...')
      logging.info('no command')
      logging.info(text)


app=webapp2.WSGIApplication([
  ('/me', MeHandler),
  ('/updates', GetUpdatesHandler),
  ('/set_webhook', SetWebhookHandler),
  ('/webhook', WebhookHandler),
], debug=True)
