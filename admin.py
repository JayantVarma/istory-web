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
from google.appengine.api import mail
from django.utils import simplejson
import adventureModel
import main

def deleteAdventureStatus(adventureStatus):
	if not adventureStatus:
		logging.warn("deleteAdventureStatus: adventureStatus is required")
		return
	logging.info("deleteAdventureStatus: start " + str(adventureStatus.key()))
	output = "deleteAdventureStatus: start " + str(adventureStatus.key())
	#loop through all the adventures and delete them
	try:
		if adventureStatus.submittedAdventure:
			logging.info("deleteAdventureStatus: deleting submittedAdventure")
			adventureStatus.submittedAdventure = None
			output += deleteAdventure(adventureStatus.submittedAdventure, False)
	except Exception, e:
		None
	try:
		if adventureStatus.editableAdventure:
			logging.info("deleteAdventureStatus: deleting editableAdventure")
			adventureStatus.editableAdventure = None
			output += deleteAdventure(adventureStatus.editableAdventure, False)
	except Exception, e:
		None
	try:
		if adventureStatus.publishedAdventure:
			logging.info("deleteAdventureStatus: deleting publishedAdventure")
			adventureStatus.publishedAdventure = None
			output += deleteAdventure(adventureStatus.publishedAdventure, False)
	except Exception, e:
		None
	#delete the ratings
	cnt = 0
	for rating in adventureStatus.ratings:
		cnt = cnt + 1
		rating.delete()
	output += "   deleted %d records from ratings<br>" % cnt
	#delete the images
	cnt = 0
	for image in adventureStatus.images:
		cnt = cnt + 1
		image.delete()
		try:
			memcache.delete('img' + str(image.key()))
		except Exception, e:
			None
	output += "   deleted %d records from images<br>" % cnt
	#delete the votes
	cnt = 0
	for vote in adventureStatus.votes:
		cnt = cnt + 1
		vote.delete()
	output += "   deleted %d records from votes<br>" % cnt
	#finish up
	memcache.delete("xmlMainRatings")
	memcache.delete("adventures")
	adventureStatus.delete()
	output += "   done"
	logging.info("deleteAdventureStatus: done")
	return output

def deleteAdventure(adventure, deleteAdventureStatusKey = True):
	output = None
	if not adventure:
		logging.warn("deleteAdventure: adventure is required")
		return
	logging.info("deleteAdventure: start " + str(adventure.key()))
	#share
	q = adventureModel.Share.all().filter('adventure =', adventure)
	a = q.fetch(9999)
	#delete the adventure shares cache
	for share in a:
		memcache.delete('adventures_' + share.child.email())
		memcache.delete('images' + share.child.email())
	output = "Admin get: delete story: deleted %d records from Share<br>" % len(a)
	db.delete(a)
	#page element
	q = adventureModel.PageElement.all().filter('adventure =', adventure)
	a = q.fetch(9999)
	output += "Admin get: delete story: deleted %d records from PageElement<br>" % len(a)
	db.delete(a)
	##image
	#q = adventureModel.Image.all().filter('adventure =', adventure)
	#a = q.fetch(9999)
	#output += "Admin get: delete story: deleted %d records from Image<br>" % len(a)
	#db.delete(a)
	#page
	q = adventureModel.Page.all().filter('adventure =', adventure)
	a = q.fetch(9999)
	output += "Admin get: delete story: deleted %d records from Page<br>" % len(a)
	db.delete(a)
	#adventure status
	#we need to go through the adventure status record and set this adventure to null
	foundAdventures = 0
	adventureStatus = db.Model.get(adventure.adventureStatus)
	if adventureStatus:
		try:
			if adventureStatus.submittedAdventure and adventureStatus.submittedAdventure == adventure:
				adventureStatus.submittedAdventure = None
		except Exception, e:
			None
		try:
			if adventureStatus.editableAdventure and adventureStatus.editableAdventure == adventure:
				adventureStatus.editableAdventure = None
		except Exception, e:
			None
		try:
			if adventureStatus.publishedAdventure and adventureStatus.publishedAdventure == adventure:
				adventureStatus.publishedAdventure = None
		except Exception, e:
			None
		adventureStatus.put()
		#now figure out how many adventures this adventureStatus has left
		try:
			if adventureStatus.editableAdventure:
				foundAdventures = foundAdventures + 1
		except Exception, e:
			None
		try:
			if adventureStatus.submittedAdventure:
				foundAdventures = foundAdventures + 1
		except Exception, e:
			None
		try:
			if adventureStatus.publishedAdventure:
				foundAdventures = foundAdventures + 1
		except Exception, e:
			None
	output += "Admin get: delete story: this adventureStatus has %d adventures left<br>" % foundAdventures
	#if we only have 0 adventures left in this adventureStatus, we need to delete it
	#we'll do that at the end

	##votes
	#q = adventureModel.UserVotes.all().filter('adventureStatus =', adventureStatus)
	#a = q.fetch(9999)
	#output += "Admin get: delete story: deleted %d records from UserVotes<br>" % len(a)
	#db.delete(a)
	##adventureRating
	#q = adventureModel.AdventureRating.all().filter('adventureStatus =', adventureStatus)
	#a = q.fetch(9999)
	#output += "Admin get: delete story: deleted %d records from AdventureRating<br>" % len(a)
	#db.delete(a)
	##adventureStatus
	#adventureStatus.delete()
	#output += "Admin get: delete story: deleted %d records from AdventureStatus<br>" % 1
	#memcache.delete('advStat' + str(adventure.key()))
	#adventure
	output += "Admin get: delete story: deleted %d records from Adventure<br>" % 1
	memcache.delete(str(adventure.key()))
	memcache.delete('pages' + str(adventure.key()))
	memcache.delete('XmlPages' + str(adventure.key()))
	memcache.delete("adventures")
	memcache.delete("xmlMainRatings")
	if adventure.adventureStatus:
		memcache.delete(adventure.adventureStatus)
	adventure.delete()
	if foundAdventures == 0 and deleteAdventureStatusKey and adventureStatus:
		#delete the adventureStatus record
		logging.info("deleteAdventure: deleting adventureStatus record as well")
		output += "DELETING ADVENTURE STATUS NOW"
		output += deleteAdventureStatus(adventureStatus)
	logging.info('deleteAdventure: done')
	logging.info(output)
	return output

def duplicateAdventure(adventure):
	if not adventure:
		return None
	#Adventure
	newAdventure = adventureModel.Adventure()
	newAdventure.title =       adventure.title
	newAdventure.realAuthor =  adventure.realAuthor
	newAdventure.author =      adventure.author
	newAdventure.desc =        adventure.desc
	newAdventure.version =     adventure.version
	newAdventure.approved = -1
	newAdventure.adventureStatus = adventure.adventureStatus
	newAdventure.created =     adventure.created
	newAdventure.modified =    adventure.modified
	newAdventure.coverImage =  adventure.coverImage
	newAdventure.put()
	#Page & PageElement
	oldPageToNewPageMap = {}
	newPageToOldPageMap = {}
	q = adventureModel.Page.all().filter('adventure =', adventure).order('created')
	pages = q.fetch(9999)
	for page in pages:
		newPage = adventureModel.Page()
		newPage.adventure = newAdventure
		newPage.name = page.name
		newPage.created = page.created
		newPage.modified = page.modified
		newPage.put()
		oldPageToNewPageMap[str(page.key())] = newPage
		logging.info("oldPageToNewPageMap [%s] %s -> %s" % (page.name, str(page.key()), str(newPage.key())))
	#now that we have the full mapping of old pages to new pages, go through the page list again and copy the page elements
	for page in pages:
		#now do the page elements for this page
		q2 = adventureModel.PageElement.all().filter('adventure =', adventure).filter('page =', page)
		pageEls = q2.fetch(9999)
		for pageEl in pageEls:
			newPageEl = adventureModel.PageElement()
			newPageEl.adventure = newAdventure
			newPageEl.page = oldPageToNewPageMap[str(page.key())]
			newPageEl.dataType = pageEl.dataType
			newPageEl.pageOrder = pageEl.pageOrder
			newPageEl.dataA = pageEl.dataA
			if pageEl.dataType == 3:
				newPageEl.dataB = str(oldPageToNewPageMap[pageEl.dataB].key())
				logging.info("[%s] got choice: changing old link(%s) to new link(%s)" % (page.name, pageEl.dataB, newPageEl.dataB))
			else:
				newPageEl.dataB = pageEl.dataB
			newPageEl.imageRef = pageEl.imageRef
			newPageEl.enabled = pageEl.enabled
			newPageEl.created = pageEl.created
			newPageEl.modified = pageEl.modified
			newPageEl.put()
	#Image
	# we don't need to do image, since you cant really edit those
	return newAdventure

def getAdventureStatus(key):
	adventureStatus = None
	#first try to get it from the cache
	adventureStatus = memcache.get(key)
	if adventureStatus:
		logging.info('getAdventureStatus: got record from cache')
	else:
		#try to get it from the db
		adventureStatus = db.Model.get(key)
		if adventureStatus:
			#add it to the cache
			logging.info('getAdventureStatus: got record from db')
			memcache.add(key, adventureStatus, 86400)
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
			adventureStatus = getAdventureStatus(adventure.adventureStatus)
			if not adventureStatus:
				logging.warn("Submit: could not found adventureStatus record: " + myAdventureKey)
			else:
				logging.info('Submit: got adventureStatus record')
	
	#if we have a submitFlag, then we're trying to submit the form
	if submitFlag and adventure and adventureStatus:
		logging.info("Submit: submit flag was set. comment(%s)" % comment)
		#delete the previous submitted adventure
		submittedAdventure = adventureStatus.submittedAdventure
		memcache.delete(str(adventureStatus.key()))
		if submittedAdventure:
			deleteAdventure(submittedAdventure)
		#now duplicate the story
		adventureStatus.submittedAdventure = duplicateAdventure(adventure)
		if adventureStatus.submittedAdventure:
			comment = 'Your story has been submitted.'
			adventureStatus.status = 2
			adventureStatus.comment = submitComment
			adventureStatus.put()
			#reset the cache
			memcache.delete('advStat' + str(adventure.key()))
			#send an email to the admins
			body = '''%s (%s) has just submitted a story for approval.
Title: %s
Author: %s
RealAuthor: %s
Description: %s

Check it out at: http://istoryweb.appspot.com/admin
''' % (users.get_current_user().email(), users.get_current_user().nickname(), adventure.title, adventure.author, adventure.realAuthor, adventure.desc)
			mail.send_mail(users.get_current_user().email(), 'tsteil+istory@gmail.com', users.get_current_user().nickname() + ' has just submitted a story for approval', body)
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
  def post(self):
	if not users.is_current_user_admin():
		return
	myAdventureStatusKey = self.request.get('myStatusKey')
	approved = self.request.get('approved')
	adminComment = self.request.get('adminComment')
	logging.info("Admin post: statusKey(%s) approved(%s) adminComment(%s)" % (myAdventureStatusKey, approved, adminComment))
	#get the AdventureStatus record
	adventureStatus = getAdventureStatus(myAdventureStatusKey)
	if not adventureStatus:
		logging.warn("Admin post: could not find adventure status key: " + myAdventureStatusKey)
	#if approved
	if approved == "yes":
		#apply the editor comment and approve this record
		adventureStatus.editorComment = adminComment
		adventureStatus.status = 3
		#delete the published adventure and change the submitted adventure to the published adventure
		if adventureStatus.publishedAdventure:
			deleteAdventure(adventureStatus.publishedAdventure)
		adventureStatus.publishedAdventure = adventureStatus.submittedAdventure
		adventureStatus.submittedAdventure = None
		#increment the version number
		adventureStatus.version = adventureStatus.version + 1.0
		adventureStatus.editableAdventure.version = adventureStatus.version
		adventureStatus.publishedAdventure.version = adventureStatus.version
		#approve the published adventure
		adventureStatus.publishedAdventure.approved = 1
		#save the record
		adventureStatus.put()
		adventureStatus.editableAdventure.put()
		adventureStatus.publishedAdventure.put()
		#find the adventureRating record and set it to approved as well
		for rating in adventureStatus.ratings:
			rating.approved = 1
			rating.put()
	#if not approved
	if approved == "no":
		#apply the editor comment and deny this record
		adventureStatus.editorComment = adminComment
		adventureStatus.status = -1
		#save the record
		adventureStatus.put()
	self.response.out.write("Success: this adventure has been changed to approval status '%s'" % approved)
	#clear out some memcache records
	memcache.delete("xmlMainRatings")
	memcache.delete('XmlPages' + str(adventureStatus.publishedAdventure.key()))
	memcache.delete("adventures")
	memcache.delete(str(adventureStatus.editableAdventure.key()))
	memcache.delete(str(adventureStatus.publishedAdventure.key()))
	memcache.delete(str(adventureStatus.key()))

  def get(self):
	if not users.is_current_user_admin():
		return
	myAdventureKey = self.request.get('myAdventureKey')
	command = self.request.get('command')
	var = self.request.get('var')
	var2 = self.request.get('var2')
	logging.info("Admin get: myAdventureKey(%s)" % (myAdventureKey))
	output = "Admin get: myAdventureKey(%s) command(%s) var(%s) var2(%s)<br>" % (myAdventureKey, command, var, var2)
	memcache.delete("adventures")
	memcache.delete("xmlMainRatings")

	if command == 'delete story collection' and var:
		#this will delete all story data for a given adventureStatus
		adventure = None
		logging.info("Admin get: delete adventureStatus: " + var)
		output += "Admin get: delete adventureStatus: " + var + "<br>"
		try:
			adventure = db.Model.get(var)
		except Exception, e:
			output += "Admin get: delete adventureStatus: exception: " + str(e) + "<br>"
		if not adventure:
			logging.info("Admin get: delete adventureStatus: adventure key not found in DB")
			output += "Admin get: delete adventureStatus: adventure key not found in DB<br>"
		else:
			#get the adventureStatus and delete it
			adventureStatus = db.Model.get(adventure.adventureStatus)
			output += deleteAdventureStatus(adventureStatus)
			memcache.delete(var)
	elif command == 'delete story' and var:
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
			output += deleteAdventure(adventure)
			memcache.delete(var)
	elif command == 'move pages' and var and var2:
		#this will move pages from var to var2
		adventure = db.Model.get(var)
		adventure2 = db.Model.get(var2)
		pageCounter = 0
		pageElCounter = 0
		if adventure and adventure2:
			for page in adventure.pages:
				page.adventure = adventure2
				page.put()
				pageCounter = pageCounter + 1
				for pageElement in page.pageElements:
					pageElement.adventure = adventure2
					pageElement.put()
					pageElCounter = pageElCounter + 1
		output += "Admin get: move pages: moved %d pages and %d page elements" % (pageCounter, pageElCounter)
		memcache.delete(var)
		memcache.delete(var2)
		memcache.delete('pages' + var)
		memcache.delete('pages' + var2)
		memcache.delete('XmlPages' + var)
		memcache.delete('XmlPages' + var2)
	elif command == 'purge unused images':
		#this will check every image to make sure it is used
		#if not, it deletes it
		q = adventureModel.Image.all()
		images = q.fetch(9999)
		n = 0
		for image in images:
			n = n + 1
			myOutput = None
			#if adventure or adventureStatus is null, delete it
			try:
				if image.adventure and image.adventureStatus:
					myOutput = "%d: not going to delete: %s<br>" % (n, image.imageName)
				else:
					myOutput = "%d: going to delete: %s<br>" % (n, image.imageName)
					memcache.delete('img' + str(image.key()))
					image.delete()
			except Exception, e:
				myOutput = "%d: *** exception ***: %s<br>" % (n, image.imageName)
				memcache.delete('img' + str(image.key()))
				image.delete()
			output += myOutput
		#remove cached images
		q = adventureModel.Share.all()
		roles = q.fetch(9999)
		n = 0
		for role in roles:
			if role.child:
				n = n + 1
				memcache.delete("images" + role.child.email())
		output += "<br>removed %d user images cache entries<br>" % n

	#show any stories waiting to be approved
	q = adventureModel.AdventureStatus.all().filter('status =', 2)
	adventureStatuses = q.fetch(9999)

	defaultTemplateValues = main.getDefaultTemplateValues(self)
	templateValues = {
		'title': 'Admin',
		'output': output,
		'adventureStatuses': adventureStatuses,
	}
	templateValues = dict(defaultTemplateValues, **templateValues)

	path = os.path.join(os.path.dirname(__file__), 'admin.html')
	self.response.out.write(template.render(path, templateValues))




