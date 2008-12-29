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
	myAdventureKey = self.request.get('myAdventureKey')
	logging.error("AddAdventure for key: " + myAdventureKey)
	if myAdventureKey:
		logging.info("existing adventure.")
		adventure = db.Model.get(myAdventureKey)
	else:
		logging.info("new adventure.")
		adventure = adventureModel.Adventure()

	if users.get_current_user():
		if not users.is_current_user_admin() and adventure.realAuthor and adventure.realAuthor != users.get_current_user():
			pass
		else:
			if not adventure.realAuthor:
				adventure.realAuthor = users.get_current_user()
			adventure.title = self.request.get('title') or "[no title]"
			adventure.author = self.request.get('author') or "[no author]"
			adventure.desc = self.request.get('desc') or "[no description]"
			adventure.version = "1.0"
			adventure.put()
			memcache.delete("adventures")
			memcache.delete("adventures_" + users.get_current_user().email())
			logging.error("AddAdventure data: " + simplejson.dumps(adventure.toDict()))
			#now create an admin role for this user + adventure
			share = adventureModel.Share()
			share.adventure = adventure
			share.owner = users.get_current_user()
			share.child = users.get_current_user()
			share.role = 3
			share.status = 2
			share.put()
	
	logging.error("AddAdventure done for key: " + myAdventureKey)
	#self.redirect('/myStories')
	if not myAdventureKey:
		#redirect you right to the story editor if its a new story
		self.redirect('/storyEditor?myAdventureKey=' + str(adventure.key()))
	else:
		#redirect you back to myStories
		self.redirect('/myStories')

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
		myAdventureKey = self.request.get('myAdventureKey')
		if myAdventureKey:
			title = 'Update Story Details'
			buttonText = 'Update Story Details'
			adventure = db.Model.get(myAdventureKey)
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
