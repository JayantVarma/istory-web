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

  #this actually gives you the 20 highest ratings, each one links to an adventure
  def getRatings(self):
	ratings = memcache.get("adventures")
	if ratings is not None:
		return ratings
	else:
		q = adventureModel.AdventureRating.all().filter('approved =', 1).order('-rating').order('created')
		ratings = q.fetch(20)
		if not memcache.add("adventures", ratings, 300):
			logging.info("memcache set failed.")
		return ratings

  def get(self):
	ratings = self.getRatings()

	defaultTemplateValues = main.getDefaultTemplateValues(self)
	templateValues = {
		'title': 'Home',
		'ratings': ratings,
	}
	templateValues = dict(defaultTemplateValues, **templateValues)

	path = os.path.join(os.path.dirname(__file__), 'index.html')
	self.response.out.write(template.render(path, templateValues))
