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
		output = "<version>%f</version>\n" % adventure.version
		adventureStatus = main.getAdventure(adventure.adventureStatus)
		if not adventureStatus:
			logging.warn("XmlWriter: could not fetch adventureStatus with key: " + adventure.adventureStatus)
			return
		for image in adventureStatus.images:
			output += image.toXML()
		for page in adventure.pages:
			if not firstPage:
				firstPage = str(page.key())
			output += page.pageHeaderToXML()
		output += "<firstPage>%s</firstPage>\n" % firstPage
		output = "<xml>\n%s</xml>" % output
	elif myPageKey:
		#get the page data for this page
		output = ''
		page = main.getPage(myPageKey)
		if not page:
			logging.warn("XmlWriter: could not fetch page with key: " + myPageKey)
			return
		for pageElement in page.pageElements:
			output += "   " + pageElement.toXML() + "\n"
		output = "<xml>\n%s</xml>" % output

	self.response.headers['Content-Type'] = 'text/plain'
	self.response.out.write(output)