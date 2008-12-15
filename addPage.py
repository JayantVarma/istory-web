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

class DeletePage(webapp.RequestHandler):
  def post(self):
	logging.error("DeletePage: begin")
	myPageKey = self.request.get('myPageKey')
	if myPageKey:
		logging.error("DeletePage: myPageKey found: " + myPageKey)
		page = db.Model.get(myPageKey)
		adventure = page.adventure
		if (page == None or adventure == None):
			logging.error("DeletePage: page or adventure were null")
			return
	else:
		logging.error("DeletePage: no pageKey passed in")
		return

	if users.get_current_user():
		if adventure.realAuthor and adventure.realAuthor != users.get_current_user():
			return
	else:
		return

	#memcache.delete("pages_" + adventure.key())
	query = adventureModel.PageElement.all().filter('page =', page.key())
	pageElements = query.fetch(1000)
	for pageElement in pageElements:
		logging.error(pageElement.key())
	db.delete(pageElements)
	page.delete()
	jsonResponse = "page and all page elements deleted"
	self.response.out.write(simplejson.dumps(jsonResponse))
	logging.error("returning addPage json: " + simplejson.dumps(jsonResponse))

class AddPage(webapp.RequestHandler):
  def post(self):
	logging.error("AddPage: begin")
	myPageKey = self.request.get('myPageKey')
	myAdventureKey = self.request.get('myAdventureKey')
	adventure = None
	page = None
	if myPageKey:
		logging.error("AddPage: myPageKey found: " + myPageKey)
		page = db.Model.get(myPageKey)
		adventure = page.adventure
	elif myAdventureKey:
		logging.error("AddPage: myAdventureKey found: " + myAdventureKey)
		page = adventureModel.Page()
		adventure = db.Model.get(myAdventureKey)
		page.adventure = adventure.key()
	else:
		logging.error("AddPage: no pageKey or adventureKey passed in")
		return

	if users.get_current_user():
		if adventure.realAuthor and adventure.realAuthor != users.get_current_user():
			return
	else:
		return

	if (page == None or adventure == None):
		logging.error("DeletePage: page or adventure were null")
		return

	page.name = self.request.get('pageName')
	page.put()
	#memcache.delete("pages_" + adventure.key())
	self.response.out.write(simplejson.dumps(page.toDict()))
	logging.error("returning addPage json: " + simplejson.dumps(page.toDict()))
	#self.redirect('/myStories')

  def get(self):
	adventure = None
	page = None
	if users.get_current_user():
		url = users.create_logout_url(self.request.uri)
		url_linktext = 'Logout'
		buttonText = 'Add Page'
		myPageKey = self.request.get('myPageKey')
		myAdventureKey = self.request.get('myAdventureKey')
		if myPageKey:
			buttonText = 'Update Page'
			page = db.Model.get(myPageKey)
			adventure = page.reference
		elif myAdventureKey:
			adventure = db.Model.get(myAdventureKey)
		else:
			buttonText = 'error: no adventure or page key'
	else:
		url = users.create_login_url(self.request.uri)
		url_linktext = 'Login To Update The Page'
		buttonText = ''

	template_values = {
		'url': url,
		'url_linktext': url_linktext,
		'buttonText': buttonText,
		'adventure': adventure,
		'page': page,
	}

	main.printHeader(self, 'Add A Page')
	path = os.path.join(os.path.dirname(__file__), 'addPage.html')
	self.response.out.write(template.render(path, template_values))
	main.printFooter(self, None)
