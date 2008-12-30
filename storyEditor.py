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

class DeletePage(webapp.RequestHandler):
  def post(self):
	logging.info("DeletePage: begin")
	myPageKey = self.request.get('myPageKey')
	if myPageKey:
		logging.info("DeletePage: myPageKey found: " + myPageKey)
		page = db.Model.get(myPageKey)
		adventure = page.adventure
		if (page == None or adventure == None):
			logging.info("DeletePage: page or adventure were null")
			return
	else:
		logging.info("DeletePage: no pageKey passed in")
		return

	if users.get_current_user():
		if not main.isUserAuthor(users.get_current_user(), adventure):
			logging.warning('DeletePage post: you are not an author of this adventure')
			error = 'Error: You are not an author of this adventure'
			return
	else:
		return

	#memcache.delete("pages_" + adventure.key())
	query = adventureModel.PageElement.all().filter('page =', page.key())
	pageElements = query.fetch(1000)
	for pageElement in pageElements:
		logging.info(pageElement.key())
	db.delete(pageElements)
	page.delete()
	jsonResponse = "page and all page elements deleted"
	self.response.out.write(simplejson.dumps(jsonResponse))
	logging.info("returning addPage json: " + simplejson.dumps(jsonResponse))

class AddPage(webapp.RequestHandler):
  def post(self):
	logging.info("AddPage: begin")
	myPageKey = self.request.get('myPageKey')
	myAdventureKey = self.request.get('myAdventureKey')
	adventure = None
	page = None
	if myPageKey:
		logging.info("AddPage: myPageKey found: " + myPageKey)
		page = db.Model.get(myPageKey)
		adventure = page.adventure
	elif myAdventureKey:
		logging.info("AddPage: myAdventureKey found: " + myAdventureKey)
		page = adventureModel.Page()
		adventure = db.Model.get(myAdventureKey)
		page.adventure = adventure.key()
	else:
		logging.info("AddPage: no pageKey or adventureKey passed in")
		return

	if users.get_current_user():
		if not main.isUserAuthor(users.get_current_user(), adventure):
			logging.warning('AddPage post: you are not an author of this adventure')
			error = 'Error: You are not an author of this adventure'
			return
	else:
		return

	if (page == None or adventure == None):
		logging.info("DeletePage: page or adventure were null")
		return

	page.name = self.request.get('pageName')
	page.put()
	#memcache.delete("pages_" + adventure.key())
	self.response.out.write(simplejson.dumps(page.toDict()))
	logging.info("returning addPage json: " + simplejson.dumps(page.toDict()))

class GetPages(webapp.RequestHandler):
  def post(self):
	error = None
	myAdventureKey = self.request.get('myAdventureKey')
	adventure = db.Model.get(myAdventureKey)
	if adventure == None:
		return
	elif not main.isUserReader(users.get_current_user(), adventure):
		logging.warning('GetPages post: you are not a reader of this adventure')
		error = 'Error: You are not a reader of this adventure'
		return

	pagesQuery = adventureModel.Page.all()
	pagesQuery.filter('adventure = ', adventure.key())
	pagesQuery.order('created')
	pages = pagesQuery.fetch(9999)
	elQuery = adventureModel.PageElement.all()
	elQuery.filter('adventure = ', adventure.key())
	elQuery.order('pageOrder')
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
	logging.info("got " + str(len(pagesJSON)) + " pages for key " + myAdventureKey)

class StoryEditor(webapp.RequestHandler):
  def get(self):
	adventure = None
	page = None
	error = None
	
	myAdventureKey = self.request.get('myAdventureKey')
	if myAdventureKey:
		adventure = db.Model.get(myAdventureKey)
	else:
		error = 'error: no adventure key passed in'
	if adventure == None:
		error = 'error: could not find Adventure ' + myAdventureKey + ' in the database'
	elif not main.isUserAuthor(users.get_current_user(), adventure):
		logging.warning('StoryEditor get: you are not an author of this adventure')
		error = 'Error: You are not an author of this adventure'
	elif not users.get_current_user():
		error = 'error: you are not logged in'

	if error:
		logging.info("########## ERROR: " + error);
	defaultTemplateValues = main.getDefaultTemplateValues(self)
	templateValues = {
		'adventure': adventure,
		'error': error,
		'title': "StoryForge - " + adventure.title,
	}
	templateValues = dict(defaultTemplateValues, **templateValues)

	path = os.path.join(os.path.dirname(__file__), 'storyEditor.html')
	self.response.out.write(template.render(path, templateValues))
