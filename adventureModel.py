from google.appengine.ext import db
import logging

class Adventure(db.Model):
	title = db.StringProperty(multiline=False)
	realAuthor = db.UserProperty()
	author = db.StringProperty(multiline=False)
	version = db.StringProperty(multiline=False)
	desc = db.TextProperty()
	created = db.DateTimeProperty(auto_now_add=True)
	modified = db.DateTimeProperty(auto_now=True)

class Page(db.Model):
	adventure = db.ReferenceProperty(Adventure)
	name = db.StringProperty()
	created = db.DateTimeProperty(auto_now_add=True)
	modified = db.DateTimeProperty(auto_now=True)
	def toDict(self):
		return {
			#'adventure': str(self.adventure.key()),
			'key': str(self.key()),
			'name': self.name,
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
			'imageName': self.imageName,
			'realAuthor': str(self.realAuthor.nickname()),
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
			'page': str(self.page.key()),
			'adventure': str(self.adventure.key()),
			'key': str(self.key()),
			'dataType': self.dataType,
			'pageOrder': self.pageOrder,
			'dataA': self.dataA,
			'dataB': self.dataB,
			'enabled': self.enabled,
			'imageRef': imageRef,
		}
