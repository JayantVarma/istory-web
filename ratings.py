import os
from google.appengine.ext.webapp import template
import cgi
import logging
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.api import memcache
import adventureModel
import main

def getRating(adventure):
	if not adventure:
		logging.warn("getRating requires adventure")
	q = None
	memStr = None
	rating = None
	q = adventureModel.AdventureRating.all().filter('adventure =', adventure)
	memStr = "rating" + str(adventure.key())
	rating = memcache.get(memStr)
	if rating:
		logging.info("getRating: got from cache: " + memStr)
	else:
		ratings = q.fetch(1)
		for myRating in ratings:
			rating = myRating
			memcache.add(memStr, rating, 3600)
			logging.info("getRating: got from db: " + memStr)
	return rating

def getUserVote(adventure, user, iphone):
	if not (adventure and (user or iphone)):
		logging.warn("getUserVote requires adventure and either user or iphone")
	userVote = None
	q = None
	if user:
		q = adventureModel.UserVotes.all().filter('adventure =', adventure).filter('voter =', user)
		voter = user.email()
	elif iphone:
		q = adventureModel.UserVotes.all().filter('adventure =', adventure).filter('iphone =', iphone)
		voter = iphone
	else:
		logging.warn("stats: tried to vote but missing user or iphone")
		return("You must be logged in to vote.")
	memStr = "vote" + str(adventure.key()) + str(voter)
	userVote = memcache.get(memStr)
	if userVote:
		logging.info("getUserVote: got from cache: " + memStr)
	else:
		votes = q.fetch(1)
		for myVote in votes:
			userVote = myVote
			memcache.add(memStr, userVote, 3600)
			logging.info("getUserVote: got from db: " + memStr)
	return userVote

def addAdventureStat(adventureKey, plays, vote, user, iphone, comment):
	#try to fetch the adventureRating, then increment the stats
	#if it doesnt exist, create the record
	rating = None
	changed = False
	adventure = None
	output = "Nothing Recorded"
	voteCount = 0
	if not adventureKey:
		logging.warn("stats: adventureKey is required")
		return("Adventure Key not found in DB")
	adventure = main.getAdventure(adventureKey)
	if not adventure:
		logging.warn("stats: adventure key was not found in the DB " + adventureKey)
		return("Adventure Key not found in DB")
	q = adventureModel.AdventureRating.all().filter('adventure =', adventure)
	ratings = q.fetch(1)
	for myRating in ratings:
		rating = myRating
	if rating:
		logging.info("addAdventurePlay: found rating key in the db: " + adventureKey)
	else:
		logging.info("addAdventurePlay: rating key was not found in the db: " + adventureKey)
		rating = adventureModel.AdventureRating()
		rating.adventure = adventure
		rating.voteCount = 0
		rating.voteSum = 0
		rating.plays = 0
		rating.approved = 0
		rating.rating = 0.0
		rating.put()
		return("Rating Key not found in DB")
	if plays and plays > 0:
		rating.plays = rating.plays + plays
		changed = True
	if vote and vote >= 0:
		#make sure this person hasn't already voted
		userVote = None
		q = None
		voter = None
		if user:
			q = adventureModel.UserVotes.all().filter('adventure =', adventure).filter('voter =', user)
			voter = user.email()
		elif iphone:
			q = adventureModel.UserVotes.all().filter('adventure =', adventure).filter('iphone =', iphone)
			voter = iphone
		else:
			logging.warn("stats: tried to vote but missing user or iphone")
			return("You must be logged in to vote.")
		#delete the memcache vote record
		memStr = "vote" + str(adventure.key()) + str(voter)
		memcache.delete(memStr)
		#fetch the vote
		votes = q.fetch(1)
		for myVote in votes:
			userVote = myVote
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
			userVote.adventure = adventure
			userVote.voter = user
			userVote.iphone = iphone
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
		logging.info("addAdventurePlays: adventure(%s): plays(%d) votes(%d) voteSum(%d) rating(%f)" % (rating.adventure.title, rating.plays, rating.voteCount, rating.voteSum, rating.rating))
	else:
		logging.info("addAdventurePlays: nothing changed")
	return(output)

def addAdventurePlay(adventureKey):
	addAdventureStat(adventureKey, 1, 0, 0, None, None)
	
def addAdventureVote(adventureKey, vote, user, comment):
	output = addAdventureStat(adventureKey, 0, vote, user, None, comment)
	return output

def addAdventureVoteIphone(adventureKey, vote, iphone, comment):
	output = addAdventureStat(adventureKey, 0, vote, None, iphone, comment)
	return output

class Vote(webapp.RequestHandler):
  def post(self):
	myAdventureKey = self.request.get('myAdventureKey')
	myVote = int(self.request.get('vote'))
	myiphone = self.request.get('iphone')
	myComment = self.request.get('comment')
	adventure = main.getAdventure(myAdventureKey)
	output = None
	if not adventure:
		logging.warn("Vote: adventure key did not exist in db: " + myAdventureKey)
	#they either have to be a reader of this adventure, or be on the iPhone
	if not main.isUserReader(users.get_current_user(), adventure):
		error = 'Error: You are not a reader of this adventure'
		output = "You do not have permission to vote on this adventure."
		if not myiphone:
			logging.warn("Vote: trying to vote but user is not a reader and no iphone was passed in")
			self.response.out.write(output)
			return
	#we should be good, lets send the vote
	if myiphone:
		output = addAdventureVoteIphone(myAdventureKey, myVote, myiphone, myComment)
	else:
		output = addAdventureVote(myAdventureKey, myVote, users.get_current_user(), myComment)
	self.response.out.write(output)
	return




