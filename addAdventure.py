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
from google.appengine.api import images
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
		adventure = main.getAdventure(myAdventureKey)
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
	adventure.approved = 0
	adventure.version = 0.0
	adventure.put()
	#we dont want to delete the cache of ratings because this adventure won't be approved or rated yet
	#memcache.delete("ratings")
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
		#now create the adventureStatus record
		adventureStatus = adventureModel.AdventureStatus()
		adventureStatus.editableAdventure = adventure
		adventureStatus.status = 1
		adventureStatus.version = 0.0
		adventureStatus.put()
		#save the adventureStatus key back to the adventure record
		adventure.adventureStatus = str(adventureStatus.key())
		adventure.put()
		#now create the rating record for this adventure
		rating = adventureModel.AdventureRating()
		rating.adventureStatus = adventureStatus
		rating.voteCount = 0
		rating.voteSum = 0
		rating.plays = 0
		rating.approved = 0
		rating.rating = 0.0
		rating.put()
	#handle the coverImage
	newCoverImage = self.request.get('coverImage')
	oldCoverImage = adventure.coverImage
	if newCoverImage:
		myImageSizeBytes = len(newCoverImage)
		logging.info("GOT IMAGE DATA!! " + str(myImageSizeBytes) + ' bytes.')
		if myImageSizeBytes > 1048576:
			logging.info("ERROR: Image was too large(%d bytes). 1 megabyte is the max size." % (myImageSizeBytes))
			self.response.out.write("ERROR: Image was too large. 1 megabyte is the max size.")
			return
		if len(newCoverImage) > 100:
			logging.info("AddAdventure: got new cover image")
			imageOBJ = images.Image(newCoverImage)
			#resize to 320x150
			imageOBJ.resize(320, 150)
			newImage = adventureModel.Image()
			newImage.imageData = imageOBJ.execute_transforms()
			#setup the rest of the image metadata
			newImage.adventure = adventure
			if adventure.adventureStatus:
				adventureStatus = main.getAdventure(adventure.adventureStatus)
				if adventureStatus:
					newImage.adventureStatus = adventureStatus
			if not newImage.adventureStatus:
				logging.warn("AddAdventure: trying to use new coverImage and adventureStatus could not be found")
			newImage.pageElement = "coverImage"
			newImage.imageName = "Cover Image"
			newImage.realAuthor = users.get_current_user()
			newImage.put()
			adventure.coverImage = str(newImage.key())
			adventure.put()
			#delete the old cover image if it exists and no page elements are using it
			if oldCoverImage:
				oldCoverImage = db.Model.get(oldCoverImage)
				if oldCoverImage:
					deleteFlag = True
					for pageElement in oldCoverImage.pageElements:
						deleteFlag = False
						logging.info("AddAdventure: not deleting old cover image because it is in use by a page element")
						break
					#also check the editable, submitted, and published adventure on this adventureStatus
					if adventureStatus.editableAdventure:
						if adventureStatus.editableAdventure.coverImage == str(oldCoverImage.key()):
							deleteFlag = False
					if adventureStatus.submittedAdventure:
						if adventureStatus.submittedAdventure.coverImage == str(oldCoverImage.key()):
							deleteFlag = False
					if adventureStatus.publishedAdventure:
						if adventureStatus.publishedAdventure.coverImage == str(oldCoverImage.key()):
							deleteFlag = False
					if deleteFlag:
						logging.info("AddAdventure: deleting old cover image")
						oldCoverImage.delete()
	
	#remove the cache object for all users who have a role for this adventure
	q = adventureModel.Share.all().filter('adventure =', adventure)
	shares = q.fetch(9999)
	logging.info("AddAdventure: removed %d cache objects" % len(shares))
	for share in shares:
		if share.child:
			memcache.delete("adventures_" + share.child.email())
	logging.info("addAdventure: deleting memcache object: " + str(adventure.key()))
	memcache.delete(str(adventure.key()))
	
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
			adventure = main.getAdventure(myAdventureKey)
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
