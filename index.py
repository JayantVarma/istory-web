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

#this actually gives you the 20 highest ratings, each one links to an adventure
def getRatings():
	ratings = memcache.get("adventures")
	if ratings is not None:
		return ratings
	else:
		q = adventureModel.AdventureRating.all().filter('approved =', 1).order('-rating').order('created')
		ratings = q.fetch(20)
		if not memcache.add("adventures", ratings, 300):
			logging.info("memcache set failed.")
		return ratings

class Index(webapp.RequestHandler):
  def get(self):
	ratings = getRatings()

	defaultTemplateValues = main.getDefaultTemplateValues(self)
	templateValues = {
		'title': 'Home',
		'ratings': ratings,
	}
	templateValues = dict(defaultTemplateValues, **templateValues)

	path = os.path.join(os.path.dirname(__file__), 'index.html')
	self.response.out.write(template.render(path, templateValues))

class Help(webapp.RequestHandler):
  def get(self):
	defaultTemplateValues = main.getDefaultTemplateValues(self)
	templateValues = {
		'title': 'Home'
	}
	templateValues = dict(defaultTemplateValues, **templateValues)

	path = os.path.join(os.path.dirname(__file__), 'help.html')
	self.response.out.write(template.render(path, templateValues))

class Hello(webapp.RequestHandler):
  def get(self):
	self.response.out.write("hello")
