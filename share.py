import os
from google.appengine.ext.webapp import template
import cgi
import re
import logging
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.api import datastore
from google.appengine.api import memcache
from google.appengine.api import mail
from django.utils import simplejson
import adventureModel
import main
import random

class ShareInvite(webapp.RequestHandler):
  def post(self):
	self.get()

  def get(self):
	#this method takes an existing share invite record and accepts it
	#get the invite from the db
	error = None
	state = None
	share = None
	myInviteKey = self.request.get('key')
	myShareKey = self.request.get('shareInviteKey')
	myResponse = self.request.get('response')
	logging.info("ShareInvite: key(%s) shareInviteKey(%s) response(%s)" % (myInviteKey, myShareKey, myResponse))
	
	#if we have an invite key, this must be the first click of the invite link
	if myInviteKey:
		logging.info("ShareInvite: someone clicked the invite link with key %s" % myInviteKey )
		q = adventureModel.Share.all().filter('status =', 1).filter('inviteKey =', myInviteKey)
		myShares = q.fetch(1)
		for myShare in myShares:
			share = myShare
		if not share:
			error = 'Error: that invite key (%s) was not found. Please check the link from the email carefully.'
		else:
			state = "1"
	elif myShareKey and myResponse:
		if myResponse == "1":
			#now we need to make sure they're logged in
			if not users.get_current_user():
				logging.info("ShareInvite: invite tried to be accepted but the user needs to login")
				error = 'To continue, you need to <a href="%s">login with your Google account</a>.' % users.create_login_url(self.request.uri)
			else:
				share = db.Model.get(myShareKey)
				if not share:
					logging.info("ShareInvite: invite accepted and the user is logged in, but the invite key did not exist " + myShareKey)
					error = 'Error: this share key was not found.'
				else:
					logging.info("ShareInvite: invite accepted and the user is logged in")
					state = "2"
					share.status = 2
					share.child = users.get_current_user()
					share.put()
					#delete the current adventure cache object
					memcache.delete("adventures_" + share.child.email())
					memcache.delete('myStoriesXML' + share.child.email())
					#remove the share invite cache object
					memcache.delete("invites_" + share.childEmail)
					memcache.delete("invites_" + users.get_current_user().email())
					#remove the user share object from cache
					removeUserShareCache(share.child, str(share.adventure.key()))
					removeUserShareCache(share.child, str(share.adventure.key()))
		else:
			logging.info("ShareInvite: invite ignored")
			error = "Invite ignored."

	defaultTemplateValues = main.getDefaultTemplateValues(self)
	templateValues = {
		'error': error,
		'share': share,
		'response': myResponse,
		'state': state,
	}
	templateValues = dict(defaultTemplateValues, **templateValues)

	path = os.path.join(os.path.dirname(__file__), 'shareInvite.html')
	self.response.out.write(template.render(path, templateValues))


class ViewSharing(webapp.RequestHandler):
  def post(self):
	error = None
	adventure = None
	myAdventureKey = self.request.get('myAdventureKey')
	myName = self.request.get('name')
	myEmail = self.request.get('email')
	myRole = int(self.request.get('role'))
	logging.info("ViewSharing: post adventureKey(%s) name(%s) email(%s) role(%d)" % (myAdventureKey, myName, myEmail, myRole))

	#make sure we're logged in
	if not users.get_current_user():
		logging.warning('ViewSharing post: you are not logged in')
		error = 'Error: You are not logged in'
		self.response.out.write(error)
		return

	#make sure the email address is valid
	if not mail.is_email_valid(myEmail):
		logging.warning('ViewSharing post: invalid email address')
		error = 'Error: Invalid email address'
		self.response.out.write(error)
		return

	#get the adventure
	adventure = main.getAdventure(myAdventureKey)
	if not adventure:
		logging.warning('ViewSharing post: adventure key %s does not exist' % (myAdventureKey))
		error = 'Error: adventure key %s does not exist' % (myAdventureKey)
		self.response.out.write(error)
		return

	#make sure we're the owner
	#if not(users.is_current_user_admin()) and adventure.realAuthor and adventure.realAuthor != users.get_current_user():
	if not main.isUserAdmin(users.get_current_user(), adventure):
		logging.warning('ViewSharing post: you are not an admin of this adventure')
		error = 'Error: You are not an admin of this adventure'
		self.response.out.write(error)
		return

	#see if this person has already been invited
	q = adventureModel.Share.all().filter('status >=', 1).filter('adventure =', adventure).filter('childEmail =', myEmail).filter('role =', myRole)
	myShares = q.fetch(1)
	for myShare in myShares:
		logging.info('ViewSharing post: this email address has already been invited to this adventure for this role.')
		error = 'Error: This email address has already been invited to this adventure for this role.'
		self.response.out.write(error)
		return

	#create the invite and store it in the DB
	logging.info("ViewSharing post: creating new invite")
	share = adventureModel.Share()
	share.adventure = adventure
	share.owner = users.get_current_user()
	share.childEmail = myEmail
	share.childName = myName
	share.status = 1
	share.inviteKey = ''
	for i in random.sample('ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890', 6):
		share.inviteKey += i
	share.role = myRole
	share.put()

	#remove the share invite cache object
	memcache.delete("invites_" + myEmail)
	
	#send the invite email
	subject = 'You have an iStory invite from %s' % (users.get_current_user().nickname())
	body = """
Hello %s,

You have been invited to collaborate with %s (%s) on the story, '%s'. Just click the link below and you'll be taken to the iStory website, where you can participate in this next generation story telling experience.

http://istoryweb.appspot.com/shareInvite?key=%s

We hope you enjoy iStory!
Thanks,
The iStory team
""" % (myName, users.get_current_user().nickname(), users.get_current_user().email(), adventure.title, share.inviteKey)
	mail.send_mail('istoryadmin@gmail.com', myEmail, subject, body)
	
	#send the json response back to the web
	logging.info('ViewSharing post: here is the invite: ' + simplejson.dumps(share.toDict()) )
	self.response.out.write(simplejson.dumps(share.toDict()))


  def get(self):
	adventure = None
	shares = None
	shareInvites = None
	yourRole = None
	page = None
	error = None
	title = 'Share and Collaborate'
	myAdventureKey = self.request.get('myAdventureKey')

	if not users.get_current_user():
		logging.info("ViewSharing get: you are not logged in")
		error = 'Error: you are not logged in'
	else:
		if myAdventureKey:
			#get the adventure
			adventure = main.getAdventure(myAdventureKey)
		if not adventure:
			logging.info("ViewSharing get: adventure key was not found")
			error = 'Error: adventure was not found'
		elif not main.isUserAdmin(users.get_current_user(), adventure):
			logging.warning('ViewSharing get: you are not an admin of this adventure')
			error = 'Error: You are not an admin of this adventure'
		else:
			#get all the shares for this adventure
			q1 = adventureModel.Share.all().filter('adventure =', adventure).filter('status >=', 1).order('status').order('-role').order('created')
			shares = q1.fetch(9999)
			logging.info("got %d shares for adventure %s" % (len(shares), adventure.title))
			#find your role in this adventure
			for share in shares:
				if share.child == users.get_current_user():
					yourRole = share
					break
			if yourRole == None and users.is_current_user_admin():
				logging.info("Share get: used mega admin powers to grant admin to %s" % users.get_current_user().email())
				yourRole = adventureModel.Share()
				yourRole.role = 3

	defaultTemplateValues = main.getDefaultTemplateValues(self)
	templateValues = {
		'adventure': adventure,
		'adventureKey': myAdventureKey,
		'error': error,
		'title': title,
		'shares': shares,
		'yourRole': yourRole,
	}
	templateValues = dict(defaultTemplateValues, **templateValues)

	path = os.path.join(os.path.dirname(__file__), 'share.html')
	self.response.out.write(template.render(path, templateValues))


class RemoveShare(webapp.RequestHandler):
  def post(self):
	share = None
	myShareKey = self.request.get('myShareKey')
	#make sure share exists
	share = db.Model.get(myShareKey)
	if not share:
		logging.info("RemoveShare: share key did not exist: " + myShareKey)
		error = "Error: share did not exist"
		self.response.out.write(error)
		return
	elif not main.isUserAdmin(users.get_current_user(), share.adventure):
		logging.warning('RemoveShare post: you are not an admin of this adventure')
		error = 'Error: You are not an admin of this adventure'
		self.response.out.write(error)
		return
	elif share.adventure.realAuthor == share.child:
		logging.info("RemoveShare: you cannot remove the owner of the adventure")
		error = 'Error: you cannot remove the owner of the adventure'
		self.response.out.write(error)
		return
	else:
		jsonText = simplejson.dumps(share.toDict())
		if share.child:
			#remove the oadventure object from cache
			memcache.delete("adventures_" + share.child.email())
			memcache.delete('myStoriesXML' + share.child.email())
			#just for good measure, remove the share invite cache
			memcache.delete("invites_" + share.child.email())
		if share.adventure and share.child:
			#remove the user share object from cache
			removeUserShareCache(share.child, str(share.adventure.key()))
		#delete the db record
		share.delete()
		#done
		logging.info('RemoveShare: share deleted: ' + jsonText)
		self.response.out.write(jsonText)


def removeUserShareCache(user, adventureKey):
	if not user or not adventureKey:
		logging.warn("removeUserShareCache: requires user and adventureKey")
		return;
	q = adventureModel.Share.all().filter('status =', 2).filter('child =', user)
	counter = 0
	shares = q.fetch(9999)
	for share in shares:
		for n in range(0, share.role):
			cacheString = str(n+1) + ',' + user.email() + ',' + str(adventureKey)
			logging.info("RemoveShare: removing cache record: " + cacheString)
			counter += 1
			memcache.delete(cacheString)
	
	logging.info("RemoveShare: removed %d shares from cache for user %s" % (counter, user.email()))



