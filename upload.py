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

class ImageManager(webapp.RequestHandler):
  def get(self):
	adventure = None
	error = None
	if users.get_current_user():
		pass
	else:
		url = users.create_login_url(self.request.uri)
		url_linktext = 'Please login to use the Story Editor'
		template_values = {
			'url': url,
			'url_linktext': url_linktext,
		}
		main.printHeader(self)
		path = os.path.join(os.path.dirname(__file__), 'pleaseLogin.html')
		self.response.out.write(template.render(path, template_values))
		main.printFooter(self, None)
		return
	
	myAdventureKey = self.request.get('myAdventureKey')
	if myAdventureKey:
		adventure = db.Model.get(myAdventureKey)
	else:
		error = 'error: no adventure key passed in'
	if adventure == None:
		error = 'error: could not find Adventure ' + myAdventureKey + ' in the database'
	elif users.get_current_user() != adventure.realAuthor:
		error = 'error: you do not own this story'
		adventure = None

	template_values = {
		'adventure': adventure,
		'error': error
	}

	main.printHeader(self)
	path = os.path.join(os.path.dirname(__file__), 'upload.html')
	self.response.out.write(template.render(path, template_values))
	main.printFooter(self, template_values)
