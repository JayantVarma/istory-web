import os
from google.appengine.ext.webapp import template
import cgi
import logging
import time
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.api import memcache
import adventureModel
import main
import admin
import signup

def getUserVote(adventureStatus, user, iphone):
	if not (adventureStatus and (user or iphone)):
		logging.warn("getUserVote requires adventureStatus and either user or iphone")
	userVote = None
	q = None
	q2 = None
	if user:
		q = adventureModel.UserVotes.all().filter('adventureStatus =', adventureStatus).filter('voter =', user)
		voter = user.email()
	elif iphone:
		q = adventureModel.UserVotes.all().filter('adventureStatus =', adventureStatus).filter('iphoneId =', iphone)
		voter = iphone
	else:
		logging.warn("stats: tried to vote but missing user or iphone")
		return("You must be logged in to vote.")
	memStr = "vote" + str(adventureStatus.key()) + str(voter)
	userVote = memcache.get(memStr)
	if userVote:
		logging.info("getUserVote: got from cache: " + memStr)
	else:
		votes = q.fetch(1)
		for myVote in votes:
			userVote = myVote
		if userVote:
			memcache.add(memStr, userVote, 3600)
			logging.info("getUserVote: got from db: " + memStr)
		else:
			logging.warn("getUserVote: could not find userVote with adventureStatus(%s) user(%s)" % (str(adventureStatus.key()), str(voter)))
	return userVote

def addAdventureStat(adventureStatus, plays, vote, user, iphone, comment):
	#try to fetch the adventureRating, then increment the stats
	rating = None
	changed = False
	userVote = None
	output = "Nothing Recorded"
	voteCount = 0
	if not adventureStatus:
		logging.warn("stats: adventureStatus is required")
		return("adventureStatus is required")
	q = adventureModel.AdventureRating.all().filter('adventureStatus =', adventureStatus)
	ratings = q.fetch(1)
	for myRating in ratings:
		rating = myRating
	if rating:
		logging.info("stats: found rating key in the db: " + str(adventureStatus.key()))
	else:
		logging.info("stats: rating key was not found in the db: " + str(adventureStatus.key()))
		return("Rating Key not found in DB")
	if plays and plays > 0:
		rating.plays = rating.plays + plays
		changed = True
	if vote and vote >= 0:
		#make sure this person hasn't already voted
		voter = None
		if user:
			voter = user.email()
		elif iphone:
			voter = iphone
		else:
			logging.warn("stats: tried to vote but missing user or iphone")
			return("You must be logged in to vote.")
		#delete the memcache vote record
		memStr = "vote" + str(adventureStatus.key()) + str(voter)
		memcache.delete(memStr)
		if user:
			userVote = getUserVote(adventureStatus, user, None)
			if not userVote:
				#see if this user has voted before as an iphone
				iphoneUser = signup.getDeviceFromUser(user)
				if iphoneUser:
					logging.info("stats: checking for vote with: " + iphoneUser)
					userVote = getUserVote(adventureStatus, None, iphoneUser)
					if userVote:
						logging.info("stats: got vote from user -> iphone")
						voter = iphoneUser;
		if iphone:
			userVote = getUserVote(adventureStatus, None, iphone)
			if not userVote:
				#see if this iphone has voted before as a user
				iphoneUser = signup.getUserFromDeviceID(iphone)
				if iphoneUser:
					userVote = getUserVote(adventureStatus, iphoneUser, None)
					if userVote:
						logging.info("stats: got vote from iphone -> user")
						voter = iphoneUser.email()
		#fetch the vote
		if userVote:
			logging.warn("stats: tried to vote but this user has already voted: " + voter)
			output = "Vote Updated. Thank You!"
			if userVote.vote != vote:
				#if they changed their vote
				voteDifference = vote - userVote.vote
				logging.info("stats: user is changing their vote. oldVote(%d) newVote(%d) diff(%d)" % (userVote.vote, vote, voteDifference))
				userVote.vote = vote
				vote = voteDifference
				userVote.comment = comment
				userVote.put()
				changed = True
		else:
			#now lets create the vote record
			output = "Vote Recorded. Thank You!"
			voteCount = 1
			userVote = adventureModel.UserVotes()
			userVote.adventureStatus = rating.adventureStatus
			userVote.voter = user
			userVote.iphoneId = iphone
			userVote.comment = comment
			userVote.vote = vote
			userVote.put()
			changed = True
		#now increment the rating
		rating.voteCount = rating.voteCount + voteCount
		rating.voteSum = rating.voteSum + vote
	if changed:
		if rating.voteCount > 0:
			rating.rating = float(rating.voteSum) / float(rating.voteCount)
		rating.put()
		logging.info("stats: adventure(%s): plays(%d) votes(%d) voteSum(%d) rating(%f)" % (rating.adventureStatus.editableAdventure.title, rating.plays, rating.voteCount, rating.voteSum, rating.rating))
	else:
		logging.info("stats: nothing changed")
	return(output)

def addAdventurePlay(adventureStatus):
	addAdventureStat(adventureStatus, 1, 0, 0, None, None)
	
def addAdventureVote(adventureStatus, vote, user, comment):
	output = addAdventureStat(adventureStatus, 0, vote, user, None, comment)
	return output

def addAdventureVoteIphone(adventureStatus, vote, iphone, comment):
	output = addAdventureStat(adventureStatus, 0, vote, None, iphone, comment)
	return output

class Vote(webapp.RequestHandler):
  def post(self):
	myAdventureKey = self.request.get('myAdventureKey')
	myVote = int(self.request.get('vote'))
	myiphone = self.request.get('iphone')
	myComment = self.request.get('comment')
	adventure = main.getAdventure(myAdventureKey)
	output = None
	adventureStatus = None
	if not adventure:
		logging.warn("Vote: adventure key did not exist in db: " + myAdventureKey)
		output = "Error: Adventure key did not exist in database."
		self.response.out.write(output)
		return
	#they either have to be logged in, or be on the iPhone
	if not users.get_current_user():
		error = 'Error: You must be logged in to vote.'
		output = "You must be logged in to vote."
		if not myiphone:
			logging.warn("Vote: trying to vote but user is not a reader and no iphone was passed in")
			self.response.out.write(output)
			return
	#we should be good, lets get the adventureStatus object now
	adventureStatus = admin.getAdventureStatus(adventure.adventureStatus)
	if not adventureStatus:
		logging.warn("Vote: could not get the adventureStatus record: " + myAdventureKey)
		return
	
	if myiphone:
		output = addAdventureVoteIphone(adventureStatus, myVote, myiphone, myComment)
	else:
		output = addAdventureVote(adventureStatus, myVote, users.get_current_user(), myComment)
	self.response.out.write(output)
	return

  def get(self):
	self.response.out.write("get vote")
	return



