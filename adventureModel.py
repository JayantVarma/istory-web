from google.appengine.ext import db
import logging
import cgi
from xml.sax.saxutils import escape
from xml.sax.saxutils import quoteattr

class Adventure(db.Model):
	title = db.StringProperty(multiline=False)
	realAuthor = db.UserProperty()
	author = db.StringProperty(multiline=False)
	desc = db.TextProperty()
	coverImage = db.StringProperty(multiline=False)
	approved = db.IntegerProperty()
	version = db.FloatProperty()
	adventureStatus = db.StringProperty(multiline=False)
	created = db.DateTimeProperty(auto_now_add=True)
	modified = db.DateTimeProperty(auto_now=True)
	def toDict(self):
		return {
			'title': cgi.escape(self.title),
			'author': cgi.escape(self.author),
			'desc': cgi.escape(self.desc),
		}

class Page(db.Model):
	adventure = db.ReferenceProperty(Adventure, collection_name='pages')
	name = db.StringProperty(multiline=False)
	created = db.DateTimeProperty(auto_now_add=True)
	modified = db.DateTimeProperty(auto_now=True)
	def toDict(self):
		return {
			#'adventure': str(self.adventure.key()),
			'key': str(self.key()),
			'name': cgi.escape(self.name),
		}
	def pageHeaderToXML(self):
		myName = 'None'
		if self.name:
			myName = self.name
		return '''<file>
	<name>%s.xml</name>
	<page>%s</page>
</file>
''' % (escape(str(self.key())), escape(myName))

class iphoneLink(db.Model):
	regEmail = db.StringProperty(multiline=False)
	regKey = db.StringProperty(multiline=False)
	iphoneId = db.StringProperty(multiline=False)
	verified = db.IntegerProperty()
	user = db.UserProperty()
	created = db.DateTimeProperty(auto_now_add=True)
	modified = db.DateTimeProperty(auto_now=True)

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
	def toDict(self):
		myChild = None
		myChildNick = None
		if self.child:
			myChild = cgi.escape(str(self.child.email()))
			myChildNick = cgi.escape(str(self.child.nickname()))
		return {
			'adventure':      str(self.adventure.key()),
			'owner':          cgi.escape(str(self.owner.email())),
			'child':          myChild,
			'ownerNick':      cgi.escape(str(self.owner.nickname())),
			'childNick':      myChildNick,
			'childEmail':     cgi.escape(self.childEmail),
			'childName':      cgi.escape(self.childName),
			'role':           cgi.escape(str(self.role)),
			'roleName':       cgi.escape(self.roleName()),
			'roleNamePhrase': cgi.escape(self.roleNamePhrase()),
			'inviteKey':      cgi.escape(self.inviteKey),
			'status':         cgi.escape(str(self.status)),
			'statusName':     cgi.escape(self.statusName()),
		}

class AdventureStatus(db.Model):
	editableAdventure = db.ReferenceProperty(Adventure, collection_name="AS_editableAdventure_set")
	submittedAdventure = db.ReferenceProperty(Adventure, collection_name="AS_submittedAdventure_set")
	publishedAdventure = db.ReferenceProperty(Adventure, collection_name="AS_publishedAdventure_set")
	version = db.FloatProperty()
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
		elif self.status == 3:
			statusName = 'Approved'
		elif self.status == -1:
			statusName = 'Not Approved'
		return statusName
	def statusDesc(self):
		statusName = 'None'
		if self.status == 1:
			statusName = 'This story has not been submitted yet.'
		elif self.status == 2 and self.submittedAdventure:
			statusName = 'This story has been submitted and is currently under review by our editors.<br>Play your submitted story <a href="/playStory?myAdventureKey=%s">here</a>.' % str(self.submittedAdventure.key())
		elif self.status == 3 and self.publishedAdventure:
			statusName = 'This story is approved. It is readable by the general public and may be on the front page of the site.<br>Play your published story <a href="/playStory?myAdventureKey=%s">here</a>.' % str(self.publishedAdventure.key())
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
	adventureStatus = db.ReferenceProperty(AdventureStatus, collection_name='ratings')
	voteCount = db.IntegerProperty()
	voteSum = db.IntegerProperty()
	rating = db.FloatProperty()
	plays = db.IntegerProperty()
	approved = db.IntegerProperty()
	created = db.DateTimeProperty(auto_now_add=True)
	modified = db.DateTimeProperty(auto_now=True)
	def getPageCount(self):
		pageCount = 0
		adventure = None
		if self.adventureStatus.publishedAdventure:
			adventure = self.adventureStatus.publishedAdventure
		else:
			adventure = self.adventureStatus.editableAdventure
		for page in adventure.pages:
			pageCount = pageCount + 1
		return pageCount
	def toXML(self):
		adventure = None
		if self.adventureStatus.publishedAdventure:
			adventure = self.adventureStatus.publishedAdventure
		else:
			adventure = self.adventureStatus.editableAdventure
		myCoverImage = ''
		if adventure.coverImage:
			myCoverImage = escape(adventure.coverImage + '.png')
		return '''<adventure>
	<id>%s</id>
	<title>%s</title>
	<desc>%s</desc>
	<author>%s</author>
	<pages>%d</pages>
	<version>%f</version>
	<coverImage>%s</coverImage>
</adventure>
''' % (escape(str(adventure.key())), escape(adventure.title), escape(adventure.desc), escape(adventure.author), self.getPageCount(), self.adventureStatus.version, myCoverImage)

	#def toDict(self):
	#	return {
	#		'adventure': str(self.adventureStatus.editableAdventure.key()),
	#		'approved': cgi.escape(str(self.approved)),
	#		'voteCount': cgi.escape(str(self.voteCount)),
	#		'voteSum':   cgi.escape(str(self.voteSum)),
	#		'rating':    cgi.escape(str(self.rating)),
	#		'plays':     cgi.escape(str(self.plays))
	#	}

class Image(db.Model):
	adventure = db.ReferenceProperty(Adventure)
	adventureStatus = db.ReferenceProperty(AdventureStatus, collection_name='images')
	#we need pageElement for uploading new images. we have to store the page element here so we can send it back to the client via json
	pageElement = db.StringProperty(multiline=False)
	imageName = db.StringProperty(multiline=False)
	imageData = db.BlobProperty()
	realAuthor = db.UserProperty()
	created = db.DateTimeProperty(auto_now_add=True)
	modified = db.DateTimeProperty(auto_now=True)
	def toXML(self):
		myName = 'None'
		if self.imageName:
			myName = self.imageName
		return '''<file>
	<name>%s.png</name>
	<page>%s</page>
</file>
''' % (escape(str(self.key())), escape(myName))
	def toDict(self):
		myPageElement = None
		if self.pageElement:
			myPageElement = cgi.escape(self.pageElement)
		return {
			'adventure': str(self.adventure.key()),
			'pageElement': myPageElement,
			'imageName': cgi.escape(self.imageName),
			'realAuthor': cgi.escape(str(self.realAuthor.nickname())),
			'key': str(self.key()),
		}

class PageElement(db.Model):
	page = db.ReferenceProperty(Page, collection_name='pageElements')
	adventure = db.ReferenceProperty(Adventure, collection_name='adventurePageElements')
	dataType = db.IntegerProperty()
	pageOrder = db.IntegerProperty()
	dataA = db.TextProperty()
	dataB = db.TextProperty()
	imageRef = db.ReferenceProperty(Image, collection_name='pageElements')
	enabled = db.IntegerProperty()
	created = db.DateTimeProperty(auto_now_add=True)
	modified = db.DateTimeProperty(auto_now=True)
	def toXML(self):
		myDataA = ''
		if self.dataA:
			myDataA = self.dataA
		myDataB = ''
		if self.dataB:
			myDataB = self.dataB + '.xml'
		myImageRef = ''
		if self.imageRef:
			myImageRef = str(self.imageRef.key())
		if self.dataType == 1:
			#text
			return '<text>%s</text>' % escape(myDataA)
		elif self.dataType == 2:
			#image
			return '<image>%s.png</image>' % myImageRef
		elif self.dataType == 3:
			#choice
			return '<choice name=%s goto=%s />' % (quoteattr(myDataA), quoteattr(myDataB))
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




