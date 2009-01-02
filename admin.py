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

def duplicateAdventure(adventure):
	if not adventure:
		return None
	#Adventure
	newAdventure = adventureModel.Adventure()
	newAdventure.title =       adventure.title
	newAdventure.realAuthor =  adventure.realAuthor
	newAdventure.author =      adventure.author
	newAdventure.version =     adventure.version
	newAdventure.desc =        adventure.desc
	newAdventure.created =     adventure.created
	newAdventure.modified =    adventure.modified
	newAdventure.put()
	#Page & PageElement
	q = adventureModel.Page.all().filter('adventure =', adventure)
	pages = q.fetch(9999)
	for page in pages:
		newPage = adventureModel.Page()
		newPage.adventure = newAdventure
		newPage.name = page.name
		newPage.created = page.created
		newPage.modified = page.modified
		newPage.put()
		#now do the page elements for this page
		q2 = adventureModel.PageElement.all().filter('adventure =', adventure).filter('page =', page)
		pageEls = q2.fetch(9999)
		for pageEl in pageEls:
			newPageEl = adventureModel.PageElement()
			newPageEl.adventure = newAdventure
			newPageEl.page = newPage
			newPageEl.dataType = pageEl.dataType
			newPageEl.pageOrder = pageEl.pageOrder
			newPageEl.dataA = pageEl.dataA
			newPageEl.dataB = pageEl.dataB
			newPageEl.imageRef = pageEl.imageRef
			newPageEl.enabled = pageEl.enabled
			newPageEl.created = pageEl.created
			newPageEl.modified = pageEl.modified
			newPageEl.put()
	#Image
	# we don't need to do image, since you cant really edit those
	return newAdventure

def getAdventureStatus(adventure):
	adventureStatus = None
	#first try to get it from the cache
	adventureStatus = memcache.get('advStat' + str(adventure.key()))
	if adventureStatus:
		logging.info('getAdventureStatus: got record from cache')
	else:
		#try to get it from the db
		q = adventureModel.AdventureStatus.all().filter('publishedAdventure =', adventure)
		statuses = q.fetch(1)
		for myStatus in statuses:
			adventureStatus = myStatus
		if adventureStatus:
			logging.info('getAdventureStatus: got published adventure')
		else:
			#look it up via the editableAdventure now
			q = adventureModel.AdventureStatus.all().filter('editableAdventure =', adventure)
			statuses = q.fetch(1)
			for myStatus in statuses:
				adventureStatus = myStatus
			if adventureStatus:
				logging.info('getAdventureStatus: got editable adventure')
			else:
				logging.warn('getAdventureStatus: could not find AdventureStatus with key: ' + str(adventure.key()))
				return
		if adventureStatus:
			#add it to the cache
			logging.info('getAdventureStatus: got record from db')
			memcache.add('advStat' + str(adventure.key()), adventureStatus, 86400)
	return adventureStatus

class Submit(webapp.RequestHandler):
  def get(self, comment_in=None, myAdventureKey_in=None, submitFlag=False):
	adventure = None
	adventureStatus = None
	error = None
	myAdventureKey = None
	submitComment = comment_in
	comment = None
	if myAdventureKey_in:
		myAdventureKey = myAdventureKey_in
	else:
		myAdventureKey = self.request.get('myAdventureKey')
	adventure = main.getAdventure(myAdventureKey)
	if not adventure:
		logging.warn('Submit: adventure was not found in the DB: ' + myAdventureKey)
		error = "Adventure key was not found in the DB"
	else:
		#make sure the logged in person is an admin
		if not main.isUserAdmin(users.get_current_user(), adventure):
			logging.warning('RemoveShare post: you are not an admin of this adventure')
			error = 'Error: You are not an admin of this adventure'
		else:
			#try to get the AdventureStatus record, if it doesn't exist, create it
			adventureStatus = getAdventureStatus(adventure)
			if not adventureStatus:
				logging.warn("Submit: could not found adventureStatus record: " + myAdventureKey)
			else:
				logging.info('Submit: got adventureStatus record')
	
	#if we have a submitFlag, then we're trying to submit the form
	if submitFlag and adventure and adventureStatus:
		logging.info("Submit: submit flag was set. comment(%s)" % comment)
		#now duplicate the story
		adventureStatus.publishedAdventure = duplicateAdventure(adventure)
		if adventureStatus.publishedAdventure:
			comment = 'Your story has been submitted.'
			adventureStatus.status = 2
			adventureStatus.put()
			#reset the cache
			memcache.delete('advStat' + str(adventure.key()))
		else:
			error = 'Error, something went wrong with the submission.'
		

	defaultTemplateValues = main.getDefaultTemplateValues(self)
	templateValues = {
		'comment': comment,
		'error': error,
		'adventureStatus': adventureStatus,
		'title': 'Submit Your Story For Approval',
	}
	templateValues = dict(defaultTemplateValues, **templateValues)

	path = os.path.join(os.path.dirname(__file__), 'submit.html')
	self.response.out.write(template.render(path, templateValues))

  def post(self):
	comment = self.request.get('comment')
	myAdventureKey = self.request.get('myAdventureKey')
	self.get(comment, myAdventureKey, True)

class Admin(webapp.RequestHandler):
  def get(self):
	if not users.is_current_user_admin():
		return
	myAdventureKey = self.request.get('myAdventureKey')
	command = self.request.get('command')
	var = self.request.get('var')
	logging.info("Admin get: myAdventureKey(%s)" % (myAdventureKey))
	output = "Admin get: myAdventureKey(%s) command(%s) var(%s)<br>" % (myAdventureKey, command, var)

	if command == 'delete story' and var:
		#this will delete all story data for a given adventure
		adventure = None
		logging.info("Admin get: delete story: " + var)
		output += "Admin get: delete story: " + var + "<br>"
		try:
			adventure = db.Model.get(var)
		except Exception, e:
			output += "Admin get: delete story: exception: " + str(e) + "<br>"
		if not adventure:
			logging.info("Admin get: delete story: adventure key not found in DB")
			output += "Admin get: delete story: adventure key not found in DB<br>"
		else:
			#share
			q = adventureModel.Share.all().filter('adventure =', adventure)
			a = q.fetch(9999)
			output += "Admin get: delete story: deleted %d records from Share<br>" % len(a)
			db.delete(a)
			#page element
			q = adventureModel.PageElement.all().filter('adventure =', adventure)
			a = q.fetch(9999)
			output += "Admin get: delete story: deleted %d records from PageElement<br>" % len(a)
			db.delete(a)
			#image
			q = adventureModel.Image.all().filter('adventure =', adventure)
			a = q.fetch(9999)
			output += "Admin get: delete story: deleted %d records from Image<br>" % len(a)
			db.delete(a)
			#page
			q = adventureModel.Page.all().filter('adventure =', adventure)
			a = q.fetch(9999)
			output += "Admin get: delete story: deleted %d records from Page<br>" % len(a)
			db.delete(a)
			#adventure
			adventure.delete()
			output += "Admin get: delete story: deleted %d records from Adventure<br>" % 1
			db.delete(a)
			memcache.delete("adventures")
			memcache.delete(var)

	defaultTemplateValues = main.getDefaultTemplateValues(self)
	templateValues = {
		'title': 'Admin',
		'output': output,
	}
	templateValues = dict(defaultTemplateValues, **templateValues)

	path = os.path.join(os.path.dirname(__file__), 'admin.html')
	self.response.out.write(template.render(path, templateValues))
