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
from django.utils import simplejson
import adventureModel
import main

class Submit(webapp.RequestHandler):
  def get(self):
	defaultTemplateValues = main.getDefaultTemplateValues(self)
	templateValues = {
		'title': 'Submit Your Story For Approval',
	}
	templateValues = dict(defaultTemplateValues, **templateValues)

	path = os.path.join(os.path.dirname(__file__), 'submit.html')
	self.response.out.write(template.render(path, templateValues))

class Admin(webapp.RequestHandler):
  def get(self):
	if not users.is_current_user_admin():
		return
	myAdventureKey = self.request.get('myAdventureKey')
	command = self.request.get('command')
	var = self.request.get('var')
	logging.info("Admin get: myAdventureKey(%s)" % (myAdventureKey))
	output = "Admin get: myAdventureKey(%s) command(%s) var(%s)<br>" % (myAdventureKey, command, var)

	if command == 'delete story' and var:
		#this will delete all story data for a given adventure
		adventure = None
		logging.info("Admin get: delete story: " + var)
		output += "Admin get: delete story: " + var + "<br>"
		try:
			adventure = db.Model.get(var)
		except Exception, e:
			output += "Admin get: delete story: exception: " + str(e) + "<br>"
		if not adventure:
			logging.info("Admin get: delete story: adventure key not found in DB")
			output += "Admin get: delete story: adventure key not found in DB<br>"
		else:
			#share
			q = adventureModel.Share.all().filter('adventure =', adventure)
			a = q.fetch(9999)
			output += "Admin get: delete story: deleted %d records from Share<br>" % len(a)
			db.delete(a)
			#page element
			q = adventureModel.PageElement.all().filter('adventure =', adventure)
			a = q.fetch(9999)
			output += "Admin get: delete story: deleted %d records from PageElement<br>" % len(a)
			db.delete(a)
			#image
			q = adventureModel.Image.all().filter('adventure =', adventure)
			a = q.fetch(9999)
			output += "Admin get: delete story: deleted %d records from Image<br>" % len(a)
			db.delete(a)
			#page
			q = adventureModel.Page.all().filter('adventure =', adventure)
			a = q.fetch(9999)
			output += "Admin get: delete story: deleted %d records from Page<br>" % len(a)
			db.delete(a)
			#adventure
			adventure.delete()
			output += "Admin get: delete story: deleted %d records from Adventure<br>" % 1
			db.delete(a)
			memcache.delete("adventures")
			memcache.delete(var)

	defaultTemplateValues = main.getDefaultTemplateValues(self)
	templateValues = {
		'title': 'Admin',
		'output': output,
	}
	templateValues = dict(defaultTemplateValues, **templateValues)

	path = os.path.join(os.path.dirname(__file__), 'admin.html')
	self.response.out.write(template.render(path, templateValues))
