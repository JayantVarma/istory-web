from google.appengine.ext import db
import logging
import cgi

class Adventure(db.Model):
	title = db.StringProperty(multiline=False)
	realAuthor = db.UserProperty()
	author = db.StringProperty(multiline=False)
	version = db.StringProperty(multiline=False)
	desc = db.TextProperty()
	approved = db.IntegerProperty()
	created = db.DateTimeProperty(auto_now_add=True)
	modified = db.DateTimeProperty(auto_now=True)
	def toDict(self):
		return {
			'title': cgi.escape(self.title),
			'author': cgi.escape(self.author),
			'desc': cgi.escape(self.desc),
		}

class Page(db.Model):
	adventure = db.ReferenceProperty(Adventure)
	name = db.StringProperty(multiline=False)
	created = db.DateTimeProperty(auto_now_add=True)
	modified = db.DateTimeProperty(auto_now=True)
	def toDict(self):
		return {
			#'adventure': str(self.adventure.key()),
			'key': str(self.key()),
			'name': cgi.escape(self.name),
		}

class Image(db.Model):
	adventure = db.ReferenceProperty(Adventure)
	pageElement = db.StringProperty(multiline=False)
	imageName = db.StringProperty(multiline=False)
	imageData = db.BlobProperty()
	realAuthor = db.UserProperty()
	created = db.DateTimeProperty(auto_now_add=True)
	modified = db.DateTimeProperty(auto_now=True)
	def toDict(self):
		return {
			'adventure': str(self.adventure.key()),
			'imageName': cgi.escape(self.imageName),
			'realAuthor': cgi.escape(str(self.realAuthor.nickname())),
			'key': str(self.key()),
			'pageElement': self.pageElement,
		}

class PageElement(db.Model):
	page = db.ReferenceProperty(Page)
	adventure = db.ReferenceProperty(Adventure)
	dataType = db.IntegerProperty()
	pageOrder = db.IntegerProperty()
	dataA = db.TextProperty()
	dataB = db.TextProperty()
	imageRef = db.ReferenceProperty(Image)
	enabled = db.IntegerProperty()
	created = db.DateTimeProperty(auto_now_add=True)
	modified = db.DateTimeProperty(auto_now=True)
	def toDict(self):
		imageRef = None
		try:
			if self.imageRef:
				imageRef = str(self.imageRef.key())
		except Exception, e:
			logging.info('%s: %s' % (e.__class__.__name__, e))
			self.imageRef = None
			self.put()
		myDataB = None
		if self.dataB:
			myDataB = cgi.escape(self.dataB)
		return {
			'page':      str(self.page.key()),
			'adventure': str(self.adventure.key()),
			'key':       str(self.key()),
			'dataType':  self.dataType,
			'pageOrder': self.pageOrder,
			'dataA':     cgi.escape(self.dataA),
			'dataB':     myDataB,
			'enabled':   self.enabled,
			'imageRef':  imageRef,
		}

class Share(db.Model):
	adventure = db.ReferenceProperty(Adventure)
	owner = db.UserProperty()
	child = db.UserProperty()
	childEmail = db.StringProperty(multiline=False)
	childName = db.StringProperty(multiline=False)
	role = db.IntegerProperty()
	inviteKey = db.StringProperty(multiline=False)
	status = db.IntegerProperty()
	created = db.DateTimeProperty(auto_now_add=True)
	modified = db.DateTimeProperty(auto_now=True)
	def isAdmin(self):
		if self.role >= 3:
			return True
		return False
	def isAuthor(self):
		if self.role >= 2:
			return True
		return False
	def isReader(self):
		if self.role >= 1:
			return True
		return False
	def statusName(self):
		statusName = 'None'
		if self.status == 1:
			statusName = 'Pending'
		if self.status == 2:
			statusName = 'Accepted'
		if self.status == -1:
			statusName = 'Denied'
		return statusName
	def roleName(self):
		roleName = 'None'
		if self.role == 1:
			roleName = 'Reader'
		elif self.role == 2:
			roleName = 'Author'
		elif self.role == 3:
			roleName = 'Admin'
		return roleName
	def roleNamePhrase(self):
		roleName = 'None'
		if self.role == 1:
			roleName = 'a Reader'
		elif self.role == 2:
			roleName = 'an Author'
		elif self.role == 3:
			roleName = 'an Admin'
		return roleName
	#def toDict(self):
	#	myChild = None
	#	myChildNick = None
	#	if self.child:
	#		myChild = cgi.escape(str(self.child.email()))
	#		myChildNick = cgi.escape(str(self.child.nickname()))
	#	return {
	#		'adventure':      str(self.adventure.key()),
	#		'owner':          cgi.escape(str(self.owner.email())),
	#		'child':          myChild,
	#		'ownerNick':      cgi.escape(str(self.owner.nickname())),
	#		'childNick':      myChildNick,
	#		'childEmail':     cgi.escape(self.childEmail),
	#		'childName':      cgi.escape(self.childName),
	#		'role':           cgi.escape(str(self.role)),
	#		'roleName':       cgi.escape(self.roleName()),
	#		'roleNamePhrase': cgi.escape(self.roleNamePhrase()),
	#		'inviteKey':      cgi.escape(self.inviteKey),
	#		'status':         cgi.escape(str(self.status)),
	#		'statusName':     cgi.escape(self.statusName()),
	#	}

class AdventureStatus(db.Model):
	editableAdventure = db.ReferenceProperty(Adventure, collection_name="AS_editableAdventure_set")
	publishedAdventure = db.ReferenceProperty(Adventure, collection_name="AS_publishedAdventure_set")
	status = db.IntegerProperty()
	comment = db.TextProperty()
	editorComment = db.TextProperty()
	created = db.DateTimeProperty(auto_now_add=True)
	modified = db.DateTimeProperty(auto_now=True)
	def statusName(self):
		statusName = 'None'
		if self.status == 1:
			statusName = 'Not Submitted'
		elif self.status == 2:
			statusName = 'Submitted'
		elif self.status == 2:
			statusName = 'Approved'
		elif self.status == -1:
			statusName = 'Not Approved'
		return statusName
	def statusDesc(self):
		statusName = 'None'
		if self.status == 1:
			statusName = 'This story has not been submitted yet.'
		elif self.status == 2:
			statusName = 'This story has been submitted and is currently under review by our editors.'
		elif self.status == 3 and publishedAdventure:
			statusName = 'This story is approved. It should be readable by the general public and may be on the front page of the site. Read your published story <a href="/playStory?myAdventureKey=%s">here</a>.' % str(publishedAdventure.key())
		elif self.status == -1:
			statusName = 'This story was not approved. Please read the editor comments and submit again.'
		return statusName


class UserVotes(db.Model):
	adventureStatus = db.ReferenceProperty(AdventureStatus)
	voter = db.UserProperty()
	voterIphone = db.StringProperty(multiline=False)
	comment = db.TextProperty()
	vote = db.IntegerProperty()
	created = db.DateTimeProperty(auto_now_add=True)
	modified = db.DateTimeProperty(auto_now=True)
	#def toDict(self):
	#	return {
	#		'adventure':   str(self.adventure.key()),
	#		'voter':       cgi.escape(str(self.voter.email())),
	#		'voterIphone': cgi.escape(str(self.voterIphone)),
	#		'comment':     cgi.escape(self.comment),
	#		'vote':        cgi.escape(str(self.vote))
	#	}

class AdventureRating(db.Model):
	adventureStatus = db.ReferenceProperty(AdventureStatus)
	voteCount = db.IntegerProperty()
	voteSum = db.IntegerProperty()
	rating = db.FloatProperty()
	plays = db.IntegerProperty()
	approved = db.IntegerProperty()
	created = db.DateTimeProperty(auto_now_add=True)
	modified = db.DateTimeProperty(auto_now=True)
	#def toDict(self):
	#	return {
	#		'adventure': str(self.adventureStatus.editableAdventure.key()),
	#		'approved': cgi.escape(str(self.approved)),
	#		'voteCount': cgi.escape(str(self.voteCount)),
	#		'voteSum':   cgi.escape(str(self.voteSum)),
	#		'rating':    cgi.escape(str(self.rating)),
	#		'plays':     cgi.escape(str(self.plays))
	#	}





