import os
from google.appengine.ext.webapp import template
import cgi
import re
import logging
import time
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.api import memcache
from django.utils import simplejson
import adventureModel
import main

class MovePageElement(webapp.RequestHandler):
  def post(self):
	logging.info("MovePageElement: begin")
	myElKey = self.request.get('myElKey')
	myNewOrderString = self.request.get('myNewOrder')
	adventure = None;
	changingPageEl = None;
	if myElKey and myNewOrderString:
		logging.info("MovePageElement: myElKey found: " + myElKey)
		changingPageEl = db.Model.get(myElKey)
		adventure = changingPageEl.adventure
	else:
		logging.info("MovePageElement: myElKey or myNewOrder not passed in")
		logging.info(myElKey + " " + myNewOrder)
		return
	if users.get_current_user():
		if not main.isUserAuthor(users.get_current_user(), adventure):
			logging.warning('MovePageElement post: you are not an author of this adventure')
			error = 'Error: You are not an author of this adventure'
			return
	myNewOrder = int(myNewOrderString)
	elQuery = adventureModel.PageElement.all()
	elQuery.filter('adventure = ', changingPageEl.adventure.key())
	elQuery.filter('page = ', changingPageEl.page.key())
	elQuery.order('pageOrder')
	elements = elQuery.fetch(9999)
	# now re-arrange the elements to be in the right order
	elementsArray = []
	counter = 0
	stagingElement = None
	for element in elements:
		element.pageOrder = counter
		if (changingPageEl.key() == element.key()):
			if (counter > 0 and myNewOrder < counter):
				oldElement = elementsArray.pop()
				element.pageOrder = counter - 1
				elementsArray.append(element)
				if (oldElement):
					oldElement.pageOrder = counter
					elementsArray.append(oldElement)
			elif (myNewOrder > counter):
				element.pageOrder = element.pageOrder + 1
				stagingElement = element
		elif stagingElement:
			stagingElement.pageOrder = counter
			elementsArray.append(stagingElement)
			stagingElement = None
			element.pageOrder = element.pageOrder - 1
			elementsArray.append(element)
		else:
			elementsArray.append(element)
		counter = counter + 1

	# print the new element order out
	counter = 0
	jsonArray = []
	for element in elementsArray:
		logging.info("MovePageElement: elementsArray[" + str(counter) + "] order(" + str(element.pageOrder) + ") : " + element.dataA)
		counter = counter + 1
		element.put()
		jsonArray.append(element.toDict())

	memcache.delete("pages" + str(adventure.key()))
	memcache.delete('XmlPages' + str(adventure.key()))
	self.response.out.write(simplejson.dumps(jsonArray))
	#logging.info(simplejson.dumps(jsonArray))

class DeletePageElement(webapp.RequestHandler):
  def post(self):
	logging.info("DeletePageElement: begin")
	adventure = None
	myElKey = self.request.get('myElKey')
	if myElKey:
		logging.info("DeletePageElement: myElKey found: " + myElKey)
		pageEl = db.Model.get(myElKey)
		adventure = pageEl.adventure
	else:
		logging.info("DeletePageElement: no myElKey passed in")
		return
	if users.get_current_user():
		if not main.isUserAuthor(users.get_current_user(), adventure):
			logging.warning('DeletePageElement post: you are not an author of this adventure')
			error = 'Error: You are not an author of this adventure'
			return
	else:
		return
	if (pageEl == None or adventure == None):
		logging.info("DeletePageElement: pageEl or adventure were null")
		return
	if (pageEl.enabled != 0):
		logging.info("DisablePageElement: cannot delete a page element that is not disabled")
		return
	pageEl.delete()
	memcache.delete("pages" + str(adventure.key()))
	memcache.delete('XmlPages' + str(adventure.key()))
	logging.info("DeletePageElement: returning json: " + simplejson.dumps("success"))
	self.response.out.write(simplejson.dumps("success"))

class DisablePageElement(webapp.RequestHandler):
  def post(self):
	logging.info("DisablePageElement: begin")
	adventure = None
	myElKey = self.request.get('myElKey')
	if myElKey:
		logging.info("DisablePageElement: myElKey found: " + myElKey)
		pageEl = db.Model.get(myElKey)
		adventure = pageEl.adventure
	else:
		logging.info("DisablePageElement: no myElKey passed in")
		return
	if users.get_current_user():
		if not main.isUserAuthor(users.get_current_user(), adventure):
			logging.warning('DisablePageElement post: you are not an author of this adventure')
			error = 'Error: You are not an author of this adventure'
			return
	else:
		return
	if (pageEl == None or adventure == None):
		logging.info("DisablePageElement: pageEl or adventure were null")
		return
	pageEl.enabled = 0
	pageEl.put()
	memcache.delete("pages" + str(adventure.key()))
	memcache.delete('XmlPages' + str(adventure.key()))
	logging.info("DisablePageElement: returning json: " + simplejson.dumps("success"))
	self.response.out.write(simplejson.dumps("success"))

class SavePageElement(webapp.RequestHandler):
  def post(self):
	#this method supports adding or updating page elements
	elementTypes = {
		"addPageElementText": 1,
		"addPageElementImage": 2,
		"addPageElementChoice": 3,
	}
	logging.info("SavePageElement begin")
	myPageElKey = self.request.get('myPageElKey')
	pageElement = None
	page = None
	adventure = None
	if myPageElKey:
		#existing page element
		logging.info("SavePageElement: key(" + myPageElKey + ") passed in did exist in DB, must be existing")
		pageElement = db.Model.get(myPageElKey)
		if pageElement:
			page = pageElement.page
			adventure = pageElement.adventure
		else:
			logging.warn("SavePageElement: key(%s) passed in did not exist in DB" % myPageElKey)
			return
	else:
		#new page element
		logging.info("SavePageElement: no page element key given, must be new")
		myPageKey = self.request.get('myPageKey')
		if (not myPageKey):
			logging.info("SavePageELement: expected myPageKey but it is null")
			return
		page = db.Model.get(myPageKey)
		if page:
			adventure = page.adventure
			pageElement = adventureModel.PageElement()
			#we dont want to change these things so we only set them when the page element is new
			pageElement.adventure = adventure.key()
			dataType = self.request.get('elementType')
			try:
				pageElement.dataType = int(dataType)
			except:
				logging.info("SavePageElement: expected elementType because new pageElement, but did not get it")
				return
		else:
			logging.warn("SavePageElement: new page element bu pageKey did not exist in DB: " + myPageKey)
			return

	if users.get_current_user():
		if not main.isUserAuthor(users.get_current_user(), adventure):
			logging.warning('SavePageElement post: you are not an author of this adventure')
			error = 'Error: You are not an author of this adventure'
			return
	else:
		return

	if not adventure or not page:
		logging.info("SavePageElement: could not find page or adventure. myPageKey(" + myPageKey + ")")

	logging.info("SavePageElement: getting page from key")
	pageElement.page = page.key()
	myPageOrder = self.request.get('pageOrder')
	pageElement.pageOrder = int(myPageOrder or 0)
	logging.info("SavePageElement: getting dataA")
	pageElement.dataA = self.request.get('dataA')
	if pageElement.dataA:
		logging.info("SavePageElement: replacing funky chars")
		#this replaces the funky quotes and stuff from MS Word / Google Docs with normal characters
		pageElement.dataA = pageElement.dataA.replace('%u2019', "'")
		pageElement.dataA = pageElement.dataA.replace('%u201C', '"')
		pageElement.dataA = pageElement.dataA.replace('%u201D', '"')
		pageElement.dataA = pageElement.dataA.replace('%u2026', '...')
		pageElement.dataA = pageElement.dataA.replace('%u2013', '-')
	logging.info("SavePageElement: getting dataB")
	pageElement.dataB = self.request.get('dataB')
	pageElement.enabled = 1;
	logging.info("SavePageElement: saving page element to DB")
	pageElement.put()
	adventure.version = adventure.version + .000001
	adventure.put()
	logging.info("SavePageElement: getting imageRef")
	myImgRef = self.request.get('imageRef')
	if myImgRef:
		logging.info("imageRef passed in: " + myImgRef)
		img = db.Model.get(myImgRef)
		img.imageName = self.request.get('imageName')
		img.pageElement = str(pageElement.key())
		img.put()
		#memcache.delete("img" + str(img.key()))
		#memcache.delete("images" + users.get_current_user().email())
		pageElement.dataA = img.imageName
		pageElement.imageRef = img.key()
		pageElement.put()
	#logging.info("dataA: " + pageElement.dataA)
	#logging.info("dataB: " + pageElement.dataB)
	logging.info("SavePageElement: clearning memcache")
	memcache.delete("pages" + str(adventure.key()))
	memcache.delete('XmlPages' + str(adventure.key()))
	memcache.delete('myStoriesXML' + users.get_current_user().email())
	#logging.info("SavePageElement: returning json: " + simplejson.dumps(pageElement.toDict()))
	logging.info("SavePageElement: returning json")
	self.response.out.write(simplejson.dumps(pageElement.toDict()))

class AddPageElement(webapp.RequestHandler):
  def post(self):
	logging.info("AddPageElement: begin")
	adventure = None
	myPageKey = self.request.get('myPageKey')
	myElementType = self.request.get('elementType')
	myPageOrder = self.request.get('pageOrder')
	elementTypes = {
		"addPageElementText": 1,
		"addPageElementImage": 2,
		"addPageElementChoice": 3,
	}
	page = None
	if myPageKey:
		logging.info("AddPageElement: myPageKey found: " + myPageKey)
		page = db.Model.get(myPageKey)
		adventure = page.adventure
	else:
		logging.info("AddPageElement: no pageKey passed in")
		return

	if users.get_current_user():
		if not main.isUserAuthor(users.get_current_user(), adventure):
			logging.warning('AddPageElement post: you are not an author of this adventure')
			error = 'Error: You are not an author of this adventure'
			return
	else:
		return

	if (page == None or adventure == None):
		logging.info("AddPageElement: page or adventure were null")
		return

	pageElement = adventureModel.PageElement()
	pageElement.page = page.key()
	pageElement.adventure = adventure.key()
	pageElement.dataType = elementTypes[myElementType]
	pageElement.pageOrder = int(myPageOrder or 1)
	pageElement.dataA = self.request.get('dataA')
	pageElement.dataB = self.request.get('dataB')
	pageElement.enabled = 1;
	pageElement.put()
	adventure.version = adventure.version + .000001
	adventure.put()
	memcache.delete("pages" + str(adventure.key()))
	memcache.delete('XmlPages' + str(adventure.key()))
	memcache.delete('myStoriesXML' + users.get_current_user().email())
	logging.info("AddPageElement: returning json: " + simplejson.dumps(pageElement.toDict()))
	self.response.out.write(simplejson.dumps(pageElement.toDict()))
