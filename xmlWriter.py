import os
from google.appengine.ext.webapp import template
import cgi
import logging
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.api import memcache
import adventureModel
import main
import admin
import index
import myStories
import signup

class MyStoriesXML(webapp.RequestHandler):
  def get(self, deviceID=None):
	#this is to handle myStories for the iPhone
	#it takes the persons iPhone ID instead of a user,
	#so we have to look up the user from the iphoneLink table
	shares = None
	output = None
	if not deviceID:
		deviceID = self.request.get("deviceID")
	if not deviceID:
		logging.info("MyStoriesXML requires deviceID")
	else:
		user = signup.getUserFromDeviceID(deviceID)
		logging.info("MyStoriesXML: getting stories for %s %s" % (deviceID, user))
	if user:
		cacheString = 'myStoriesXML' + user.email()
		output = memcache.get(cacheString)
		if output:
			logging.info("MyStoriesXML: got stories from cache for %s %s" % (deviceID, user))
		else:
			#build the xml string
			shares = myStories.getMyShares(user)
			output = ''
			cnt = 0
			for share in shares:
				cnt = cnt + 1
				output += share.toXML()
			output = '<xml>\n%s</xml>' % output
			memcache.add(cacheString, output, 300)
			logging.info("MyStoriesXML: got %d stories from db for %s %s" % (cnt, deviceID, user))
	if not output:
		logging.info("MyStoriesXML: user did not have any stories: %s %s" % (deviceID, user))
		output = '<xml>\n</xml>'
	self.response.headers['Content-Type'] = 'text/plain'
	self.response.out.write(output)

class XmlWriter(webapp.RequestHandler):
  def get(self, myAdventureKey=None, myPageKey=None):
	logging.info("XmlWriter: myAdventureKey(%s) myPageKey(%s)" % (myAdventureKey, myPageKey))
	output = None
	cacheString = None
	if not myAdventureKey and not myPageKey:
		#main entry point, just get the list of advenures
		cacheString = 'xmlMainRatings'
		output = memcache.get(cacheString)
		if output:
			logging.info("XmlWriter: got main ratings from cache")
		else:
			#get approved adventures
			output = ''
			ratings = index.getRatings()
			for rating in ratings:
				output += rating.toXML()
			output = "<xml>\n%s</xml>" % output
			memcache.add(cacheString, output, 86400)
			logging.info("XmlWriter: got main ratings from db")
	elif myAdventureKey and myPageKey == 'files.xml':
		#get the list of pages for this adventure
		adventure = main.getAdventure(myAdventureKey)
		firstPage = None
		if not adventure:
			logging.warn("XmlWriter: could not fetch adventure with key: " + myAdventureKey)
			return
		cacheString = 'XmlPages' + myAdventureKey
		output = memcache.get(cacheString)
		if output:
			logging.info("XmlWriter: got pages for adventure %s from cache" % myAdventureKey)
		else:
			output = "<version>%.4f</version>\n" % adventure.version
			adventureStatus = main.getAdventure(adventure.adventureStatus)
			if not adventureStatus:
				logging.warn("XmlWriter: could not fetch adventureStatus with key: " + adventure.adventureStatus)
				return
			for image in adventureStatus.images:
				output += image.toXML()
			for page in adventure.pages.order('created'):
				if not firstPage:
					firstPage = str(page.key())
				output += page.pageHeaderToXML()
			output += "<firstPage>%s.xml</firstPage>\n" % firstPage
			output = "<xml>\n%s</xml>" % output
			#if adventure is the editable one, set the duration to 300
			cacheDuration = 86400
			if adventure.key() == adventureStatus.editableAdventure.key():
				cacheDuration = 300
			memcache.add(cacheString, output, 86400)
			logging.info("XmlWriter: got pages for adventure %s from db, set cache duration to %d" % (myAdventureKey, cacheDuration))
	elif myPageKey:
		#get the page data for this page
		cacheString = 'XmlPage' + myPageKey
		output = memcache.get(cacheString)
		if output:
			logging.info("XmlWriter: got page %s from cache" % myPageKey)
		else:
			output = ''
			page = main.getPage(myPageKey)
			if not page:
				logging.warn("XmlWriter: could not fetch page with key: " + myPageKey)
				return
			for pageElement in page.pageElements.order('pageOrder'):
				output += "   " + pageElement.toXML() + "\n"
			output = "<xml>\n%s</xml>" % output
			adventureStatus = main.getAdventure(page.adventure.adventureStatus)
			#if adventure is the editable one, set the duration to 300
			cacheDuration = 86400
			if page.adventure.key() == adventureStatus.editableAdventure.key():
				cacheDuration = 300
			memcache.add(cacheString, output, 300)
			logging.info("XmlWriter: got page %s from db, set cache duration to %d" % (myPageKey, cacheDuration))

	self.response.headers['Content-Type'] = 'text/plain'
	self.response.out.write(output)