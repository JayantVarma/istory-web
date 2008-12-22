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
		adventure = db.Model.get(myAdventureKey)
	else:
		error = 'error: no adventure key passed in'
	if adventure == None:
		error = 'error: could not find Adventure ' + myAdventureKey + ' in the database'
	#elif users.get_current_user() and users.get_current_user() != adventure.realAuthor:
	#	error = 'error: you do not own this story'
	else:
		title = adventure.title
	

	defaultTemplateValues = main.getDefaultTemplateValues(self)
	templateValues = {
		'adventure': adventure,
		'error': error,
		'title': title,
	}
	templateValues = dict(defaultTemplateValues, **templateValues)

	if self.request.get('playLite'):
		path = os.path.join(os.path.dirname(__file__), 'playStoryLite.html')
	else:
		path = os.path.join(os.path.dirname(__file__), 'playStory.html')
	self.response.out.write(template.render(path, templateValues))
