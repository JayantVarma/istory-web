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

class GetPages(webapp.RequestHandler):
  def get(self):
	error = None
	myAdventureKey = self.request.get('myAdventureKey')
	adventure = db.Model.get(myAdventureKey)
	if users.get_current_user() != adventure.realAuthor:
		adventure = None

	pagesQuery = adventureModel.Page.all()
	pagesQuery.filter('adventure = ', adventure.key())
	pages = pagesQuery.fetch(9999)
	elQuery = adventureModel.PageElement.all()
	elQuery.filter('adventure = ', adventure.key())
	elements = elQuery.fetch(9999)
	pagesJSON = []
	for page in pages:
		elementsArray = []
		for element in elements:
			if element.page.key() == page.key():
				elementsArray.append(element.toDict())
		pageDict = page.toDict()
		pageDict['elements'] = elementsArray
		pagesJSON.append(pageDict)
	self.response.out.write(simplejson.dumps(pagesJSON))
	logging.error(simplejson.dumps(pagesJSON))
	#self.response.out.write("[{\"adventure\": 5, \"name\": \"page name\", \"id\": 6}]")
	#self.response.out.write(json.GqlEncoder.encode(pagesQuery))
	#template_values = {
	#	'pages': pages
	#}
	#path = os.path.join(os.path.dirname(__file__), 'getPages.html')
	#self.response.out.write(template.render(path, template_values))

class StoryEditor(webapp.RequestHandler):
  def get(self):
	adventure = None
	page = None
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

	if users.get_current_user() != adventure.realAuthor:
		error = 'error: you do not own this story'
		adventure = None

	template_values = {
		'adventure': adventure,
		'error': error
	}

	main.printHeader(self)
	path = os.path.join(os.path.dirname(__file__), 'storyEditor.html')
	self.response.out.write(template.render(path, template_values))
	main.printFooter(self, None)
