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
import addAdventure
import index
import myStories
import storyEditor
import pageElement
import images
import playStory
import share
import admin
import ratings
import xmlWriter

def getPage(key):
	#this returns an adventure object from the cache (if it exists there) or from the db (and then adds it to the cache)
	if not key:
		logging.error("ERROR: getPage called with no key")
		return None
	adventure = memcache.get(key)
	if adventure:
		logging.info("got page from cache: " + key)
		return adventure
	adventure = db.Model.get(key)
	if adventure:
		logging.info("got page from db: " + key)
		memcache.add(key, adventure, 3600)
		return adventure
	return None

def getAdventure(key):
	#this returns an adventure object from the cache (if it exists there) or from the db (and then adds it to the cache)
	if not key:
		logging.error("ERROR: getAdventure called with no key")
		return None
	adventure = memcache.get(key)
	if adventure:
		logging.info("got adventure from cache: " + key)
		return adventure
	adventure = db.Model.get(key)
	if adventure:
		logging.info("got adventure from db: " + key)
		memcache.add(key, adventure, 3600)
		return adventure
	return None

def isUserAdmin(user, adventure):
	if isUserSomething(user, adventure, 3):
		return True
	return False
def isUserAuthor(user, adventure):
	if isUserSomething(user, adventure, 2):
		return True
	return False
def isUserReader(user, adventure):
	return True
	if isUserSomething(user, adventure, 1):
		return True
	return False

def isUserSomething(user, adventure, role):
	share = None
	if not user or not adventure or not role:
		logging.info("isUserSomething: function requires 3 arguments, user & adventure & role")
		return False
	#if user is admin, just return true
	if users.is_current_user_admin():
		return True
	#format for cache string is role,email,adventureKey
	cacheString = str(role) + ',' + user.email() + ',' + str(adventure.key())
	logging.info("isUserSomething: cacheString: " + cacheString)
	share = memcache.get(cacheString)
	if share is not None and share != "None":
		logging.info("isUserSomething: fetched share from cache. user has this role")
		return True
	elif share is not None and share == "None":
		logging.info("isUserSomething: user does not have this role (from cache)")
		return False
	else:
		q = adventureModel.Share.all().filter('adventure =', adventure).filter('role >=', role).filter('child =', user)
		shares = q.fetch(1)
		for myShare in shares:
			share = myShare
		if share is not None:
			#user has this role
			logging.info("isUserSomething: fetched share from db. user has this role")
			#add cache entries for the other roles, if necessary
			#admin adds cache entries for both author and reader
			#author adds cache entries for reader
			for n in range(0, role):
				cacheString = str(n+1) + ',' + user.email() + ',' + str(adventure.key())
				logging.info("isUserSomething: adding cache record: " + cacheString)
				if not memcache.add(cacheString, share, 3600):
					logging.info("memcache set failed.")
			#done
			return True
	#user does not have this role
	logging.info("isUserSomething: user does not have this role (not from cache)")
	if not memcache.add(cacheString, "None", 3600):
		logging.info("isUserSomething false memcache set failed.")
	return False

def getDefaultTemplateValues(self):
	myStoriesURL = '/myStories'
	myStories = 'My Stories'
	
	loggedIn = None
	currentUser = users.get_current_user()
	if users.get_current_user():
		loginURL = users.create_logout_url(self.request.uri)
		login = 'Logout'
		loggedIn = True
	else:
		loginURL = '/myStories'
		login = 'Login to access the <b>StoryForge</b> and begin creating your adventure!'
#		loginURL = users.create_login_url(self.request.uri)
#		login = 'Login'

	stats = memcache.get_stats()
	templateValues = {
		'currentUser': currentUser,
		'loggedIn': loggedIn,
		'loginURL': loginURL,
		'login': login,
		'myStoriesURL': myStoriesURL,
		'myStories': myStories,
		'title': 'Home',
		'cacheHits': stats['hits'],
		'cacheMisses': stats['misses']
	}
	
	return templateValues


application = webapp.WSGIApplication(
	[
		('/', index.Index),
		('/xml/signup', admin.Signup),
		(r'^/xml/.+?/data/(.+?)\.png$', images.ImageServer),
		(r'^/xml/(.+?)/data/(.+?)\.xml$', xmlWriter.XmlWriter),
		(r'^/xml/(.+?)/(files\.xml)$', xmlWriter.XmlWriter),
		(r'^/xml/adventures\.xml?$', xmlWriter.XmlWriter),
		('/admin', admin.Admin),
		('/submit', admin.Submit),
		('/vote', ratings.Vote),
		('/share', share.ViewSharing),
		('/removeShare', share.RemoveShare),
		('/shareInvite', share.ShareInvite),
		('/playStory', playStory.Play),
		('/createStory', addAdventure.AddAdventure),
		('/myStories', myStories.MyStories),
		('/addPage', storyEditor.AddPage),
		('/deletePage', storyEditor.DeletePage),
		('/storyEditor', storyEditor.StoryEditor),
		('/getPages', storyEditor.GetPages),
		('/addPageElement', pageElement.AddPageElement),
		('/disablePageElement', pageElement.DisablePageElement),
		('/deletePageElement', pageElement.DeletePageElement),
		('/savePageElement', pageElement.SavePageElement),
		('/movePageElement', pageElement.MovePageElement),
		('/imageManager', images.ImageManager),
		('/upload', images.Uploader),
		(r'^/images/(.+?).png$', images.ImageServer),
		('/images', images.ImageServer),
		('/imagesByUser', images.ImagesByUser),
		('/imageCropper', images.ImageCropper),
	],
	debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()