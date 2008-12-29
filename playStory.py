import os
from google.appengine.ext.webapp import template
import cgi
import re
import logging
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.api import datastore
from google.appengine.api import memcache
from django.utils import simplejson
import adventureModel
import main

class Play(webapp.RequestHandler):
  def get(self):
	adventure = None
	page = None
	error = None
	title = None

	myAdventureKey = self.request.get('myAdventureKey')
	if myAdventureKey:
		adventure = memcache.get(myAdventureKey)
		if adventure:
			logging.info("Play: got adventure from cache")
		else:
			logging.info("Play: got adventure from db")
			adventure = db.Model.get(myAdventureKey)
			memcache.add(myAdventureKey, adventure, 3600)
	else:
		error = 'Error: no adventure key passed in'
	if adventure == None:
		error = 'Error: could not find Adventure ' + myAdventureKey + ' in the database'
	elif not main.isUserReader(users.get_current_user(), adventure):
		error = 'Error: You are not a reader of this adventure'
	else:
		title = adventure.title
	if error:
		logging.info('Play get: ' + error)

	defaultTemplateValues = main.getDefaultTemplateValues(self)
	templateValues = {
		'adventure': adventure,
		'error': error,
		'title': title,
		'isUserAuthor': main.isUserAuthor(users.get_current_user(), adventure),
		'isUserAdmin': main.isUserAdmin(users.get_current_user(), adventure),
	}
	templateValues = dict(defaultTemplateValues, **templateValues)

	if self.request.get('playLite'):
		path = os.path.join(os.path.dirname(__file__), 'playStoryLite.html')
	else:
		path = os.path.join(os.path.dirname(__file__), 'playStory.html')
	self.response.out.write(template.render(path, templateValues))
