from google.appengine.ext import db
import logging
import cgi

class Adventure(db.Model):
	title = db.StringProperty(multiline=False)
	realAuthor = db.UserProperty()
	author = db.StringProperty(multiline=False)
	version = db.StringProperty(multiline=False)
	desc = db.TextProperty()
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
	name = db.StringProperty()
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
			logging.error('%s: %s' % (e.__class__.__name__, e))
			self.imageRef = None
			self.put()
		return {
			'page':      str(self.page.key()),
			'adventure': str(self.adventure.key()),
			'key':       str(self.key()),
			'dataType':  self.dataType,
			'pageOrder': self.pageOrder,
			'dataA':     cgi.escape(self.dataA),
			'dataB':     cgi.escape(self.dataB),
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
			myChild = self.child.email()
			myChildNick = self.child.nickname()
		return {
			'adventure':      str(self.adventure.key()),
			'owner':          cgi.escape(str(self.owner.email())),
			'child':          cgi.escape(str(myChild)),
			'ownerNick':      cgi.escape(str(self.owner.nickname())),
			'childNick':      cgi.escape(str(myChildNick)),
			'childEmail':     cgi.escape(self.childEmail),
			'childName':      cgi.escape(self.childName),
			'role':           cgi.escape(str(self.role)),
			'roleName':       cgi.escape(self.roleName()),
			'roleNamePhrase': cgi.escape(self.roleNamePhrase()),
			'inviteKey':      cgi.escape(self.inviteKey),
			'status':         cgi.escape(str(self.status)),
			'statusName':     cgi.escape(self.statusName()),
		}



