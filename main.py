import os
from google.appengine.ext.webapp import template
import cgi
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
import adventureModel
import addAdventure
import index
import myStories
import addPage
import storyEditor
import pageElement
import upload

def printHeader(self):

	addAdventureURL = '/addAdventure'
	addAdventure = 'Create New Story'
	myStoriesURL = '/myStories'
	myStories = 'My Stories'
	loggedIn = ''
	currentUser = users.get_current_user()

	if users.get_current_user():
		loginURL = users.create_logout_url(self.request.uri)
		login = 'Logout'
		loggedIn = True
	else:
		loginURL = users.create_login_url(self.request.uri)
		login = 'Login'

	template_values = {
		'currentUser': currentUser,
		'loggedIn': loggedIn,
		'loginURL': loginURL,
		'login': login,
		'addAdventureURL': addAdventureURL,
		'addAdventure': addAdventure,
		'myStoriesURL': myStoriesURL,
		'myStories': myStories
	}
	path = os.path.join(os.path.dirname(__file__), 'mainHeader.html')
	self.response.out.write(template.render(path, template_values))

def printFooter(self, template_values):
	path = os.path.join(os.path.dirname(__file__), 'mainFooter.html')
	self.response.out.write(template.render(path, template_values))

application = webapp.WSGIApplication(
	[
		('/', index.Index),
		('/addAdventure', addAdventure.AddAdventure),
		('/myStories', myStories.MyStories),
		('/addPage', addPage.AddPage),
		('/deletePage', addPage.DeletePage),
		('/storyEditor', storyEditor.StoryEditor),
		('/getPages', storyEditor.GetPages),
		('/addPageElement', pageElement.AddPageElement),
		('/disablePageElement', pageElement.DisablePageElement),
		('/deletePageElement', pageElement.DeletePageElement),
		('/savePageElement', pageElement.SavePageElement),
		('/imageManager', upload.ImageManager),
		('/movePageElement', pageElement.MovePageElement),
	],
	debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()