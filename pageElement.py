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

class MovePageElement(webapp.RequestHandler):
  def post(self):
	logging.error("MovePageElement: begin")
	myElKey = self.request.get('myElKey')
	myNewOrderString = self.request.get('myNewOrder')
	adventure = None;
	changingPageEl = None;
	if myElKey and myNewOrderString:
		logging.error("MovePageElement: myElKey found: " + myElKey)
		changingPageEl = db.Model.get(myElKey)
		adventure = changingPageEl.adventure
	else:
		logging.error("MovePageElement: myElKey or myNewOrder not passed in")
		logging.error(myElKey + " " + myNewOrder)
		return
	if users.get_current_user():
		if adventure.realAuthor and adventure.realAuthor != users.get_current_user():
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
		logging.error("MovePageElement: elementsArray[" + str(counter) + "] order(" + str(element.pageOrder) + ") : " + element.dataA)
		counter = counter + 1
		element.put()
		jsonArray.append(element.toDict())
	self.response.out.write(simplejson.dumps(jsonArray))
	logging.error(simplejson.dumps(jsonArray))

class DeletePageElement(webapp.RequestHandler):
  def post(self):
	logging.error("DeletePageElement: begin")
	myElKey = self.request.get('myElKey')
	if myElKey:
		logging.error("DeletePageElement: myElKey found: " + myElKey)
		pageEl = db.Model.get(myElKey)
		adventure = pageEl.adventure
	else:
		logging.error("DeletePageElement: no myElKey passed in")
		return
	if users.get_current_user():
		if adventure.realAuthor and adventure.realAuthor != users.get_current_user():
			return
	else:
		return
	if (pageEl == None or adventure == None):
		logging.error("DeletePageElement: pageEl or adventure were null")
		return
	if (pageEl.enabled != 0):
		logging.error("DisablePageElement: cannot delete a page element that is not disabled")
		return
	pageEl.delete()
	self.response.out.write(simplejson.dumps("success"))
	logging.error("DeletePageElement: returning json: " + simplejson.dumps("success"))

class DisablePageElement(webapp.RequestHandler):
  def post(self):
	logging.error("DisablePageElement: begin")
	myElKey = self.request.get('myElKey')
	if myElKey:
		logging.error("DisablePageElement: myElKey found: " + myElKey)
		pageEl = db.Model.get(myElKey)
		adventure = pageEl.adventure
	else:
		logging.error("DisablePageElement: no myElKey passed in")
		return
	if users.get_current_user():
		if adventure.realAuthor and adventure.realAuthor != users.get_current_user():
			return
	else:
		return
	if (pageEl == None or adventure == None):
		logging.error("DisablePageElement: pageEl or adventure were null")
		return
	pageEl.enabled = 0
	pageEl.put()
	self.response.out.write(simplejson.dumps("success"))
	logging.error("DisablePageElement: returning json: " + simplejson.dumps("success"))

class SavePageElement(webapp.RequestHandler):
  def post(self):
	#this method supports adding or updating page elements
	elementTypes = {
		"addPageElementText": 1,
		"addPageElementImage": 2,
		"addPageElementChoice": 3,
	}
	logging.error("SavePageElement begin")
	myPageElKey = self.request.get('myPageElKey')
	pageElement = None
	page = None
	adventure = None
	if myPageElKey:
		#existing page element
		pageElement = db.Model.get(myPageElKey)
		page = pageElement.page
		adventure = pageElement.adventure
	else:
		#new page element
		logging.error("SavePageElement: key passed in did not exist in DB, must be new")
		myPageKey = self.request.get('myPageKey')
		if (not myPageKey):
			logging.error("SavePageELement: expected myPageKey but it is null")
			return
		page = db.Model.get(myPageKey)
		adventure = page.adventure
		pageElement = adventureModel.PageElement()
		#we dont want to change these things so we only set them when the page element is new
		pageElement.adventure = adventure.key()
		dataType = self.request.get('elementType')
		try:
			pageElement.dataType = int(dataType)
		except:
			logging.error("SavePageElement: expected elementType because new pageElement, but did not get it")
			return

	if users.get_current_user():
		if adventure.realAuthor and adventure.realAuthor != users.get_current_user():
			return
	else:
		return

	if not adventure or not page:
		logging.error("SavePageElement: could not find page or adventure. myPageKey(" + myPageKey + ")")

	pageElement.page = page.key()
	myPageOrder = self.request.get('pageOrder')
	pageElement.pageOrder = int(myPageOrder or 1)
	pageElement.dataA = self.request.get('dataA')
	pageElement.dataB = self.request.get('dataB')
	pageElement.enabled = 1;
	pageElement.put()
	logging.error("dataA: " + pageElement.dataA)
	logging.error("dataB: " + pageElement.dataB)
	self.response.out.write(simplejson.dumps(pageElement.toDict()))
	logging.error("AddPageElement: returning json: " + simplejson.dumps(pageElement.toDict()))

class AddPageElement(webapp.RequestHandler):
  def post(self):
	logging.error("AddPageElement: begin")
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
		logging.error("AddPageElement: myPageKey found: " + myPageKey)
		page = db.Model.get(myPageKey)
		adventure = page.adventure
	else:
		logging.error("AddPageElement: no pageKey passed in")
		return

	if users.get_current_user():
		if adventure.realAuthor and adventure.realAuthor != users.get_current_user():
			return
	else:
		return

	if (page == None or adventure == None):
		logging.error("AddPageElement: page or adventure were null")
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
	#memcache.delete("pages_" + adventure.key())
	self.response.out.write(simplejson.dumps(pageElement.toDict()))
	logging.error("AddPageElement: returning json: " + simplejson.dumps(pageElement.toDict()))
