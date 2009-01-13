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
from google.appengine.api import mail
from django.utils import simplejson
import random
import adventureModel
import main

def getUserFromDeviceID(deviceID):
	if not deviceID:
		logging.warn("getUserFromDeviceID requires deviceID")
		return
	memcacheStr = "link" + deviceID
	user = memcache.get(memcacheStr)
	if user:
		logging.info("getUserFromDeviceID: got user from memcache: %s, %s" % (deviceID, user))
		return user
	#lookup deviceID in database
	iphoneLink = None
	q = adventureModel.iphoneLink.all().filter('iphoneId =', deviceID)
	iphoneLinks = q.fetch(1)
	for myIphoneLink in iphoneLinks:
		iphoneLink = myIphoneLink
	if not iphoneLink:
		logging.info("getUserFromDeviceID: could not find iphone in db: %s" % deviceID)
		memcache.add(memcacheStr, None, 300)
		return
	logging.info("getUserFromDeviceID: got user from memcache: %s, %s" % (deviceID, user))
	memcache.add(memcacheStr, iphoneLink.user, 300)
	return iphoneLink.user

def getDeviceFromUser(user):
	if not user:
		logging.warn("getDeviceFromUser requires user")
		return
	memcacheStr = "link" + str(user.email())
	deviceID = memcache.get(memcacheStr)
	if deviceID:
		logging.info("getDeviceFromUser: got user from memcache: %s, %s" % (deviceID, user))
		return deviceID
	#lookup deviceID in database
	iphoneLink = None
	q = adventureModel.iphoneLink.all().filter('user =', user)
	iphoneLinks = q.fetch(1)
	for myIphoneLink in iphoneLinks:
		iphoneLink = myIphoneLink
	if not iphoneLink:
		logging.info("getDeviceFromUser: could not find user in db: %s" % user)
		memcache.add(memcacheStr, None, 300)
		return
	logging.info("getDeviceFromUser: got user from memcache: %s, %s" % (deviceID, user))
	memcache.add(memcacheStr, iphoneLink.iphoneId, 300)
	return iphoneLink.iphoneId

class Signup(webapp.RequestHandler):
  def get(self):
	myEmail = self.request.get('email')
	myDeviceID = self.request.get('deviceID')
	logging.info("Signup: email(%s) deviceID(%s)" % (myEmail, myDeviceID))
	if not myEmail or not myDeviceID:
		self.response.out.write("Error: Email and/or Device ID not found")
		return
	#create the iphoneLink record
	iphoneLink = adventureModel.iphoneLink()
	iphoneLink.regEmail = myEmail
	iphoneLink.iphoneId = myDeviceID
	iphoneLink.verified = 0
	iphoneLink.regKey = ''
	#generate the signup key
	for i in random.sample('ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890', 6):
		iphoneLink.regKey += i
	iphoneLink.put()
	#send the email
	body = '''Greetings from the iStory team,

Thanks for signing up! We're looking forward to seeing what kind of great stories you and the rest of the iStory community can make.

Your registration link is: http://istoryweb.appspot.com/signup?key=%s

Thanks,
Taylor Steil and the iStory Team
''' % iphoneLink.regKey
	mail.send_mail(sender="istoryadmin@gmail.com", to=iphoneLink.regEmail, subject='Your iStory registration request', body=body)
	self.response.out.write("%s has been sent an invitation." % myEmail)

class SignupDone(webapp.RequestHandler):
  def get(self):
	iphoneLink = None
	error = None
	myKey = self.request.get('key')
	if not myKey:
		logging.warn("SignupDone: ERROR: requires myKey")
		error = "Error: missing signup key"
	else:
		q = adventureModel.iphoneLink.all().filter('regKey =', myKey).filter('verified =', 0)
		iphoneLinks = q.fetch(1)
		for myIphoneLink in iphoneLinks:
			iphoneLink = myIphoneLink
		if not iphoneLink:
			logging.warn("SignupDone: ERROR: iphoneLink was not found with regKey: " + myKey)
			error = "Error: unused signup key was not found in the database. Maybe you already signed up with this key?"
		else:
			logging.info("SignupDone: iphoneLink was found with regkey: " + myKey)
	
	#if they are signed in, consume the iphoneLink record
	if iphoneLink and users.get_current_user():
		iphoneLink.verified = 1
		iphoneLink.user = users.get_current_user()
		iphoneLink.put()
		#remove the cache record
		memcache.delete('iphoneLinks' + users.get_current_user().email())
		memcache.delete('myStoriesXML' + users.get_current_user().email())
	
	defaultTemplateValues = main.getDefaultTemplateValues(self)
	templateValues = {
		'error': error,
		'iphoneLink': iphoneLink,
		'title': 'Thanks For Signing Up!'
	}
	templateValues = dict(defaultTemplateValues, **templateValues)

	path = os.path.join(os.path.dirname(__file__), 'signup.html')
	self.response.out.write(template.render(path, templateValues))






