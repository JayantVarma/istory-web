import os
from google.appengine.ext.webapp import template
import cgi
import re
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.api import memcache
import adventureModel
import addAdventure
import main

class Index(webapp.RequestHandler):

  def getAdventures(self):
	adventures = memcache.get("adventures")
	if adventures is not None:
		return adventures
	else:
		adventures_query = adventureModel.Adventure.all().order('-date')
		adventures = adventures_query.fetch(10)
		if not memcache.add("adventures", adventures, 300):
			logging.error("memcache set failed.")
		return adventures

  def get(self):
	adventures = self.getAdventures()
	stats = memcache.get_stats()

	if users.get_current_user():
		url = users.create_logout_url(self.request.uri)
		url_linktext = 'Logout'
	else:
		url = users.create_login_url(self.request.uri)
		url_linktext = 'Login'

	#newlineRE = re.compile('\n')
	#for adventure in adventures:
	#	adventure.desc = newlineRE.sub('<br>\n', adventure.desc)
	template_values = {
		'adventures': adventures,
		'url': url,
		'url_linktext': url_linktext,
	}

	footer_template_values = {
		'cacheHits': stats['hits'],
		'cacheMisses': stats['misses'],
	}

	main.printHeader(self)
	path = os.path.join(os.path.dirname(__file__), 'index.html')
	self.response.out.write(template.render(path, template_values))
	main.printFooter(self, footer_template_values)
