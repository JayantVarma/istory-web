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
		adventures_query.order('-date')
		adventures = adventures_query.fetch(10)
		if not memcache.add("adventures_" + myUser.email(), adventures, 300):
			logging.error("memcache set failed.")
		return adventures

  def get(self):
	myUser = users.get_current_user()
	if myUser:
		pass
	else:
		url = users.create_login_url(self.request.uri)
		url_linktext = 'Please login to see your adventures.'
		template_values = {
			'url': url,
			'url_linktext': url_linktext,
		}
		main.printHeader(self)
		path = os.path.join(os.path.dirname(__file__), 'pleaseLogin.html')
		self.response.out.write(template.render(path, template_values))
		main.printFooter(self)
		return

	adventures = self.getMyAdventures(myUser)
	stats = memcache.get_stats()
	#newlineRE = re.compile('\n')
	#for adventure in adventures:
	#	adventure.desc = newlineRE.sub('<br>\n', adventure.desc)

	template_values = {
		'adventures': adventures,
	}
	footer_template_values = {
		'cacheHits': stats['hits'],
		'cacheMisses': stats['misses'],
	}

	main.printHeader(self)
	path = os.path.join(os.path.dirname(__file__), 'myStories.html')
	self.response.out.write(template.render(path, template_values))
	main.printFooter(self, footer_template_values)
