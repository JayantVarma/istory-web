import os
from google.appengine.ext.webapp import template
import cgi
import re
import logging
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.api import memcache
from django.utils import simplejson
import adventureModel
import main

class AddAdventure(webapp.RequestHandler):
  def post(self):
	myKey = self.request.get('myKey')
	logging.error("AddAdventure for key: " + myKey)
	if myKey:
		adventure = db.Model.get(myKey)
	else:
		adventure = adventureModel.Adventure()

	if users.get_current_user():
		if not users.is_current_user_admin() and adventure.realAuthor and adventure.realAuthor != users.get_current_user():
			pass
		else:
			adventure.realAuthor = users.get_current_user()
			adventure.title = self.request.get('title') or "[no title]"
			adventure.author = self.request.get('author') or "[no author]"
			adventure.desc = self.request.get('desc') or "[no description]"
			adventure.version = "1.0"
			adventure.put()
			memcache.delete("adventures")
			memcache.delete("adventures_" + users.get_current_user().email())
			logging.error("AddAdventure data: " + simplejson.dumps(adventure.toDict()))
	
	logging.error("AddAdventure done for key: " + myKey)
	#self.redirect('/myStories')
	#redirect you right to the story editor
	self.redirect('/storyEditor?myAdventureKey=' + str(adventure.key()))

  def get(self):
	adventure = None
	buttonText = None
	title = 'Create A New Story'
	url = None
	url_linktext = None
	if users.get_current_user():
		url = users.create_logout_url(self.request.uri)
		url_linktext = 'Logout'
		buttonText = 'Create Story'
		myKey = self.request.get('key')
		if myKey:
			title = 'Update Story Details'
			buttonText = 'Update Story Details'
			adventure = db.Model.get(myKey)
	else:
		url = users.create_login_url(self.request.uri)
		url_linktext = 'Login To Create A Story'
		buttonText = ''

	defaultTemplateValues = main.getDefaultTemplateValues(self)
	templateValues = {
		'title': title,
		'url': url,
		'url_linktext': url_linktext,
		'buttonText': buttonText,
		'adventure': adventure,
	}
	templateValues = dict(defaultTemplateValues, **templateValues)


	path = os.path.join(os.path.dirname(__file__), 'addAdventure.html')
	self.response.out.write(template.render(path, templateValues))
