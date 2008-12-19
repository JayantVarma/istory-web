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
		adventures_query = adventureModel.Adventure.all().order('-created')
		adventures = adventures_query.fetch(10)
		if not memcache.add("adventures", adventures, 300):
			logging.error("memcache set failed.")
		return adventures

  def get(self):
	adventures = self.getAdventures()

	defaultTemplateValues = main.getDefaultTemplateValues(self)
	templateValues = {
		'title': 'Home',
		'adventures': adventures,
	}
	templateValues = dict(defaultTemplateValues, **templateValues)

	path = os.path.join(os.path.dirname(__file__), 'index.html')
	self.response.out.write(template.render(path, templateValues))
