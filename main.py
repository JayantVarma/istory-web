import os
from google.appengine.ext.webapp import template
import cgi
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
		('/images', images.ImageServer),
		('/imagesByUser', images.ImagesByUser),
		('/imageCropper', images.ImageCropper),
	],
	debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()