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
import adventureModel
import addAdventure
import main
import storyEditor

class MyStories(webapp.RequestHandler):
  def getMyShares(self, myUser):
	shares = memcache.get("adventures_" + myUser.email())
	if shares is not None:
		logging.info("getMyShares: cache was used to return %d shares" % len(shares))
		return shares
	else:
		q = adventureModel.Share.all()
		q.filter('child =', myUser)
		q.filter('status >=', 2)
		q.order('-status')
		q.order('-role')
		q.order('-created')
		shares = q.fetch(9999)
		#now go through the shares and only keep the first instance of every adventure
		myShares = []
		myAdventures = set()
		for share in shares:
			if not str(share.adventure.key()) in myAdventures:
				#adventure does not already exists, add it to the list
				myAdventures.add(str(share.adventure.key()))
				myShares.append(share)
			else:
				#adventure already exists
				logging.info("MyStories getMyShares: multiple role detected adventure(%s) role(%s)" % (share.adventure.key(), share.roleName()))
		if not memcache.add("adventures_" + myUser.email(), myShares, 3600):
			logging.info("memcache set failed.")
		logging.info("getMyShares: db was used to return %d shares" % len(myShares))
		return myShares

  def get(self):
	myUser = users.get_current_user()
	if myUser:
		pass
	else:
		url = users.create_login_url(self.request.uri)
		self.redirect(url)
		return

	shares = self.getMyShares(myUser)
	
	#get any pending share invites
	shareInvites = None
	shareInviteCacheString = "invites_" + users.get_current_user().email()
	shareInvites = memcache.get(shareInviteCacheString)
	if shareInvites and shareInvites != "None":
		logging.info("got %d invites from cache for user %s" % (len(shareInvites), users.get_current_user().email()))
	elif shareInvites and shareInvites == "None":
		logging.info("got 0 invites from cache for user %s" % users.get_current_user().email())
		shareInvites = None
	else:
		q = adventureModel.Share.all().filter('status =', 1).filter('childEmail =', users.get_current_user().email()).order('-created')
		shareInvites = q.fetch(9999)
		if shareInvites:
			if not memcache.add(shareInviteCacheString, shareInvites, 3600):
				logging.info("myStories shareInvites true memcache set failed.")
		else:
			if not memcache.add(shareInviteCacheString, "None", 3600):
				logging.info("myStories shareInvites false memcache set failed.")
		logging.info("got %d invites from db for user %s" % (len(shareInvites), users.get_current_user().email()))

	defaultTemplateValues = main.getDefaultTemplateValues(self)
	templateValues = {
		'title': 'My Stories',
		'shares': shares,
		'shareInvites': shareInvites
	}
	templateValues = dict(defaultTemplateValues, **templateValues)

	path = os.path.join(os.path.dirname(__file__), 'myStories.html')
	self.response.out.write(template.render(path, templateValues))
	