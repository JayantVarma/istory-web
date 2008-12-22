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

class ViewSharing(webapp.RequestHandler):
  def get(self):
	adventure = None
	page = None
	error = None
	title = 'Share and Collaborate'
	myAdventureKey = self.request.get('myAdventureKey')
	ownedAdventures = None
	sharedAdventures = None

	if not users.get_current_user():
		error = 'error: you are not logged in'
	else:
		#we're logged in, so get all the adventures that this person owns or has been shared
		#owned adventures
		q1 = adventureModel.Adventure.all()
		q1.filter('realAuthor = ', users.get_current_user())
		q1.order('-created')
		ownedAdventures = q1.fetch(9999)
		#shared adventures
		q2 = adventureModel.Share.all()
		q2.filter('child = ', users.get_current_user())
		q2.order('-owner')
		sharedAdventures = q2.fetch(9999)

	defaultTemplateValues = main.getDefaultTemplateValues(self)
	templateValues = {
		'adventureKey': myAdventureKey,
		'error': error,
		'title': title,
		'ownedAdventures': ownedAdventures,
		'sharedAdventures': sharedAdventures,
	}
	templateValues = dict(defaultTemplateValues, **templateValues)

	path = os.path.join(os.path.dirname(__file__), 'share.html')
	self.response.out.write(template.render(path, templateValues))
