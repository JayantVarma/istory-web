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
  def getMyAdventures(self, myUser):
	adventures = memcache.get("adventures_" + myUser.email())
	if adventures is not None:
		return adventures
	else:
		adventures_query = adventureModel.Adventure.all()
		adventures_query.filter('realAuthor = ', myUser)
		adventures_query.order('-created')
		adventures = adventures_query.fetch(9999)
		if not memcache.add("adventures_" + myUser.email(), adventures, 300):
			logging.error("memcache set failed.")
		return adventures

  def get(self):
	myUser = users.get_current_user()
	if myUser:
		pass
	else:
		url = users.create_login_url(self.request.uri)
		self.redirect(url)
		return

	adventures = self.getMyAdventures(myUser)
	
	#get any pending share invites
	q = adventureModel.Share.all().filter('status =', 1).filter('childEmail =', users.get_current_user().email()).order('-created')
	shareInvites = q.fetch(9999)
	logging.info("got %d invites for user %s" % (len(shareInvites), users.get_current_user().email()))

	defaultTemplateValues = main.getDefaultTemplateValues(self)
	templateValues = {
		'title': 'My Stories',
		'adventures': adventures,
		'shareInvites': shareInvites
	}
	templateValues = dict(defaultTemplateValues, **templateValues)

	path = os.path.join(os.path.dirname(__file__), 'myStories.html')
	self.response.out.write(template.render(path, templateValues))
	