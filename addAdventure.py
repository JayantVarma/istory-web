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
	error = None
	newAdventure = False
	myAdventureKey = self.request.get('myAdventureKey')
	logging.info("AddAdventure for key: " + myAdventureKey)
	if not users.get_current_user():
		logging.warning('AddAdventure post: you need to login')
		error = "Error: You need to login."
	if myAdventureKey:
		logging.info("existing adventure.")
		adventure = db.Model.get(myAdventureKey)
		if not main.isUserAdmin(users.get_current_user(), adventure):
			logging.warning('AddAdventure post: you are not an admin of this adventure')
			error = "Error: You are not an admin of this adventure."
	else:
		logging.info("new adventure.")
		adventure = adventureModel.Adventure()
		newAdventure = True

	if error:
		defaultTemplateValues = main.getDefaultTemplateValues(self)
		templateValues = {
			'error': error
		}
		templateValues = dict(defaultTemplateValues, **templateValues)
		path = os.path.join(os.path.dirname(__file__), 'addAdventure.html')
		self.response.out.write(template.render(path, templateValues))
		return

	if not adventure.realAuthor:
		adventure.realAuthor = users.get_current_user()
	adventure.title = self.request.get('title') or "[no title]"
	adventure.author = self.request.get('author') or "[no author]"
	adventure.desc = self.request.get('desc') or "[no description]"
	adventure.version = "1.0"
	adventure.put()
	memcache.delete("adventures")
	memcache.delete("adventures_" + users.get_current_user().email())
	logging.info("AddAdventure data: " + simplejson.dumps(adventure.toDict()))
	if newAdventure:
		#now create an admin role for this user + adventure, only if its a new adventure
		share = adventureModel.Share()
		share.adventure = adventure
		share.owner = users.get_current_user()
		share.child = users.get_current_user()
		share.role = 3
		share.status = 2
		share.put()
	
	#remove the cache object for all users who have a role for this adventure
	q = adventureModel.Share.all().filter('adventure =', adventure)
	shares = q.fetch(9999)
	logging.info("AddAdventure: removed %d cache objects" % len(shares))
	for share in shares:
		memcache.delete("adventures_" + share.child.email())
	memcache.delete(str(adventure.key))
	
	logging.info("AddAdventure done for key: " + myAdventureKey)
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
